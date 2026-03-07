import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface AnalysisDiagnosticProps {
    onComplete: () => void;
    data: {
        bpm: string;
        key: string;
        lufs: string;
        energy: string;
    };
}

export function AnalysisDiagnostic({ onComplete, data }: AnalysisDiagnosticProps) {
    const [loadedStates, setLoadedStates] = useState([false, false, false, false]);
    const [showProceed, setShowProceed] = useState(false);
    const [allReady, setAllReady] = useState(false);

    useEffect(() => {
        // Simulated staggered loading
        const timers = [
            setTimeout(() => setLoadedStates(prev => [true, prev[1], prev[2], prev[3]]), 800),
            setTimeout(() => setLoadedStates(prev => [prev[0], true, prev[2], prev[3]]), 1600),
            setTimeout(() => setLoadedStates(prev => [prev[0], prev[1], true, prev[3]]), 2200),
            setTimeout(() => setLoadedStates(prev => [prev[0], prev[1], prev[2], true]), 2800),
        ];

        const finalTimer = setTimeout(() => {
            setAllReady(true);
            setTimeout(() => setShowProceed(true), 800);
        }, 3200);

        return () => {
            timers.forEach(clearTimeout);
            clearTimeout(finalTimer);
        };
    }, []);

    const cards = [
        { label: 'PRIMARY TEMPO', value: data.bpm, sub: 'BPM' },
        { label: 'KEY SIGNATURE', value: data.key, sub: 'HARMONIC' },
        { label: 'LOUDNESS (INTEGRATED)', value: data.lufs, sub: 'LUFS' },
        { label: 'ENERGY INDEX', value: data.energy, sub: 'DYNAMIC' },
    ];

    return (
        <div className="relative w-full max-w-4xl mx-auto py-12 flex flex-col items-center">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full relative z-10">
                {cards.map((card, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{
                            opacity: 1,
                            y: 0,
                            borderColor: loadedStates[i] ? 'rgba(6, 182, 212, 0.4)' : 'rgba(255, 255, 255, 0.1)'
                        }}
                        transition={{
                            delay: i * 0.2,
                            borderColor: { duration: 0.3 }
                        }}
                        className={`
                            backdrop-blur-xl bg-black/40 border-2 rounded-xl p-6 flex flex-col items-center justify-center min-h-[160px] transition-shadow duration-300
                            ${loadedStates[i] ? 'shadow-[0_0_20px_rgba(6,182,212,0.1)]' : 'animate-pulse opacity-50'}
                            ${allReady ? 'border-accent-cyan/60' : ''}
                        `}
                    >
                        <span className="font-sans text-[10px] tracking-[0.2em] text-gray-400 uppercase mb-4 text-center">
                            {card.label}
                        </span>

                        <div className="flex flex-col items-center">
                            {loadedStates[i] ? (
                                <motion.span
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="font-mono text-3xl text-cyan-400 drop-shadow-[0_0_10px_rgba(6,182,212,0.5)]"
                                >
                                    {card.value}
                                </motion.span>
                            ) : (
                                <div className="h-9 w-24 bg-white/5 rounded animate-pulse" />
                            )}
                            <span className="text-[10px] text-gray-500 font-mono mt-1">{card.sub}</span>
                        </div>
                    </motion.div>
                ))}
            </div>

            <AnimatePresence>
                {showProceed && (
                    <motion.button
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        transition={{ type: "spring", bounce: 0.4 }}
                        onClick={onComplete}
                        className="mt-12 group relative px-8 py-4 bg-purple-600/20 border border-cyan-400/30 rounded-full font-bold text-white tracking-widest uppercase text-sm overflow-hidden transition-all hover:bg-purple-600/30 hover:border-cyan-400"
                        title="Proceed to Metadata Editor"
                        aria-label="Proceed to Metadata Editor"
                    >
                        <span className="relative z-10 flex items-center gap-2">
                            Proceed to Pitch & Export
                            <motion.span
                                animate={{ x: [0, 5, 0] }}
                                transition={{ repeat: Infinity, duration: 1 }}
                            >
                                →
                            </motion.span>
                        </span>
                        <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/0 via-cyan-400/10 to-cyan-400/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700" />
                    </motion.button>
                )}
            </AnimatePresence>
        </div>
    );
}
