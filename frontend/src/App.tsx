import { useState, useEffect } from 'react';
import { UploadSection } from './components/UploadSection';
import { MetadataEditor, type AnalyzedData } from './components/MetadataEditor';
import { TrackMetadata } from './types/track';
import { Stepper } from './components/Stepper';
import { TagScanner } from './components/TagScanner';
import { AuthOverlay } from './components/AuthOverlay';
import { auth } from './lib/firebase';
import { onAuthStateChanged, signOut, type User } from 'firebase/auth';
import { LogOut, User as UserIcon } from 'lucide-react';
import { AnalysisDiagnostic } from './components/AnalysisDiagnostic';
import { CanvasVisualizer } from './components/CanvasVisualizer';
import { Vault } from './components/Vault';
import { PitchView } from './components/PitchView';
import { useToast, ToastContainer } from './components/Toast';

function App() {
    const [currentStep, setCurrentStep] = useState(1);
    const [view, setView] = useState<'engine' | 'vault'>('vault');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analyzedFiles, setAnalyzedFiles] = useState<AnalyzedData[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [results, setResults] = useState<{ fileId: string, downloadUrl: string, oneSheetUrl: string, masterUrl?: string }[]>([]);
    const [isDiagnostic, setIsDiagnostic] = useState(false);
    const { toasts, addToast, dismiss } = useToast();

    const [user, setUser] = useState<User | null>(null);
    const [showAuthOverlay, setShowAuthOverlay] = useState(false);

    // Detect Public Pitch View
    const urlParams = new URLSearchParams(window.location.search);
    const pitchId = urlParams.get('pitch');

    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
            setUser(currentUser);
        });
        return () => unsubscribe();
    }, []);

    const handleSignOut = async () => {
        try {
            await signOut(auth);
        } catch (error) {
            console.error('Error signing out:', error);
        }
    };

    const steps = ['Upload Master', 'Review & Tag', 'Download Assets'];

    const handleBatchAnalyzed = async (batch: { file: File, analysis: any }[]) => {
        setIsAnalyzing(true);
        try {
            const token = await auth.currentUser?.getIdToken();
            const authHeader: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {} as Record<string, string>;


            const syncPromises = batch.map(async (item) => {
                try {
                    const formData = new FormData();
                    formData.append('file', item.file);
                    formData.append('localAnalysis', JSON.stringify(item.analysis));

                    const res = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: authHeader,
                        body: formData,
                    });

                    if (!res.ok) throw new Error(`Analysis failed for ${item.file.name}`);
                    const data = await res.json();
                    return data as AnalyzedData;
                } catch (e) {
                    console.error(`Error analyzing ${item.file.name}:`, e);
                    return null;
                }
            });

            const rawResults = await Promise.all(syncPromises);
            const validResults = rawResults.filter((r): r is AnalyzedData => r !== null);

            if (validResults.length === 0) {
                addToast('All files in the batch failed analysis.', 'error');
                return;
            }

            setAnalyzedFiles(validResults);
            setIsDiagnostic(true);
        } catch (err) {
            console.error(err);
            addToast('Failed to sync batch with server.', 'error');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSaveBatchMetadata = async (batchMetadata: { fileId: string, metadata: TrackMetadata }[]) => {
        setIsProcessing(true);
        try {
            const token = await auth.currentUser?.getIdToken();
            const authHeader: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};

            const embedPromises = batchMetadata.map(async (item) => {
                try {
                    const formData = new FormData();
                    formData.append('fileId', item.fileId);
                    formData.append('metadata', JSON.stringify(item.metadata));
                    if (user?.uid) {
                        formData.append('uid', user.uid);
                    }

                    const res = await fetch('/api/embed', {
                        method: 'POST',
                        headers: authHeader,
                        body: formData
                    });

                    if (!res.ok) throw new Error('Embedding failed');
                    const result = await res.json();
                    return { fileId: item.fileId, ...result };
                } catch (e) {
                    console.error(`Error embedding ${item.fileId}:`, e);
                    return null;
                }
            });

            const rawFinalResults = await Promise.all(embedPromises);
            const validFinalResults = rawFinalResults.filter((r): r is any => r !== null);

            if (validFinalResults.length === 0) {
                addToast('Failed to process any files in this batch.', 'error');
                return;
            }

            setResults(validFinalResults);
            setCurrentStep(3);
        } catch (err) {
            console.error(err);
            addToast('Failed to embed batch metadata.', 'error');
        } finally {
            setIsProcessing(false);
        }
    };

    const resetFlow = () => {
        setCurrentStep(1);
        setAnalyzedFiles([]);
        setResults([]);
    };

    const [activeBuffer, setActiveBuffer] = useState<AudioBuffer | null>(null);

    if (pitchId) {
        return <PitchView pitchId={pitchId} />;
    }

    return (
        <div className="min-h-screen bg-[#050505] text-white flex flex-col font-sans selection:bg-accent-cyan/30">
            <ToastContainer toasts={toasts} onDismiss={dismiss} />
            {/* Background Visualizer */}
            <CanvasVisualizer audioBuffer={activeBuffer || analyzedFiles[0]?.audioBuffer} />

            {/* Top Right Auth */}
            <div className="absolute top-6 right-6 z-50">
                {user ? (
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 text-sm text-text-secondary bg-black/20 px-3 py-1.5 rounded-full border border-white/10">
                            <UserIcon size={14} />
                            <span>{user.email}</span>
                        </div>
                        <button
                            onClick={handleSignOut}
                            title="Sign Out"
                            className="p-2 text-text-secondary hover:text-white bg-black/20 hover:bg-black/40 rounded-full border border-white/10 transition-colors"
                        >
                            <LogOut size={16} />
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => setShowAuthOverlay(true)}
                        className="glass-button text-sm px-4 py-2 flex items-center gap-2"
                    >
                        <UserIcon size={16} />
                        Sign In
                    </button>
                )}
            </div>

            {/* Header */}
            <div className="max-w-7xl mx-auto text-center mb-16 relative z-10">
                <h1 className="text-5xl font-bold mb-4 tracking-tight">
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-cyan to-accent-purple">Resonant</span>
                    <span className="text-white">Crab</span>
                </h1>
                <p className="text-lg text-text-secondary max-w-2xl mx-auto font-light">
                    Seamlessly analyze, tag, and export your masters to perfect DISCO-compliant standards with Cyanite-level ML insights and One-Sheet generation.
                </p>
            </div>

            {showAuthOverlay && (
                <AuthOverlay
                    onClose={() => setShowAuthOverlay(false)}
                    onSuccess={() => setShowAuthOverlay(false)}
                />
            )}

            {/* In-Engine Stepper - Only visible when processing */}
            {view === 'engine' && (
                <div className="animate-fade-in">
                    <Stepper currentStep={currentStep} steps={steps} />
                </div>
            )}

            {/* View Toggle (Only if logged in) */}
            {user && (
                <div className="max-w-7xl mx-auto mb-8 flex justify-center">
                    <div className="bg-black/20 p-1 rounded-xl border border-white/10 flex gap-1">
                        <button
                            onClick={() => setView('engine')}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${view === 'engine'
                                ? 'bg-white/10 text-white shadow-lg'
                                : 'text-text-secondary hover:text-white'
                                }`}
                        >
                            ENGINE
                        </button>
                        <button
                            onClick={() => setView('vault')}
                            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${view === 'vault'
                                ? 'bg-white/10 text-white shadow-lg'
                                : 'text-text-secondary hover:text-white'
                                }`}
                        >
                            THE VAULT
                        </button>
                    </div>
                </div>
            )}

            {/* Main Content Area */}
            <div className="max-w-7xl mx-auto relative z-10 mt-8">
                {view === 'vault' && user ? (
                    <Vault uid={user.uid} onProcessNew={() => setView('engine')} />
                ) : (
                    <>
                        {currentStep === 1 && (
                            <div className="max-w-2xl mx-auto">
                                {isDiagnostic && analyzedFiles.length > 0 ? (
                                    <div className="relative">
                                        <AnalysisDiagnostic
                                            data={{
                                                bpm: analyzedFiles[0].bpm.toFixed(2),
                                                key: `${analyzedFiles[0].key} ${analyzedFiles[0].scale}`,
                                                lufs: analyzedFiles[0].lufs?.toFixed(1) ?? 'N/A',
                                                energy: (Number(analyzedFiles[0].energy) * 100).toFixed(0)
                                            }}
                                            onComplete={() => {
                                                setIsDiagnostic(false);
                                                setCurrentStep(2);
                                            }}
                                        />
                                    </div>
                                ) : (
                                    <UploadSection onFilesAnalyzed={handleBatchAnalyzed} isAnalyzing={isAnalyzing} />
                                )}
                            </div>
                        )}

                        {currentStep === 2 && analyzedFiles.length > 0 && (
                            <MetadataEditor
                                files={analyzedFiles}
                                onSave={handleSaveBatchMetadata}
                                isProcessing={isProcessing}
                                onPlayBuffer={setActiveBuffer}
                            />
                        )}

                        {currentStep === 3 && results.length > 0 && (
                            <div className="max-w-3xl mx-auto">
                                <TagScanner
                                    results={results}
                                    onStartOver={resetFlow}
                                    onGoToVault={() => {
                                        resetFlow();
                                        setView('vault');
                                    }}
                                />
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}

export default App;
