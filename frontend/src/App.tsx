import { useState } from 'react';
import { UploadSection } from './components/UploadSection';
import { MetadataEditor } from './components/MetadataEditor';
import type { AnalyzedData } from './components/MetadataEditor';
import { Stepper } from './components/Stepper';
import { TagScanner } from './components/TagScanner';


function App() {
    const [currentStep, setCurrentStep] = useState(1);
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [analyzedData, setAnalyzedData] = useState<AnalyzedData | null>(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [completedFileUrl, setCompletedFileUrl] = useState<string | null>(null);
    const [oneSheetUrl, setOneSheetUrl] = useState<string | null>(null);
    const [count, setCount] = useState(0);

    const steps = ['Upload Master', 'Review & Tag', 'Download Assets'];

    const handleFileSelect = async (file: File, localAnalysis: any) => {
        setIsAnalyzing(true);

        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('localAnalysis', JSON.stringify(localAnalysis));

            const res = await fetch('http://localhost:8000/api/analyze', {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) throw new Error('Analysis failed');

            const data = await res.json();
            setAnalyzedData(data);
            setCurrentStep(2);
        } catch (err) {
            console.error(err);
            alert('Failed to analyze audio.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleSaveMetadata = async (data: any) => {
        if (!analyzedData?.fileId) return;
        setIsProcessing(true);

        try {
            const formData = new FormData();
            formData.append('fileId', analyzedData.fileId);
            formData.append('metadata', JSON.stringify(data));

            const res = await fetch('http://localhost:8000/api/embed', {
                method: 'POST',
                body: formData
            });

            if (!res.ok) throw new Error('Embedding failed');

            const result = await res.json();
            setCompletedFileUrl(result.downloadUrl);
            setOneSheetUrl(result.oneSheetUrl);
            setCurrentStep(3);
        } catch (err) {
            console.error(err);
            alert('Failed to embed metadata');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleDownloadOneSheet = () => {
        if (oneSheetUrl) {
            window.open(oneSheetUrl, '_blank');
        }
    };

    const resetFlow = () => {
        setCurrentStep(1);
        setAnalyzedData(null);
        setCompletedFileUrl(null);
        setOneSheetUrl(null);
    };

    return (
        <div className="min-h-screen bg-bg-primary text-text-primary py-12 px-4 sm:px-6 lg:px-8">
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

            <Stepper currentStep={currentStep} steps={steps} />

            {/* Main Content Area */}
            <div className="max-w-7xl mx-auto relative z-10 mt-16">

                {currentStep === 1 && (
                    <div className="max-w-2xl mx-auto">
                        <UploadSection onFileSelect={handleFileSelect} isAnalyzing={isAnalyzing} />
                    </div>
                )}

                {currentStep === 2 && analyzedData && (
                    <MetadataEditor
                        initialData={analyzedData}
                        onSave={handleSaveMetadata}
                        onDownloadOneSheet={handleDownloadOneSheet}
                        isProcessing={isProcessing}
                    />
                )}

                {currentStep === 3 && analyzedData?.fileId && (
                    <div className="max-w-2xl mx-auto">
                        <TagScanner
                            fileId={analyzedData.fileId}
                            downloadUrl={completedFileUrl || '#'}
                            oneSheetUrl={oneSheetUrl || '#'}
                            onReset={resetFlow}
                        />
                    </div>
                )}
            </div>
            {/* TypeScript Logo and Counter Widget */}
            <div className="fixed bottom-6 right-6 z-50 flex items-center gap-4 bg-black/20 p-3 rounded-2xl backdrop-blur-md border border-white/10 shadow-xl">
                <a href="https://www.typescriptlang.org/" target="_blank" rel="noopener noreferrer">
                    <img
                        src="https://upload.wikimedia.org/wikipedia/commons/4/4c/Typescript_logo_2020.svg"
                        alt="TypeScript Logo"
                        className="w-10 h-10 hover:drop-shadow-[0_0_10px_rgba(49,120,198,0.8)] transition-all duration-300 transform hover:scale-110"
                    />
                </a>
                <button
                    onClick={() => setCount((c) => c + 1)}
                    className="glass-button h-10 px-6 font-medium text-sm border-accent-cyan/30 text-accent-cyan hover:bg-accent-cyan/10 transition-colors"
                >
                    count is {count}
                </button>
            </div>

        </div>
    );
}

export default App;
