import { useState, useEffect, useRef } from 'react';
import { Download, FileText, Play, Pause, ExternalLink, Mail } from 'lucide-react';
import WaveSurfer from 'wavesurfer.js';

interface PitchData {
    title: string;
    clientName: string;
    tracks: Array<{
        id: string;
        metadata: any;
        urls: {
            mp3: string;
            oneSheet: string;
        };
    }>;
}

export function PitchView({ pitchId }: { pitchId: string }) {
    const [pitch, setPitch] = useState<PitchData | null>(null);
    const [loading, setLoading] = useState(true);
    const [playingId, setPlayingId] = useState<string | null>(null);
    const waveRef = useRef<Record<string, WaveSurfer>>({});
    const containerRefs = useRef<Record<string, HTMLDivElement | null>>({});

    useEffect(() => {
        const fetchPitch = async () => {
            try {
                const res = await fetch(`/api/pitches/${pitchId}`);
                if (!res.ok) throw new Error("Pitch not found");
                const data = await res.json();
                setPitch(data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchPitch();
    }, [pitchId]);

    const initWaveform = (id: string, url: string) => {
        if (waveRef.current[id] || !containerRefs.current[id]) return;

        const ws = WaveSurfer.create({
            container: containerRefs.current[id]!,
            waveColor: 'rgba(2, 180, 211, 0.2)',
            progressColor: '#02b4d3',
            cursorColor: '#02b4d3',
            barWidth: 2,
            barRadius: 3,
            cursorWidth: 1,
            height: 40,
            normalize: true,
            interact: true
        });

        ws.load(url);
        ws.on('play', () => setPlayingId(id));
        ws.on('pause', () => setPlayingId(null));
        ws.on('finish', () => setPlayingId(null));

        waveRef.current[id] = ws;
    };

    const togglePlay = (id: string) => {
        Object.keys(waveRef.current).forEach(key => {
            if (key !== id) waveRef.current[key].pause();
        });
        waveRef.current[id]?.playPause();
    };

    if (loading) return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-accent-cyan/20 border-t-accent-cyan rounded-full animate-spin" />
                <p className="text-accent-cyan font-bold tracking-widest animate-pulse">PREPARING PITCH...</p>
            </div>
        </div>
    );

    if (!pitch) return (
        <div className="min-h-screen bg-[#050505] flex items-center justify-center text-white">
            <div className="text-center">
                <h1 className="text-4xl font-bold mb-4">404</h1>
                <p className="text-text-secondary">This pitch has expired or does not exist.</p>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-[#050505] text-white">
            {/* Cinematic Hero Header */}
            <header className="relative py-24 px-6 overflow-hidden border-b border-white/5">
                <div className="absolute inset-0 bg-gradient-to-b from-accent-cyan/5 to-transparent pointer-events-none" />
                <div className="max-w-5xl mx-auto relative z-10 text-center">
                    <div className="inline-block px-4 py-1 rounded-full border border-accent-cyan/20 bg-accent-cyan/5 text-accent-cyan text-xs font-bold tracking-[0.2em] mb-6 animate-fade-in">
                        EXCLUSIVE PITCH
                    </div>
                    <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight animate-in slide-in-from-bottom-4 duration-700">
                        {pitch.title}
                    </h1>
                    <div className="flex items-center justify-center gap-4 text-text-secondary animate-fade-in delay-200">
                        <span className="text-xl font-medium tracking-wide">For: <span className="text-white">{pitch.clientName}</span></span>
                    </div>
                </div>
            </header>

            <main className="max-w-5xl mx-auto px-6 py-20">
                <div className="space-y-6">
                    {pitch.tracks.map((track) => (
                        <div
                            key={track.id}
                            className="glass-panel glass-deep p-8 hover:bg-white/[0.04] transition-all border-white/10 group animate-in slide-in-from-bottom-8 duration-700 pitch-track"
                        >
                            <div className="flex flex-col md:flex-row gap-8 items-center">
                                {/* Play Control */}
                                <button
                                    onClick={() => togglePlay(track.id)}
                                    className="w-16 h-16 rounded-full bg-accent-cyan flex items-center justify-center text-black hover:scale-105 transition-transform shrink-0 shadow-[0_0_20px_rgba(2,180,211,0.4)]"
                                >
                                    {playingId === track.id ? <Pause fill="black" /> : <Play fill="black" className="ml-1" />}
                                </button>

                                <div className="flex-1 w-full overflow-hidden">
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <h3 className="text-2xl font-bold text-white mb-1 group-hover:text-accent-cyan transition-colors">
                                                {track.metadata.title}
                                            </h3>
                                            <p className="text-text-secondary font-medium tracking-wide">
                                                {track.metadata.bpm} BPM • {track.metadata.key} {track.metadata.scale} • {track.metadata.mood}
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <a
                                                href={track.urls.mp3}
                                                download
                                                className="glass-button p-3 hover:bg-accent-cyan/10 hover:text-accent-cyan transition-all"
                                                title="Download MP3"
                                            >
                                                <Download size={20} />
                                            </a>
                                            <a
                                                href={track.urls.oneSheet}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="glass-button p-3 hover:bg-accent-cyan/10 hover:text-accent-cyan transition-all"
                                                title="View One-Sheet"
                                            >
                                                <FileText size={20} />
                                            </a>
                                        </div>
                                    </div>

                                    {/* Waveform Visualization */}
                                    <div
                                        ref={el => {
                                            if (el) {
                                                containerRefs.current[track.id] = el;
                                                initWaveform(track.id, track.urls.mp3);
                                            }
                                        }}
                                        className="mt-4 opacity-60 group-hover:opacity-100 transition-opacity"
                                    />
                                </div>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Call to Action Footer */}
                <footer className="mt-20 pt-20 border-t border-white/5 text-center">
                    <h4 className="text-2xl font-bold mb-6">Interested in licensing?</h4>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <button className="glass-button primary px-12 py-4 flex items-center gap-3 text-lg">
                            <Mail size={20} />
                            REQUEST LICENSE
                        </button>
                        <button className="glass-button secondary px-12 py-4 flex items-center gap-3 text-lg">
                            <ExternalLink size={20} />
                            VIEW ALL RELEASES
                        </button>
                    </div>
                    <p className="mt-12 text-sm text-text-secondary opacity-40">
                        &copy; 2026 ResonantCrab Dynamics • AI-Driven Sync Management
                    </p>
                </footer>
            </main>
        </div>
    );
}
