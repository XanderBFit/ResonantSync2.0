import { useState, useEffect } from 'react';
import { Search, Music, Database, Share2, Check, X, Trash2, Scissors, Loader2, Download } from 'lucide-react';
import { useToast, ToastContainer } from './Toast';
import { getAuthHeader } from '../lib/apiAuth';

interface VaultItem {
    fileId: string;
    metadata: any;
    downloadUrl: string;
    oneSheetUrl: string;
    masterUrl?: string;
    isMaster: boolean;
    createdAt: string;
}

interface PromoLinks {
    '15s'?: string;
    '30s'?: string;
    '60s'?: string;
}

interface VaultProps {
    uid: string;
    onProcessNew: () => void;
}

export function Vault({ uid, onProcessNew }: VaultProps) {
    const [tracks, setTracks] = useState<VaultItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [selectedMood, setSelectedMood] = useState('all');
    const [selectedIds, setSelectedIds] = useState<string[]>([]);
    const [isSharing, setIsSharing] = useState(false);
    const [pitchTitle, setPitchTitle] = useState('');
    const [pitchClient, setPitchClient] = useState('');
    const [generatedLink, setGeneratedLink] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [promoState, setPromoState] = useState<Record<string, { loading: boolean; links?: PromoLinks; error?: string }>>({});
    const { toasts, addToast, dismiss } = useToast();

    useEffect(() => {
        const fetchVault = async () => {
            try {
                const headers = await getAuthHeader();
                const res = await fetch(`/api/vault?uid=${uid}`, { headers });
                if (res.ok) {
                    const data = await res.json();
                    setTracks(data);
                }
            } catch (err) {
                console.error("Failed to fetch vault:", err);
            } finally {
                setLoading(false);
            }
        };
        fetchVault();
    }, [uid]);

    const filteredTracks = tracks.filter(t => {
        const matchesSearch = t.metadata.title?.toLowerCase().includes(search.toLowerCase()) ||
            t.metadata.artist?.toLowerCase().includes(search.toLowerCase());
        const matchesMood = selectedMood === 'all' || t.metadata.mood?.toLowerCase().includes(selectedMood.toLowerCase());
        return matchesSearch && matchesMood;
    });

    const toggleSelect = (id: string) => {
        setSelectedIds(prev =>
            prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
        );
    };

    const handleDeleteTrack = async (e: React.MouseEvent, fileId: string) => {
        e.stopPropagation();
        if (!confirm('Remove this track from your vault? This cannot be undone.')) return;
        setDeletingId(fileId);
        try {
            const headers = await getAuthHeader();
            const res = await fetch(`/api/vault/${fileId}`, { method: 'DELETE', headers });
            if (!res.ok) throw new Error('Delete failed');
            setTracks(prev => prev.filter(t => t.fileId !== fileId));
            setSelectedIds(prev => prev.filter(id => id !== fileId));
            addToast('Track removed from vault.', 'success');
        } catch {
            addToast('Failed to delete track. Please try again.', 'error');
        } finally {
            setDeletingId(null);
        }
    };

    const handleGeneratePromos = async (e: React.MouseEvent, fileId: string) => {
        e.stopPropagation();
        setPromoState(prev => ({ ...prev, [fileId]: { loading: true } }));
        try {
            const headers = await getAuthHeader();
            const res = await fetch(`/api/promos/${fileId}`, { method: 'POST', headers });
            if (!res.ok) throw new Error('Generation failed');
            const links: PromoLinks = await res.json();
            setPromoState(prev => ({ ...prev, [fileId]: { loading: false, links } }));
            addToast('Promo cuts ready for download!', 'success');
        } catch {
            setPromoState(prev => ({ ...prev, [fileId]: { loading: false, error: 'Failed' } }));
            addToast('Failed to generate promo cuts.', 'error');
        }
    };

    const handleDownload = async (e: React.MouseEvent<HTMLAnchorElement>, url: string) => {
        e.preventDefault();
        try {
            const headers = await getAuthHeader();
            const res = await fetch(url, { headers });
            if (!res.ok) throw new Error("Download failed");

            const blob = await res.blob();
            const objectUrl = window.URL.createObjectURL(blob);

            // Try to extract filename from Content-Disposition
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
            addToast('Failed to download file.', 'error');
        }
    };

    const handleCreatePitch = async () => {
        if (selectedIds.length === 0) return;
        setIsSharing(true);
    };

    const finalizePitch = async () => {
        try {
            const headers = await getAuthHeader();
            const res = await fetch('/api/pitches', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...headers },
                body: JSON.stringify({
                    uid,
                    title: pitchTitle || "Cinematic Pitch",
                    clientName: pitchClient || "Sync Professional",
                    trackIds: selectedIds
                })
            });
            const data = await res.json();
            const link = `${window.location.origin}?pitch=${data.pitchId}`;
            setGeneratedLink(link);
        } catch {
            addToast("Failed to create pitch link.", 'error');
        }
    };

    const moods = ['all', 'cinematic', 'dark', 'upbeat', 'lo-fi'];

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
                <div className="w-12 h-12 rounded-full border-2 border-accent-cyan/20 border-t-accent-cyan animate-spin" />
                <p className="text-text-secondary animate-pulse">Accessing the Vault...</p>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto space-y-8 animate-fade-in pb-20">
            <ToastContainer toasts={toasts} onDismiss={dismiss} />

            {/* Vault Header & Filters */}
            <div className="glass-panel p-6 flex flex-col md:flex-row justify-between items-center gap-6">
                <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-full bg-accent-blue/10 flex items-center justify-center text-accent-blue">
                        <Database size={24} />
                    </div>
                    <div>
                        <h2 className="text-2xl font-bold text-white uppercase tracking-widest">The Vault</h2>
                        <p className="text-sm text-text-secondary">{tracks.length} Master Assets Persisted</p>
                    </div>
                </div>

                <div className="flex flex-col sm:flex-row gap-4 w-full md:w-auto">
                    <button
                        onClick={onProcessNew}
                        className="glass-button primary px-6 py-2 flex items-center justify-center gap-2 whitespace-nowrap order-last md:order-first shadow-[0_0_20px_rgba(2,180,211,0.2)]"
                    >
                        <Music size={18} />
                        PROCESS NEW MASTERS
                    </button>

                    <div className="relative group flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary group-focus-within:text-accent-cyan transition-colors" size={18} />
                        <input
                            type="text"
                            placeholder="Search Library..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="glass-input pl-10 w-full md:w-64"
                        />
                    </div>
                </div>
            </div>

            {/* Filter Chips */}
            <div className="flex gap-2 overflow-x-auto pb-4 no-scrollbar">
                {moods.map(mood => (
                    <button
                        key={mood}
                        onClick={() => setSelectedMood(mood)}
                        className={`px-4 py-2 rounded-full text-xs font-bold transition-all border whitespace-nowrap ${selectedMood === mood
                            ? 'bg-accent-cyan/20 border-accent-cyan text-accent-cyan shadow-[0_0_15px_rgba(2,180,211,0.3)]'
                            : 'bg-white/5 border-white/10 text-text-secondary hover:border-white/20'
                            }`}
                    >
                        {mood.toUpperCase()}
                    </button>
                ))}
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredTracks.map((track) => {
                    const isSelected = selectedIds.includes(track.fileId);
                    const promo = promoState[track.fileId];
                    return (
                        <div
                            key={track.fileId}
                            onClick={() => toggleSelect(track.fileId)}
                            className={`glass-panel p-6 hover:bg-white/[0.04] transition-all border group relative cursor-pointer flex flex-col ${isSelected ? 'border-accent-cyan shadow-[0_0_20px_rgba(2,180,211,0.2)]' : 'border-white/10'
                                }`}
                        >
                            {/* Selection Checkmark */}
                            <div className={`absolute top-4 right-12 w-6 h-6 rounded-full border flex items-center justify-center transition-all ${isSelected ? 'bg-accent-cyan border-accent-cyan text-black' : 'bg-black/20 border-white/10 text-transparent group-hover:border-white/30'
                                }`}>
                                <Check size={14} strokeWidth={4} />
                            </div>

                            {/* Delete Button */}
                            <button
                                onClick={(e) => handleDeleteTrack(e, track.fileId)}
                                className="absolute top-4 right-4 w-6 h-6 flex items-center justify-center text-text-secondary hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                                title="Remove from vault"
                            >
                                {deletingId === track.fileId
                                    ? <Loader2 size={14} className="animate-spin" />
                                    : <Trash2 size={14} />
                                }
                            </button>

                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-lg bg-accent-cyan/10 flex items-center justify-center text-accent-cyan">
                                        <Music size={20} />
                                    </div>
                                    <div>
                                        <h3 className="font-bold text-white max-w-[150px] truncate">{track.metadata.title}</h3>
                                        <p className="text-xs text-text-secondary">{track.metadata.artist}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-3 mb-4">
                                <div className="bg-black/30 rounded-lg p-2 border border-white/5">
                                    <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1">Sonic Profile</p>
                                    <p className="text-xs font-medium text-accent-cyan">{track.metadata.bpm} BPM • {track.metadata.key} {track.metadata.scale}</p>
                                </div>
                                <div className="bg-black/30 rounded-lg p-2 border border-white/5">
                                    <p className="text-[10px] text-text-secondary uppercase tracking-wider mb-1">Vibe</p>
                                    <p className="text-xs font-medium text-white">{track.metadata.mood}</p>
                                </div>
                            </div>

                            <div className="flex gap-2 mb-4" onClick={e => e.stopPropagation()}>
                                <a
                                    href={track.downloadUrl}
                                    onClick={(e) => handleDownload(e, track.downloadUrl)}
                                    className="flex-1 glass-button text-xs py-2 bg-white/5 hover:bg-white/10"
                                >
                                    MP3
                                </a>
                                <a
                                    href={track.oneSheetUrl}
                                    download
                                    className="flex-1 glass-button text-xs py-2 border-accent-cyan/20 text-accent-cyan hover:bg-accent-cyan/10"
                                >
                                    One-Sheet
                                </a>
                            </div>

                            {/* Promo Cuts */}
                            <div className="border-t border-white/5 pt-4 mt-auto" onClick={e => e.stopPropagation()}>
                                {!promo ? (
                                    <button
                                        onClick={(e) => handleGeneratePromos(e, track.fileId)}
                                        className="glass-button text-xs text-accent-purple border-accent-purple/20 hover:bg-accent-purple/5 flex items-center gap-1.5 w-full justify-center py-2"
                                    >
                                        <Scissors size={13} />
                                        Generate Promo Cuts
                                    </button>
                                ) : promo.loading ? (
                                    <div className="flex items-center justify-center gap-2 text-xs text-text-secondary py-2">
                                        <Loader2 size={13} className="animate-spin" />
                                        Finding peak section...
                                    </div>
                                ) : promo.error ? (
                                    <p className="text-xs text-red-400 text-center py-1">{promo.error}</p>
                                ) : (
                                    <div className="flex gap-2 animate-in fade-in duration-500">
                                        {(['15s', '30s', '60s'] as const).map(len =>
                                            promo.links?.[len] ? (
                                                <a
                                                    key={len}
                                                    href={promo.links![len]}
                                                    download
                                                    className="flex-1 glass-button text-xs py-1.5 text-accent-purple border-accent-purple/20 hover:bg-accent-purple/5 flex items-center justify-center gap-1"
                                                >
                                                    <Download size={11} />{len}
                                                </a>
                                            ) : null
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}

                {filteredTracks.length === 0 && (
                    <div className="col-span-full py-24 text-center glass-panel border-dashed border-white/10 flex flex-col items-center justify-center">
                        <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6 text-text-secondary opacity-30">
                            <Database size={40} />
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">The Vault is empty</h3>
                        <p className="text-text-secondary mb-8 max-w-sm mx-auto">Your processed masters and cinematic one-sheets will appear here for instant retrieval.</p>
                        <button
                            onClick={onProcessNew}
                            className="glass-button primary px-10"
                        >
                            PROCESS YOUR FIRST MASTER
                        </button>
                    </div>
                )}
            </div>

            {/* Selection Action Bar */}
            {selectedIds.length > 0 && (
                <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-10 duration-500">
                    <div className="glass-panel glass-deep px-8 py-4 flex items-center gap-8 shadow-2xl border-accent-cyan/30">
                        <div className="flex flex-col">
                            <span className="text-accent-cyan font-bold text-lg">{selectedIds.length} Tracks Selected</span>
                            <span className="text-xs text-text-secondary">Ready for sharing</span>
                        </div>
                        <div className="h-10 w-[1px] bg-white/10" />
                        <div className="flex gap-4">
                            <button
                                onClick={() => setSelectedIds([])}
                                className="glass-button text-text-secondary hover:text-white"
                            >
                                Clear
                            </button>
                            <button
                                onClick={handleCreatePitch}
                                className="glass-button primary px-8 py-3 flex items-center gap-2 shadow-[0_0_20px_rgba(2,180,211,0.3)]"
                            >
                                <Share2 size={18} />
                                CREATE PITCH LINK
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Sharing Overlay */}
            {isSharing && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-xl animate-fade-in">
                    <div className="glass-panel glass-deep max-w-md w-full p-8 relative overflow-hidden">
                        <button
                            onClick={() => {
                                setIsSharing(false);
                                setGeneratedLink(null);
                            }}
                            className="absolute top-4 right-4 text-text-secondary hover:text-white"
                            title="Close"
                        >
                            <X size={24} />
                        </button>

                        {!generatedLink ? (
                            <>
                                <h3 className="text-2xl font-bold text-white mb-2">Generate Pitch Page</h3>
                                <p className="text-text-secondary mb-6 text-sm">Create a high-end, public landing page for music supervisors to review these {selectedIds.length} tracks.</p>

                                <div className="space-y-4">
                                    <div>
                                        <label className="text-xs font-bold text-text-secondary uppercase tracking-widest block mb-2">Pitch Title</label>
                                        <input
                                            type="text"
                                            className="glass-input w-full"
                                            placeholder="e.g. Modern Minimalist Strings for [Project]"
                                            value={pitchTitle}
                                            onChange={e => setPitchTitle(e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <label className="text-xs font-bold text-text-secondary uppercase tracking-widest block mb-2">Client / Agency Name</label>
                                        <input
                                            type="text"
                                            className="glass-input w-full"
                                            placeholder="e.g. White Lotus Season 3"
                                            value={pitchClient}
                                            onChange={e => setPitchClient(e.target.value)}
                                        />
                                    </div>
                                    <button
                                        onClick={finalizePitch}
                                        className="glass-button primary w-full py-4 font-bold mt-4"
                                    >
                                        GENERATE PUBLIC LINK
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className="text-center animate-fade-in">
                                <div className="w-16 h-16 rounded-full bg-success/20 text-success flex items-center justify-center mx-auto mb-6">
                                    <Check size={32} />
                                </div>
                                <h3 className="text-2xl font-bold text-white mb-2">Pitch Link Generated</h3>
                                <p className="text-text-secondary mb-8 text-sm">Send this link to your client. They will see a high-end cinematic player with all metadata.</p>

                                <div className="glass-panel bg-black/40 p-4 border-white/5 mb-8 flex items-center justify-between gap-4">
                                    <code className="text-xs text-accent-cyan truncate flex-1 text-left">{generatedLink}</code>
                                    <button
                                        onClick={() => {
                                            navigator.clipboard.writeText(generatedLink);
                                            addToast('Link copied to clipboard!', 'success');
                                        }}
                                        className="text-white hover:text-accent-cyan transition-colors"
                                    >
                                        Copy
                                    </button>
                                </div>

                                <button
                                    onClick={() => {
                                        setIsSharing(false);
                                        setGeneratedLink(null);
                                        setSelectedIds([]);
                                    }}
                                    className="glass-button secondary w-full py-3"
                                >
                                    DONE
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
