import { useState } from 'react';
import { Download, FileText, CheckCircle2, Search, ArrowLeft, Database, Scissors, Loader2 } from 'lucide-react';
import { getAuthHeader } from '../lib/apiAuth';

interface ProcessingResult {
    fileId: string;
    downloadUrl: string;
    oneSheetUrl: string;
    masterUrl?: string;
}

interface TagScannerProps {
    results: ProcessingResult[];
    onStartOver: () => void;
    onGoToVault: () => void;
}

interface PromoLinks {
    '15s'?: string;
    '30s'?: string;
    '60s'?: string;
}

export function TagScanner({ results, onStartOver, onGoToVault }: TagScannerProps) {
    const [promoState, setPromoState] = useState<Record<string, { loading: boolean; links?: PromoLinks; error?: string }>>({});

    const handleDownload = async (e: React.MouseEvent<HTMLAnchorElement>, url: string) => {
        e.preventDefault();
        try {
            const headers = await getAuthHeader();
            const res = await fetch(url, { headers });
            if (!res.ok) throw new Error("Download failed");

            const blob = await res.blob();
            const objectUrl = window.URL.createObjectURL(blob);

            let filename = 'download.mp3';
            const contentDisposition = res.headers.get('Content-Disposition');
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?([^"]+)"?/);
                if (match && match[1]) filename = match[1];
            } else {
                filename = url.split('/').pop() + '.mp3';
            }

            const a = document.createElement('a');
            a.href = objectUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(objectUrl);
        } catch (err) {
            console.error('Download error:', err);
        }
    };

    const handleGeneratePromos = async (fileId: string) => {
        setPromoState(prev => ({ ...prev, [fileId]: { loading: true } }));
        try {
            const res = await fetch(`/api/promos/${fileId}`, { method: 'POST' });
            if (!res.ok) throw new Error('Generation failed');
            const links: PromoLinks = await res.json();
            setPromoState(prev => ({ ...prev, [fileId]: { loading: false, links } }));
        } catch {
            setPromoState(prev => ({ ...prev, [fileId]: { loading: false, error: 'Failed to generate promos' } }));
        }
    };

    return (
        <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500 pb-20">
            <div className="flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-success/20 flex items-center justify-center text-success shrink-0">
                        <CheckCircle2 size={28} />
                    </div>
                    <div>
                        <h2 className="text-3xl font-bold text-text-primary">Batch Mastery Complete</h2>
                        <p className="text-text-secondary">All tracks have been processed, tagged, and transcoded to industry standards.</p>
                    </div>
                </div>
                <div className="flex flex-col sm:flex-row gap-3">
                    <button
                        onClick={onGoToVault}
                        className="glass-button text-text-secondary border-white/5 hover:bg-white/5 flex items-center gap-2"
                    >
                        <Database size={18} />
                        Go to Vault
                    </button>
                    <button
                        onClick={onStartOver}
                        className="glass-button secondary flex items-center gap-2"
                    >
                        <ArrowLeft size={18} />
                        New Batch
                    </button>
                    {results.length > 1 && (
                        <a
                            href={`/api/export-zip?fileIds=${results.map(r => r.fileId).join(',')}`}
                            className="glass-button primary flex items-center gap-2 bg-gradient-to-r from-accent-cyan to-accent-blue border-none"
                            download
                        >
                            <Download size={18} />
                            Download Master Package (.zip)
                        </a>
                    )}
                </div>
            </div>

            <div className="grid grid-cols-1 gap-6">
                {results.map((res) => (
                    <div key={res.fileId} className="glass-panel p-6 hover:bg-white/[0.04] transition-colors border-white/10 group">
                        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center text-accent-cyan group-hover:bg-accent-cyan/20 transition-colors">
                                    <Search size={22} />
                                </div>
                                <div>
                                    <h3 className="text-lg font-semibold text-white">Track ID: {res.fileId}</h3>
                                    <p className="text-xs text-text-secondary opacity-60">Verified &amp; Embedded</p>
                                </div>
                            </div>

                            <div className="flex flex-wrap gap-3 w-full md:w-auto">
                                {res.oneSheetUrl && (
                                    <a
                                        href={res.oneSheetUrl}
                                        download
                                        className="glass-button text-sm flex-1 md:flex-none py-2 text-accent-cyan border-accent-cyan/20 hover:bg-accent-cyan/5"
                                        title="Download PDF One-Sheet"
                                    >
                                        <FileText size={16} />
                                        One-Sheet
                                    </a>
                                )}
                                {res.masterUrl && (
                                    <a
                                        href={res.masterUrl}
                                        download
                                        className="glass-button text-sm flex-1 md:flex-none py-2 text-text-secondary border-white/10 hover:bg-white/5"
                                        title="Download Master AIFF/WAV"
                                    >
                                        <Download size={16} />
                                        Master
                                    </a>
                                )}
                                <a
                                    href={res.downloadUrl}
                                    onClick={(e) => handleDownload(e, res.downloadUrl)}
                                    className="glass-button primary text-sm flex-1 md:flex-none py-2 min-w-[140px]"
                                    title="Download Pitched 320kbps MP3"
                                >
                                    <Download size={16} />
                                    320kbps MP3
                                </a>
                            </div>
                        </div>

                        {/* Promo Cuts Section */}
                        <div className="mt-5 pt-5 border-t border-white/5">
                            {!promoState[res.fileId] ? (
                                <button
                                    onClick={() => handleGeneratePromos(res.fileId)}
                                    className="glass-button text-sm text-accent-purple border-accent-purple/20 hover:bg-accent-purple/5 flex items-center gap-2"
                                    title="Generate 15s, 30s, and 60s broadcast promos"
                                >
                                    <Scissors size={15} />
                                    Generate Promo Cuts
                                </button>
                            ) : promoState[res.fileId].loading ? (
                                <div className="flex items-center gap-2 text-sm text-text-secondary">
                                    <Loader2 size={15} className="animate-spin" />
                                    Analyzing peak section &amp; cutting promos...
                                </div>
                            ) : promoState[res.fileId].error ? (
                                <p className="text-sm text-red-400">{promoState[res.fileId].error}</p>
                            ) : (
                                <div className="flex flex-wrap gap-3 animate-in fade-in duration-500">
                                    <span className="text-xs text-text-secondary self-center mr-1">PROMOS:</span>
                                    {(['15s', '30s', '60s'] as const).map(len =>
                                        promoState[res.fileId]?.links?.[len] ? (
                                            <a
                                                key={len}
                                                href={promoState[res.fileId]!.links![len]}
                                                download
                                                className="glass-button text-xs py-1.5 px-3 text-accent-purple border-accent-purple/20 hover:bg-accent-purple/5 flex items-center gap-1.5"
                                            >
                                                <Download size={13} />
                                                {len} Cut
                                            </a>
                                        ) : null
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <div className="glass-panel p-8 bg-gradient-to-br from-accent-purple/5 to-transparent border-accent-purple/10">
                <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-full bg-accent-purple/20 flex items-center justify-center text-accent-purple shrink-0">
                        <Search size={20} />
                    </div>
                    <div>
                        <h4 className="font-semibold text-white mb-1">Metadata Verification</h4>
                        <p className="text-sm text-text-secondary">
                            All files have been injected with ID3v2.3 frames (for maximum DISCO compatibility) including BPM, Key, Energy, Mood, and your Publisher contact info.
                            These tags are fully searchable in DISCO, iTunes, and Serato.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
