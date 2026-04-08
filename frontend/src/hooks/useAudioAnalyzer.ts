import { useCallback, useRef } from 'react';



export interface AnalysisResult {
    bpm: number;
    key: string;
    scale: string;
    energy: number;
    danceability: number;
    valence: number;
    lufs: number;
    mood: string;
    genre: string;
    instruments: string[];
    vocalPresence: string;
    audioBuffer?: AudioBuffer;
}

export function useAudioAnalyzer() {
    const essentiaRef = useRef<any>(null);

    /** Polls until both Essentia globals are available (CDN scripts load async). */
    const waitForEssentia = (): Promise<void> => {
        return new Promise((resolve, reject) => {
            const start = Date.now();
            const check = () => {
                if (typeof window.EssentiaWASM === 'function' && typeof window.Essentia === 'function') {
                    resolve();
                } else if (Date.now() - start > 10000) {
                    reject(new Error('Essentia.js scripts failed to load. Please check your browser tracking prevention settings or network connection.'));
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    };

    const initEssentia = async () => {
        if (!essentiaRef.current) {
            await waitForEssentia();
            const wasmModule = await window.EssentiaWASM();
            const essentia = new window.Essentia(wasmModule);
            essentiaRef.current = essentia;
        }
        return essentiaRef.current;
    };

    const analyzeAudio = useCallback(async (file: File, onProgress?: (p: number) => void): Promise<AnalysisResult | null> => {
        const updateProgress = (val: number) => onProgress && onProgress(val);

        try {
            const essentia = await initEssentia();

            // 1. Decode Audio File
            updateProgress(10);
            const arrayBuffer = await file.arrayBuffer();
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

            // Audio data for Essentia (mono)
            const signal = essentia.arrayToVector(audioBuffer.getChannelData(0));
            updateProgress(30);

            // 2. Core Analysis (BPM & Key)
            updateProgress(40);
            const rhythmResult = essentia.rhythmExtractor2013(signal);
            const keyResult = essentia.keyExtractor(signal);

            updateProgress(60);
            const danceabilityResult = essentia.Danceability(signal);
            const energyResult = essentia.Energy(signal);

            // 3. RMS-based LUFS Approximation (Simplified)
            updateProgress(65);
            const rms = essentia.RMS(signal).rms;
            const lufs = 20 * Math.log10(rms + 1e-9); // Standard RMS to dB transformation

            // 4. Deep MusiCNN Inference (Mood & Genre)
            updateProgress(75);
            let mood = "Cinematic";
            let genre = "Electronic";
            let instruments = ["Synthesizer"];

            if (window.EssentiaModel) {
                try {
                    const model = new window.EssentiaModel.EssentiaTFInputMusiCNN();
                    // MusiCNN expects 3s patches @ 16kHz usually, but essentia.js-model handles the windowing
                    // We extract mel-spectrogram features as required by the MS-D/MTAGS models
                    const features = essentia.MSDSpectrogramMusiCNN(signal);
                    const predictions = await model.predict(features);

                    // Probability mapping logic
                    const tags = model.getLabels();
                    const results = predictions[0].dataSync() as Float32Array;

                    // Filter top predictions
                    const sortedIndices = Array.from(results.keys())
                        .sort((a, b) => results[b] - results[a])
                        .slice(0, 5);

                    const topTags = sortedIndices.map(i => tags[i]);

                    // Professional mapping
                    const tagMap: Record<string, string[]> = {
                        cinematic: ['emotional', 'film', 'epic', 'orchestral', 'soundtrack'],
                        dark: ['dark', 'scary', 'moody', 'mysterious', 'tension'],
                        grouping: ['epic', 'trailer', 'dramatic', 'intense'],
                        upbeat: ['happy', 'cheerful', 'energetic', 'bright', 'fun'],
                        lofi: ['lofi', 'chill', 'mellow', 'relaxed', 'calm']
                    };

                    const genreMap: Record<string, string> = {
                        'electronic': 'Electronic',
                        'rock': 'Rock',
                        'pop': 'Pop',
                        'jazz': 'Jazz',
                        'classical': 'Classical',
                        'hiphop': 'Hip-Hop'
                    };

                    // Set Genre
                    const detectedGenre = topTags.find(t => genreMap[t.toLowerCase()]);
                    if (detectedGenre) genre = genreMap[detectedGenre.toLowerCase()];

                    // Set Mood (Complex lookup)
                    if (topTags.some(t => tagMap.cinematic.includes(t.toLowerCase()))) mood = 'Cinematic';
                    else if (topTags.some(t => tagMap.dark.includes(t.toLowerCase()))) mood = 'Dark & Moody';
                    else if (topTags.some(t => tagMap.upbeat.includes(t.toLowerCase()))) mood = 'Upbeat & Bright';
                    else if (topTags.some(t => tagMap.lofi.includes(t.toLowerCase()))) mood = 'Lo-fi & Chill';

                    // Simple instrument detection
                    instruments = topTags.filter(t => ['guitar', 'piano', 'synth', 'vocals', 'drums', 'strings', 'brass'].includes(t.toLowerCase()));
                    if (instruments.length === 0) instruments = ["Hybrid Ensemble"];
                } catch (tfError) {
                    console.warn("MusiCNN inference failed, falling back to heuristics:", tfError);
                    if (energyResult.energy > 0.8) mood = "High-Energy";
                }
            }

            updateProgress(100);

            return {
                bpm: Math.round(rhythmResult.bpm * 10) / 10,
                key: keyResult.key,
                scale: keyResult.scale,
                energy: Math.round(energyResult.energy * 100) / 100,
                danceability: Math.round(danceabilityResult.danceability * 100) / 100,
                valence: keyResult.scale === 'major' ? 0.7 : 0.3,
                lufs: Math.round(lufs * 10) / 10,
                mood,
                genre,
                instruments,
                vocalPresence: instruments.includes('vocals') ? 'Vocal' : 'Instrumental',
                audioBuffer
            };

        } catch (err: any) {
            console.error("Audio Analysis Error:", err);
            return null;
        }
    }, []);

    return {
        analyzeAudio
    };
}
