import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useAudioAnalyzer } from './useAudioAnalyzer';

describe('useAudioAnalyzer', () => {
    // Setup standard mocks
    beforeEach(() => {
        vi.useFakeTimers();

        // 1. Mock AudioContext
        const mockAudioBuffer = {
            getChannelData: vi.fn().mockReturnValue(new Float32Array(100))
        };
        const mockDecodeAudioData = vi.fn().mockResolvedValue(mockAudioBuffer);
        window.AudioContext = vi.fn().mockImplementation(function() { return {
            decodeAudioData: mockDecodeAudioData
        }; }) as any;

        // 2. Mock EssentiaWASM
        window.EssentiaWASM = vi.fn().mockResolvedValue('mock-wasm-module');

        // 3. Mock Essentia
        window.Essentia = vi.fn().mockImplementation(function() { return {
            arrayToVector: vi.fn().mockReturnValue('mock-signal'),
            rhythmExtractor2013: vi.fn().mockReturnValue({ bpm: 120.5 }),
            keyExtractor: vi.fn().mockReturnValue({ key: 'C', scale: 'major' }),
            Danceability: vi.fn().mockReturnValue({ danceability: 0.8 }),
            Energy: vi.fn().mockReturnValue({ energy: 0.9 }),
            RMS: vi.fn().mockReturnValue({ rms: 0.5 }),
            MSDSpectrogramMusiCNN: vi.fn().mockReturnValue('mock-features')
        }; });

        // 4. Mock EssentiaModel
        const mockPredict = vi.fn().mockResolvedValue([
            { dataSync: () => new Float32Array([0.1, 0.9, 0.2, 0.8, 0.3]), keys: () => [0, 1, 2, 3, 4] }
        ]);
        window.EssentiaModel = {
            EssentiaTFInputMusiCNN: vi.fn().mockImplementation(function() { return {
                predict: mockPredict,
                getLabels: () => ['rock', 'electronic', 'jazz', 'cinematic', 'pop']
            }; })
        };
    });

    afterEach(() => {
        vi.runOnlyPendingTimers();
        vi.useRealTimers();
        vi.restoreAllMocks();
        delete (window as any).AudioContext;
        delete (window as any).EssentiaWASM;
        delete (window as any).Essentia;
        delete (window as any).EssentiaModel;
    });

    it('successfully analyzes an audio file and maps properties correctly', async () => {
        const { result } = renderHook(() => useAudioAnalyzer());
        const mockFile = new File([''], 'test.mp3', { type: 'audio/mp3' });
        const onProgress = vi.fn();

        let analysisPromise: Promise<any>;
        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile, onProgress);
        });

        // Resolve any awaited promises
        await act(async () => {
            vi.runAllTimers();
            await analysisPromise;
        });

        const analysis = await analysisPromise;

        expect(analysis).not.toBeNull();
        expect(analysis?.bpm).toBe(120.5);
        expect(analysis?.key).toBe('C');
        expect(analysis?.scale).toBe('major');
        expect(analysis?.energy).toBe(0.9);
        expect(analysis?.danceability).toBe(0.8);
        expect(analysis?.valence).toBe(0.7);
        // lufs logic: 20 * Math.log10(0.5 + 1e-9) ≈ -6
        expect(analysis?.lufs).toBeCloseTo(-6.0, 1);
        expect(analysis?.genre).toBe('Electronic'); // because index 1 has 0.9 and maps to 'electronic'
        expect(analysis?.mood).toBe('Cinematic'); // because index 3 has 0.8 and maps to 'cinematic'

        expect(onProgress).toHaveBeenCalledWith(10);
        expect(onProgress).toHaveBeenCalledWith(30);
        expect(onProgress).toHaveBeenCalledWith(40);
        expect(onProgress).toHaveBeenCalledWith(60);
        expect(onProgress).toHaveBeenCalledWith(65);
        expect(onProgress).toHaveBeenCalledWith(75);
        expect(onProgress).toHaveBeenCalledWith(100);
    });

    it('falls back to heuristics if EssentiaModel throws an error', async () => {
        window.EssentiaModel.EssentiaTFInputMusiCNN = vi.fn().mockImplementation(function() {
            throw new Error('MusiCNN model failed to load');
        });

        const { result } = renderHook(() => useAudioAnalyzer());
        const mockFile = new File([''], 'test.mp3', { type: 'audio/mp3' });

        let analysisPromise: Promise<any>;
        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile);
        });

        await act(async () => {
            vi.runAllTimers();
            await analysisPromise;
        });

        const analysis = await analysisPromise;
        expect(analysis).not.toBeNull();
        expect(analysis?.mood).toBe('High-Energy'); // Fallback heuristic since energy > 0.8
        expect(analysis?.instruments).toContain('Synthesizer');
    });

    it('waits for Essentia if it loads asynchronously', async () => {
        // Initially Essentia is not defined
        const EssentiaWASM = window.EssentiaWASM;
        const Essentia = window.Essentia;
        delete (window as any).EssentiaWASM;
        delete (window as any).Essentia;

        const { result } = renderHook(() => useAudioAnalyzer());
        const mockFile = new File([''], 'test.mp3', { type: 'audio/mp3' });

        let analysisPromise: Promise<any>;
        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile);
        });

        // Simulate script loading after 1 second
        act(() => {
            vi.advanceTimersByTime(1000);
            window.EssentiaWASM = EssentiaWASM;
            window.Essentia = Essentia;
            vi.advanceTimersByTime(200); // Trigger the next check
        });

        await act(async () => {
            vi.runAllTimers();
            await analysisPromise;
        });

        const analysis = await analysisPromise;
        expect(analysis).not.toBeNull();
    });

    it('returns null and logs error if Essentia fails to load within 10 seconds', async () => {
        // Essentia is never defined
        delete (window as any).EssentiaWASM;
        delete (window as any).Essentia;

        const consoleErrorMock = vi.spyOn(console, 'error').mockImplementation(() => {});

        const { result } = renderHook(() => useAudioAnalyzer());
        const mockFile = new File([''], 'test.mp3', { type: 'audio/mp3' });

        let analysisPromise: Promise<any>;
        act(() => {
            analysisPromise = result.current.analyzeAudio(mockFile);
        });

        await act(async () => {
            vi.advanceTimersByTime(11000);
            await analysisPromise;
        });

        const analysis = await analysisPromise;
        expect(analysis).toBeNull();
        expect(consoleErrorMock).toHaveBeenCalled();

        consoleErrorMock.mockRestore();
    });
});
