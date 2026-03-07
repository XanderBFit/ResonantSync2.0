import { useState, useCallback, useRef } from 'react';
import { UploadCloud, FileAudio, AlertCircle, Play, Pause } from 'lucide-react';
import WaveSurfer from 'wavesurfer.js';
import { useAudioAnalyzer, type AnalysisResult } from '../hooks/useAudioAnalyzer';

interface UploadSectionProps {
    onFileSelect: (file: File, analysisData: AnalysisResult) => void;
    isAnalyzing: boolean;
}

export function UploadSection({ onFileSelect, isAnalyzing }: UploadSectionProps) {
    const [isDragging, setIsDragging] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const wavesurferRef = useRef<WaveSurfer | null>(null);
    const waveformContainerRef = useRef<HTMLDivElement>(null);
    const { analyzeAudio, isAnalyzing: isLocalAnalyzing, progress } = useAudioAnalyzer();

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setIsDragging(true);
        } else if (e.type === 'dragleave') {
            setIsDragging(false);
        }
    }, []);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragging(false);
            setError(null);

            const files = Array.from(e.dataTransfer.files);
            if (files.length > 0) {
                handleProcessFile(files[0]);
            }
        },
        [onFileSelect]
    );

    const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        setError(null);
        if (e.target.files && e.target.files.length > 0) {
            handleProcessFile(e.target.files[0]);
        }
    };

    const handleProcessFile = async (file: File) => {
        if (!file.type.startsWith('audio/')) {
            setError('Please upload a valid audio file (.mp3, .wav, .aiff)');
            return;
        }

        // Generate Waveform
        if (waveformContainerRef.current) {
            // Destroy old instance if exists
            if (wavesurferRef.current) {
                wavesurferRef.current.destroy();
            }

            const ws = WaveSurfer.create({
                container: waveformContainerRef.current,
                waveColor: 'rgba(6, 182, 212, 0.4)',
                progressColor: 'rgba(139, 92, 246, 0.8)',
                cursorColor: '#ffffff',
                barWidth: 2,
                barGap: 1,
                barRadius: 2,
                height: 80,
                normalize: true,
            });

            ws.on('play', () => setIsPlaying(true));
            ws.on('pause', () => setIsPlaying(false));

            const fileUrl = URL.createObjectURL(file);
            ws.load(fileUrl);
            wavesurferRef.current = ws;
        }

        // Analyze locally with Essentia.js
        const result = await analyzeAudio(file);

        if (result) {
            onFileSelect(file, result);
        } else {
            setError('Could not complete audio analysis.');
        }
    };

    const togglePlay = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (wavesurferRef.current) {
            wavesurferRef.current.playPause();
        }
    };

    // To properly show the waveform and loading states we structure it based on local analysis OR server uploading
    const showLoading = isAnalyzing || isLocalAnalyzing;

    return (
        <div
            className={`glass-panel p-10 flex flex-col items-center justify-center text-center cursor-pointer transition-all duration-300 relative overflow-hidden ${isDragging ? 'border-accent-cyan bg-white/5 scale-[1.02]' : ''
                }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            style={{ minHeight: '350px' }}
        >
            {/* Dynamic Glow background */}
            {isDragging && (
                <div className="absolute inset-0 bg-gradient-to-tr from-cyan-500/10 to-purple-500/10 pointer-events-none" />
            )}

            {showLoading ? (
                <div className="flex flex-col items-center z-10 animate-fade-in">
                    <div className="relative mb-6">
                        <div className="w-20 h-20 rounded-full border-4 border-white/10 border-t-accent-cyan animate-spin"></div>
                        <FileAudio className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-accent-cyan w-8 h-8" />
                    </div>
                    {isLocalAnalyzing ? (
                        <>
                            <h3 className="text-2xl font-semibold mb-2 text-gradient-accent">Local Analysis ({progress}%)</h3>
                            <p className="text-text-secondary max-w-sm">
                                Extracting deep metrics: Valence, Danceability, Energy, BPM natively...
                            </p>
                            <div className="w-64 h-2 bg-white/10 rounded-full mt-4 overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-accent-cyan to-accent-purple transition-all duration-300" style={{ width: `${progress}%` }}></div>
                            </div>
                        </>
                    ) : (
                        <>
                            <h3 className="text-2xl font-semibold mb-2 text-gradient-accent">Analyzing Track</h3>
                            <p className="text-text-secondary max-w-sm">
                                Extracting deep metadata: Mood, Genre, Energy, BPM, Key, and Instrument Profiles...
                            </p>
                        </>
                    )}
                </div>
            ) : (
                <div className="flex flex-col items-center z-10 animate-fade-in">
                    <div className={`w-20 h-20 rounded-full flex items-center justify-center mb-6 transition-colors duration-300 ${isDragging ? 'bg-cyan-500/20 text-accent-cyan' : 'bg-white/5 text-text-secondary'}`}>
                        <UploadCloud size={40} />
                    </div>
                    <h3 className="text-2xl font-semibold mb-3">Drop your master track here</h3>
                    <p className="text-text-secondary mb-8 max-w-md">
                        Upload your WAV, AIFF, or MP3. We'll strip existing data, run our AI model, and prep it perfectly for DISCO.
                    </p>

                    <label className="glass-button primary">
                        Select File
                        <input
                            type="file"
                            className="hidden"
                            accept="audio/*"
                            onChange={handleFileInput}
                        />
                    </label>

                    {error && (
                        <div className="mt-6 flex items-center gap-2 text-red-400 bg-red-400/10 px-4 py-2 rounded-lg text-sm animate-fade-in">
                            <AlertCircle size={16} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Hidden Waveform container that populates while uploading */}
                    <div className="w-full mt-8" onClick={(e) => e.stopPropagation()}>
                        <div ref={waveformContainerRef} className="w-full" />
                        {wavesurferRef.current && !error && (
                            <button onClick={togglePlay} className="mt-4 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors text-white">
                                {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                            </button>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
