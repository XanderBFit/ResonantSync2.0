import { useEffect, useRef } from 'react';

interface CanvasVisualizerProps {
    audioBuffer?: AudioBuffer | null;
}

export function CanvasVisualizer({ audioBuffer }: CanvasVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const analyzerRef = useRef<AnalyserNode | null>(null);
    const dataArrayRef = useRef<Uint8Array | null>(null);

    useEffect(() => {
        if (!audioBuffer) {
            analyzerRef.current = null;
            dataArrayRef.current = null;
            return;
        }

        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const analyzer = audioCtx.createAnalyser();
        analyzer.fftSize = 256;
        const bufferLength = analyzer.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);

        const source = audioCtx.createBufferSource();
        source.buffer = audioBuffer;
        source.loop = true;

        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 0; // Maintain cinematic silence

        source.connect(analyzer);
        analyzer.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        source.start(0);

        analyzerRef.current = analyzer;
        dataArrayRef.current = dataArray;

        return () => {
            source.stop();
            audioCtx.close();
        };
    }, [audioBuffer]);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrameId: number;
        const barCount = 128;
        const mockBars = new Array(barCount).fill(0).map(() => Math.random() * 50);

        const render = () => {
            const width = canvas.width = canvas.offsetWidth;
            const height = canvas.height = canvas.offsetHeight;
            ctx.clearRect(0, 0, width, height);

            const analyzer = analyzerRef.current;
            const dataArray = dataArrayRef.current;

            if (analyzer && dataArray) {
                analyzer.getByteFrequencyData(dataArray as any);
            }

            const barWidth = width / (barCount / 2); // Show half the spectrum for impact

            for (let i = 0; i < barCount / 2; i++) {
                let h = 0;

                if (dataArray) {
                    // Use real data
                    h = (dataArray[i] / 255) * height * 0.6;
                } else {
                    // Fallback to mock
                    const target = Math.random() * (height * 0.3);
                    mockBars[i] += (target - mockBars[i]) * 0.1;
                    h = mockBars[i];
                }

                const x = i * barWidth;
                const ratio = i / (barCount / 2);

                // Color mapping: Low (Purple) -> High (Cyan)
                const color = ratio < 0.5
                    ? `rgba(168, 85, 247, ${0.4 * (1 - ratio)})` // Purple
                    : `rgba(6, 182, 212, ${0.4 * ratio})`;      // Cyan

                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.roundRect(x + 2, height - h, barWidth - 4, h, [8, 8, 0, 0]);
                ctx.fill();
            }

            animationFrameId = requestAnimationFrame(render);
        };

        render();

        return () => cancelAnimationFrame(animationFrameId);
    }, []);

    return (
        <canvas
            ref={canvasRef}
            className="absolute inset-0 w-full h-full opacity-40 pointer-events-none z-0"
        />
    );
}
