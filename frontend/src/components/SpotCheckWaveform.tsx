import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause } from 'lucide-react';

interface SpotCheckWaveformProps {
    audioBuffer: AudioBuffer;
    onPlayStateChange?: (isPlaying: boolean) => void;
}

export function SpotCheckWaveform({ audioBuffer, onPlayStateChange }: SpotCheckWaveformProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const wavesurferRef = useRef<WaveSurfer | null>(null);
    const [isPlaying, setIsPlaying] = useState(false);

    useEffect(() => {
        if (!containerRef.current) return;

        const ws = WaveSurfer.create({
            container: containerRef.current,
            waveColor: 'rgba(6, 182, 212, 0.3)', // Cyan muted
            progressColor: '#a855f7', // Purple
            cursorColor: '#06b6d4',
            barWidth: 2,
            barRadius: 3,
            height: 40,
            cursorWidth: 1,
            interact: true,
            normalize: true,
            fillParent: true,
        });

        // In v7, we create a pseudo-URL from the buffer data or use load() with options
        // Easiest for AudioBuffer is to convert to blob and load
        const blob = bufferToWavBlob(audioBuffer);
        const url = URL.createObjectURL(blob);
        ws.load(url);

        ws.on('play', () => {
            setIsPlaying(true);
            onPlayStateChange?.(true);
        });

        ws.on('pause', () => {
            setIsPlaying(false);
            onPlayStateChange?.(false);
        });

        wavesurferRef.current = ws;

        return () => {
            ws.destroy();
            URL.revokeObjectURL(url);
        };
    }, [audioBuffer]);

    const togglePlay = () => {
        wavesurferRef.current?.playPause();
    };

    return (
        <div className="flex items-center gap-4 w-full bg-black/20 rounded-lg p-2 border border-white/5 group hover:border-accent-cyan/20 transition-all">
            <button
                onClick={togglePlay}
                className="w-8 h-8 rounded-full bg-accent-cyan/20 flex items-center justify-center text-accent-cyan hover:bg-accent-cyan/40 transition-colors"
                title={isPlaying ? "Pause" : "Play Spot Check"}
            >
                {isPlaying ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
            </button>
            <div ref={containerRef} className="flex-1 min-w-0" />
        </div>
    );
}

// Helper to convert AudioBuffer to a WAV blob for WaveSurfer v7 loading
function bufferToWavBlob(buffer: AudioBuffer): Blob {
    const numOfChan = buffer.numberOfChannels;
    const length = buffer.length * numOfChan * 2 + 44;
    const arrayBuffer = new ArrayBuffer(length);
    const view = new DataView(arrayBuffer);
    const channels = [];
    let offset = 0;
    let pos = 0;

    // write WAVE header
    setUint32(0x46464952);                         // "RIFF"
    setUint32(length - 8);                         // file length - 8
    setUint32(0x45564157);                         // "WAVE"
    setUint32(0x20746d66);                         // "fmt " chunk
    setUint32(16);                                 // length = 16
    setUint16(1);                                  // PCM (uncompressed)
    setUint16(numOfChan);
    setUint32(buffer.sampleRate);
    setUint32(buffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
    setUint16(numOfChan * 2);                      // block-align
    setUint16(16);                                 // 16-bit
    setUint32(0x61746164);                         // "data" - chunk
    setUint32(length - pos - 4);                   // chunk length

    // write interleaved data
    for (let i = 0; i < buffer.numberOfChannels; i++) {
        channels.push(buffer.getChannelData(i));
    }

    while (pos < length) {
        for (let i = 0; i < numOfChan; i++) {
            let sample = Math.max(-1, Math.min(1, channels[i][offset]));
            sample = (sample < 0 ? sample * 0x8000 : sample * 0x7FFF);
            view.setInt16(pos, sample, true);
            pos += 2;
        }
        offset++;
    }

    return new Blob([arrayBuffer], { type: "audio/wav" });

    function setUint16(data: number) {
        view.setUint16(pos, data, true);
        pos += 2;
    }

    function setUint32(data: number) {
        view.setUint32(pos, data, true);
        pos += 4;
    }
}
