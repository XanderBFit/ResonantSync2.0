import { useState, useCallback } from 'react';
import { UploadCloud, FileAudio, AlertCircle } from 'lucide-react';
import { useAudioAnalyzer, type AnalysisResult } from '../hooks/useAudioAnalyzer';

export interface BatchFile {
    file: File;
    analysis: AnalysisResult;
}

interface UploadSectionProps {
    onFilesAnalyzed: (batch: BatchFile[]) => void;
    isAnalyzing: boolean;
}

interface ProcessingTrack {
    id: string;
    file: File;
    progress: number;
    status: 'analyzing' | 'completed' | 'error';
    analysis?: AnalysisResult;
}

export function UploadSection({ onFilesAnalyzed, isAnalyzing }: UploadSectionProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [processingTracks, setProcessingTracks] = useState<ProcessingTrack[]>([]);
    const { analyzeAudio } = useAudioAnalyzer();

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragging(true);
        } else if (e.type === 'dragleave') {
            setIsDragging(false);
        }
    }, []);

    const processAllFiles = async (files: File[]) => {
        const audioFiles = files.filter(f => f.type.startsWith('audio/') || f.name.match(/\.(mp3|wav|aiff)$/i));
        if (audioFiles.length === 0) {
            setError('Please upload valid audio files (.mp3, .wav, .aiff)');
            return;
        }

        const initialTracks: ProcessingTrack[] = audioFiles.map(f => ({
            id: Math.random().toString(36).substring(7),
            file: f,
            progress: 0,
            status: 'analyzing'
        }));

        setProcessingTracks(initialTracks);

        const analysisPromises = initialTracks.map(async (track) => {
            const result = await analyzeAudio(track.file, (p) => {
                setProcessingTracks(prev => prev.map(t =>
                    t.id === track.id ? { ...t, progress: p } : t
                ));
            });

            if (result) {
                setProcessingTracks(prev => prev.map(t =>
                    t.id === track.id ? { ...t, status: 'completed', analysis: result, progress: 100 } : t
                ));
                return { file: track.file, analysis: result };
            } else {
                setProcessingTracks(prev => prev.map(t =>
                    t.id === track.id ? { ...t, status: 'error' } : t
                ));
                return null;
            }
        });

        const results = await Promise.all(analysisPromises);
        const validResults = results.filter((r): r is BatchFile => r !== null);

        if (validResults.length > 0) {
            onFilesAnalyzed(validResults);
        } else {
            setError('Failed to analyze the uploaded tracks.');
        }
    };

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(false);
            setError(null);

            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                processAllFiles(files);
            }
        },
        []
    );

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setError(null);
        if (e.target.files && e.target.files.length > 0) {
            processAllFiles(Array.from(e.target.files));
        }
    };

    return (
        <div className={`relative w-full ${isDragging ? 'mesh-bloom' : ''}`}>
            {/* Kinetic Mesh Background layer scoped to Step 1 */}
            <div className="mesh-gradient-container">
                <div className="mesh-ball mesh-ball-1" />
                <div className="mesh-ball mesh-ball-2" />
            </div>

            <div
                className={`glass-panel glass-deep p-12 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-500 relative overflow-hidden min-h-[450px] ${isDragging ? 'highlight scale-[1.02]' : ''
                    }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                {isDragging && (
                    <div className="absolute inset-0 bg-accent-cyan/5 pointer-events-none animate-pulse" />
                )}

                {processingTracks.length > 0 ? (
                    <div className="w-full space-y-4 z-10 animate-fade-in">
                        <h3 className="text-xl font-semibold mb-6 flex items-center justify-center gap-2">
                            <FileAudio className="text-accent-cyan" />
                            Batch Processing ({processingTracks.filter(t => t.status === 'completed').length}/{processingTracks.length})
                        </h3>

                        <div className="max-h-[300px] overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                            {processingTracks.map(track => (
                                <div key={track.id} className="bg-black/20 rounded-xl p-4 border border-white/5 flex flex-col gap-2">
                                    <div className="flex justify-between items-center">
                                        <span className="text-sm font-medium truncate max-w-[200px]">{track.file.name}</span>
                                        <span className="text-xs text-text-secondary">
                                            {track.status === 'analyzing' ? `${track.progress}%` : track.status}
                                        </span>
                                    </div>
                                    <progress
                                        value={track.progress}
                                        max="100"
                                        className={`w-full progress-bar ${track.status === 'error' ? 'error' : ''}`}
                                        aria-label={`Analysis progress for ${track.file.name}`}
                                    />
                                </div>
                            ))}
                        </div>

                        {isAnalyzing && (
                            <div className="mt-6 pt-6 border-t border-white/10 animate-pulse">
                                <p className="text-sm text-accent-cyan">Syncing batch with server and GCS...</p>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center z-10 animate-fade-in">
                        <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-colors duration-300 ${isDragging ? 'bg-cyan-500/20 text-accent-cyan' : 'bg-white/5 text-text-secondary'}`}>
                            <UploadCloud size={40} />
                        </div>
                        <h3 className="text-2xl font-semibold mb-3">Drop your album or stems here</h3>
                        <p className="text-text-secondary mb-8 max-w-md">
                            Upload 10+ tracks at once. We'll run parallel AI analysis and prep them perfectly for DISCO.
                        </p>

                        <label className="glass-button primary">
                            Select Files
                            <input
                                type="file"
                                className="hidden"
                                accept=".mp3,.wav,.aiff"
                                multiple
                                onChange={handleFileInput}
                            />
                        </label>

                        {error && (
                            <div className="mt-6 flex items-center gap-2 text-red-400 bg-red-400/10 px-4 py-2 rounded-lg text-sm animate-fade-in">
                                <AlertCircle size={16} />
                                <span>{error}</span>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
