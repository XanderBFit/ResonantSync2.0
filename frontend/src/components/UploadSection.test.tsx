import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { UploadSection } from './UploadSection';
import * as useAudioAnalyzerHook from '../hooks/useAudioAnalyzer';

// Mock the hook
vi.mock('../hooks/useAudioAnalyzer', () => ({
    useAudioAnalyzer: vi.fn()
}));

describe('UploadSection', () => {
    const mockOnFilesAnalyzed = vi.fn();
    const mockAnalyzeAudio = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();
        (useAudioAnalyzerHook.useAudioAnalyzer as any).mockReturnValue({
            analyzeAudio: mockAnalyzeAudio
        });
    });

    it('renders correctly in initial state', () => {
        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);

        expect(screen.getByText(/Drop your album or stems here/i)).toBeInTheDocument();
        expect(screen.getByText(/Select Files/i)).toBeInTheDocument();
    });

    it('handles file selection via input', async () => {
        mockAnalyzeAudio.mockResolvedValue({ bpm: 120, key: 'C' });

        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);

        const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' });
        const input = screen.getByLabelText(/Select Files/i) as HTMLInputElement;

        fireEvent.change(input, { target: { files: [file] } });

        await waitFor(() => {
            expect(mockAnalyzeAudio).toHaveBeenCalledWith(file, expect.any(Function));
        });

        await waitFor(() => {
            expect(mockOnFilesAnalyzed).toHaveBeenCalledWith([
                { file, analysis: { bpm: 120, key: 'C' } }
            ]);
        });
    });

    it('shows error for invalid file types', async () => {
        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);

        const file = new File(['text content'], 'test.txt', { type: 'text/plain' });
        const input = screen.getByLabelText(/Select Files/i) as HTMLInputElement;

        fireEvent.change(input, { target: { files: [file] } });

        expect(screen.getByText(/Please upload valid audio files/i)).toBeInTheDocument();
        expect(mockAnalyzeAudio).not.toHaveBeenCalled();
    });

    it('handles drag and drop interactions', async () => {
        mockAnalyzeAudio.mockResolvedValue({ bpm: 120, key: 'C' });

        const { container } = render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);
        const dropZone = container.querySelector('.glass-panel');

        if (!dropZone) throw new Error('Drop zone not found');

        // Drag enter
        fireEvent.dragEnter(dropZone);
        expect(dropZone).toHaveClass('highlight');

        // Drag leave
        fireEvent.dragLeave(dropZone);
        expect(dropZone).not.toHaveClass('highlight');

        // Drop
        const file = new File(['audio content'], 'test.wav', { type: 'audio/wav' });
        const dropEvent = {
            preventDefault: vi.fn(),
            stopPropagation: vi.fn(),
            dataTransfer: {
                files: [file]
            }
        };

        fireEvent.drop(dropZone, dropEvent);

        await waitFor(() => {
            expect(mockAnalyzeAudio).toHaveBeenCalledWith(file, expect.any(Function));
        });
    });

    it('displays processing tracks and progress', async () => {
        let progressCallback: (p: number) => void = () => {};
        mockAnalyzeAudio.mockImplementation((_file, onProgress) => {
            progressCallback = onProgress;
            return new Promise((_resolve) => {
                // Don't resolve immediately so we can check progress state
            });
        });

        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);

        const file = new File(['audio content'], 'track1.mp3', { type: 'audio/mpeg' });
        const input = screen.getByLabelText(/Select Files/i);
        fireEvent.change(input, { target: { files: [file] } });

        await waitFor(() => {
            expect(screen.getByText(/Batch Processing/i)).toBeInTheDocument();
            expect(screen.getByText('track1.mp3')).toBeInTheDocument();
        });

        // Update progress
        await waitFor(() => {
            progressCallback(45);
        });

        expect(screen.getByText('45%')).toBeInTheDocument();
    });

    it('handles analysis failure for some tracks', async () => {
        const file1 = new File(['audio 1'], 'track1.mp3', { type: 'audio/mpeg' });
        const file2 = new File(['audio 2'], 'track2.mp3', { type: 'audio/mpeg' });

        mockAnalyzeAudio
            .mockResolvedValueOnce({ bpm: 100 }) // Success for track 1
            .mockResolvedValueOnce(null); // Failure for track 2

        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);

        const input = screen.getByLabelText(/Select Files/i);
        fireEvent.change(input, { target: { files: [file1, file2] } });

        await waitFor(() => {
            expect(mockOnFilesAnalyzed).toHaveBeenCalledWith([
                { file: file1, analysis: { bpm: 100 } }
            ]);
        });

        expect(screen.getByText('error')).toBeInTheDocument();
    });

    it('shows error message if all analysis fails', async () => {
        // Use a promise that resolves to null to ensure processAllFiles completes
        mockAnalyzeAudio.mockResolvedValue(null);

        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={false} />);

        const file = new File(['audio content'], 'fail.mp3', { type: 'audio/mpeg' });
        const input = screen.getByLabelText(/Select Files/i);
        fireEvent.change(input, { target: { files: [file] } });

        // We need to wait for the analysisPromises to finish in processAllFiles
        await waitFor(() => {
            expect(mockAnalyzeAudio).toHaveBeenCalled();
        });

        await waitFor(() => {
            // After analysisPromises finish, it should show the error if validResults.length === 0
            expect(screen.getByText(/Failed to analyze the uploaded tracks/i)).toBeInTheDocument();
        }, { timeout: 2000 });
    });

    it('displays syncing message when isAnalyzing is true', async () => {
        mockAnalyzeAudio.mockResolvedValue({ bpm: 120 });

        render(<UploadSection onFilesAnalyzed={mockOnFilesAnalyzed} isAnalyzing={true} />);

        const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' });
        const input = screen.getByLabelText(/Select Files/i);
        fireEvent.change(input, { target: { files: [file] } });

        await waitFor(() => {
            expect(screen.getByText(/Syncing batch with server and GCS/i)).toBeInTheDocument();
        });
    });
});
