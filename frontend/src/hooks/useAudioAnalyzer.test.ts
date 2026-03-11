import { renderHook, act } from '@testing-library/react';
import { useAudioAnalyzer } from './useAudioAnalyzer';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';

describe('useAudioAnalyzer', () => {
    let mockEssentiaInstance: any;
    let mockAudioBuffer: any;

    beforeEach(() => {
        // Reset timers
        vi.useFakeTimers();

        mockEssentiaInstance = {
            arrayToVector: vi.fn().mockReturnValue('mock-signal'),
            rhythmExtractor2013: vi.fn().mockReturnValue({ bpm: 120.55 }),
            keyExtractor: vi.fn().mockReturnValue({ key: 'C', scale: 'major' }),
            Danceability: vi.fn().mockReturnValue({ danceability: 0.85 }),
            Energy: vi.fn().mockReturnValue({ energy: 0.9 }),
            RMS: vi.fn().mockReturnValue({ rms: 0.5 }),
            MSDSpectrogramMusiCNN: vi.fn().mockReturnValue('mock-features')
        };

        window.EssentiaWASM = vi.fn().mockResolvedValue('mock-wasm-module');
        window.Essentia = vi.fn().mockImplementation(function() {
            return mockEssentiaInstance;
        });

        mockAudioBuffer = {
            getChannelData: vi.fn().mockReturnValue(new Float32Array([0.1, 0.2, 0.3]))
        };

        window.AudioContext = vi.fn().mockImplementation(function() {
            return {
                decodeAudioData: vi.fn().mockResolvedValue(mockAudioBuffer)
            };
        }) as any;

        window.EssentiaModel = {
            EssentiaTFInputMusiCNN: vi.fn().mockImplementation(function() {
                return {
                    predict: vi.fn().mockResolvedValue([{
                        dataSync: () => new Float32Array([0.1, 0.9, 0.2, 0.8, 0.3])
                    }]),
                    getLabels: vi.fn().mockReturnValue(['rock', 'electronic', 'jazz', 'cinematic', 'pop'])
                };
            })
        } as any;
    });

    afterEach(() => {
        vi.clearAllMocks();
        vi.useRealTimers();
        delete (window as any).EssentiaWASM;
        delete (window as any).Essentia;
        delete (window as any).AudioContext;
        delete (window as any).EssentiaModel;
    });

    it('should wait for Essentia to load and analyze audio successfully', async () => {
        const { result } = renderHook(() => useAudioAnalyzer());

        const mockFile = {
            arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(8))
        } as unknown as File;

        const onProgress = vi.fn();

        let analysisPromise: Promise<any>;

        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile, onProgress);
        });

        // Fast-forward timers to allow waitForEssentia to complete
        await act(async () => {
            vi.advanceTimersByTime(100);
            await vi.runAllTimersAsync();
        });

        const analysis = await analysisPromise!;

        expect(analysis).not.toBeNull();
        expect(analysis?.bpm).toBe(120.6); // 120.55 rounded
        expect(analysis?.key).toBe('C');
        expect(analysis?.scale).toBe('major');
        expect(analysis?.energy).toBe(0.9);
        expect(analysis?.danceability).toBe(0.85);
        expect(analysis?.valence).toBe(0.7); // major scale

        // lufs = 20 * Math.log10(0.5 + 1e-9) = 20 * -0.30103 = -6.0206 => -6.0
        expect(analysis?.lufs).toBe(-6.0);

        // Predict logic:
        // labels: ['rock', 'electronic', 'jazz', 'cinematic', 'pop']
        // scores: [0.1, 0.9, 0.2, 0.8, 0.3]
        // sorted indices: [1, 3, 4, 2, 0] -> 'electronic', 'cinematic', 'pop', 'jazz', 'rock'
        // 'electronic' is first, so genre should be 'Electronic'
        // 'cinematic' is second, so mood should be 'Cinematic'
        expect(analysis?.genre).toBe('Electronic');
        expect(analysis?.mood).toBe('Cinematic');

        expect(onProgress).toHaveBeenCalledWith(10);
        expect(onProgress).toHaveBeenCalledWith(100);
    });

    it('should timeout and return null if Essentia does not load', async () => {
        // Remove globals to simulate failure
        delete (window as any).EssentiaWASM;
        delete (window as any).Essentia;

        const { result } = renderHook(() => useAudioAnalyzer());
        const mockFile = {
            arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(8))
        } as unknown as File;

        let analysisPromise: Promise<any>;

        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile);
        });

        // Advance past the 10s timeout
        await act(async () => {
            vi.advanceTimersByTime(10500);
            await vi.runAllTimersAsync();
        });

        const analysis = await analysisPromise!;
        expect(analysis).toBeNull();
    });

    it('should fallback to heuristics if MusiCNN fails', async () => {
        // Break MusiCNN
        window.EssentiaModel = {
            EssentiaTFInputMusiCNN: vi.fn().mockImplementation(function() {
                throw new Error("TF Error");
            })
        } as any;

        const { result } = renderHook(() => useAudioAnalyzer());
        const mockFile = {
            arrayBuffer: vi.fn().mockResolvedValue(new ArrayBuffer(8))
        } as unknown as File;

        let analysisPromise: Promise<any>;
        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile);
        });

        await act(async () => {
            vi.advanceTimersByTime(100);
            await vi.runAllTimersAsync();
        });

        const analysis = await analysisPromise!;
        // energy is 0.9 > 0.8 so mood should be High-Energy
        expect(analysis?.mood).toBe('High-Energy');
    });
});
