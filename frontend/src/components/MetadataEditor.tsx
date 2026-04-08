import { useState, useEffect } from 'react';
import { CheckCircle2, Save } from 'lucide-react';
import { auth, db } from '../lib/firebase';
import { doc, getDoc } from 'firebase/firestore';
import { SpotCheckWaveform } from './SpotCheckWaveform';
import { type AnalyzedData, type TrackMetadata } from '../types/track';

export interface MetadataEditorProps {
    files: AnalyzedData[];
    onSave: (batch: { fileId: string, metadata: TrackMetadata }[]) => void;
    isProcessing: boolean;
    onPlayBuffer?: (buffer: AudioBuffer | null) => void;
}

export function MetadataEditor({ files, onSave, isProcessing, onPlayBuffer }: MetadataEditorProps) {
    const [bulkMetadata, setBulkMetadata] = useState({
        artist: files[0]?.artist || '',
        album: files[0]?.album || '',
        publisher: '',
        composer: '',
        contactName: '',
        contactEmail: '',
        oneStop: false,
    });

    const [tracks, setTracks] = useState<Record<string, TrackMetadata>>(() => {
        const initial: Record<string, TrackMetadata> = {};
        files.forEach(f => {
            if (f.fileId) {
                initial[f.fileId] = {
                    title: f.title || '',
                    bpm: f.bpm?.toString() || '',
                    key: f.key || '',
                    mood: f.mood || '',
                    genre: f.genre || '',
                    instruments: f.instruments?.join(', ') || '',
                    vocalPresence: f.vocalPresence || '',
                    isrc: '',
                };
            }
        });
        return initial;
    });

    useEffect(() => {
        const loadTemplate = async () => {
            if (!auth.currentUser) return;
            try {
                const userDoc = await getDoc(doc(db, 'userTemplates', auth.currentUser.uid));
                if (userDoc.exists()) {
                    const data = userDoc.data();
                    setBulkMetadata(prev => ({
                        ...prev,
                        publisher: data.publisher || prev.publisher,
                        composer: data.composer || prev.composer,
                        contactName: data.contactName || prev.contactName,
                        contactEmail: data.contactEmail || prev.contactEmail,
                        oneStop: data.oneStop !== undefined ? data.oneStop : prev.oneStop
                    }));
                }
            } catch (err) {
                console.error("Failed to load template:", err);
            }
        };
        loadTemplate();
    }, []);

    const handleBulkChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value, type, checked } = e.target;
        setBulkMetadata(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleTrackChange = (fileId: string, field: string, value: string) => {
        setTracks(prev => ({
            ...prev,
            [fileId]: { ...prev[fileId], [field]: value }
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const batch = files.map(f => ({
            fileId: f.fileId!,
            metadata: {
                ...bulkMetadata,
                ...tracks[f.fileId!],
                scale: files.find(file => file.fileId === f.fileId)?.scale || ''
            }
        }));
        onSave(batch);
    };

    return (
        <div className="w-full max-w-5xl mx-auto animate-fade-in space-y-8 pb-20">
            <div className="glass-panel p-8 relative overflow-hidden">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-cyan via-accent-blue to-accent-purple" />
                <div className="mb-8">
                    <h2 className="text-3xl font-bold mb-2 text-gradient-accent">Batch Metadata</h2>
                    <p className="text-text-secondary">Apply common attributes to all {files.length} tracks</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="space-y-1">
                        <label htmlFor="bulk-artist" className="block text-sm font-medium text-text-secondary">Artist (Bulk)</label>
                        <input id="bulk-artist" type="text" name="artist" value={bulkMetadata.artist} onChange={handleBulkChange} className="glass-input" placeholder="Artist Name" title="Collective Artist Name" />
                    </div>
                    <div className="space-y-1">
                        <label htmlFor="bulk-album" className="block text-sm font-medium text-text-secondary">Album (Bulk)</label>
                        <input id="bulk-album" type="text" name="album" value={bulkMetadata.album} onChange={handleBulkChange} className="glass-input" placeholder="Album Title" title="Collective Album Title" />
                    </div>
                    <div className="space-y-1">
                        <label htmlFor="bulk-publisher" className="block text-sm font-medium text-text-secondary">Publisher (Bulk)</label>
                        <input id="bulk-publisher" type="text" name="publisher" value={bulkMetadata.publisher} onChange={handleBulkChange} className="glass-input" placeholder="Publisher Entity" title="Music Publisher" />
                    </div>
                    <div className="space-y-1">
                        <label htmlFor="bulk-composer" className="block text-sm font-medium text-text-secondary">Composer (Bulk)</label>
                        <input id="bulk-composer" type="text" name="composer" value={bulkMetadata.composer} onChange={handleBulkChange} className="glass-input" placeholder="Composer Names" title="Musical Composers" />
                    </div>
                    <div className="space-y-1">
                        <label htmlFor="bulk-contact" className="block text-sm font-medium text-text-secondary">Contact Name</label>
                        <input id="bulk-contact" type="text" name="contactName" value={bulkMetadata.contactName} onChange={handleBulkChange} className="glass-input" placeholder="Contact Person" title="Point of Contact" />
                    </div>
                    <div className="flex items-center gap-6 mt-6">
                        <label className="flex items-center gap-2 cursor-pointer group">
                            <div className="relative flex items-center justify-center w-5 h-5 rounded border border-white/20 group-hover:border-accent-blue transition-colors bg-black/20">
                                <input type="checkbox" name="oneStop" checked={bulkMetadata.oneStop} onChange={handleBulkChange} className="opacity-0 absolute" />
                                {bulkMetadata.oneStop && <CheckCircle2 className="text-accent-blue w-4 h-4" />}
                            </div>
                            <span className="text-sm font-medium text-white group-hover:text-accent-blue transition-colors">One-Stop</span>
                        </label>
                    </div>
                </div>
            </div>

            <div className="space-y-4">
                <h3 className="text-xl font-semibold px-2">Individual Tracks</h3>
                {files.map((file) => {
                    const trackData = tracks[file.fileId!];
                    if (!trackData) return null;

                    return (
                        <div key={file.fileId} className="glass-panel p-6 border-white/5 bg-white/5 hover:bg-white/[0.07] transition-colors">
                            <div className="flex flex-col lg:flex-row gap-6">
                                <div className="lg:w-1/3">
                                    <div className="mb-4">
                                        <div className="min-w-0 mb-3">
                                            <input
                                                type="text"
                                                value={trackData.title}
                                                onChange={(e) => handleTrackChange(file.fileId!, 'title', e.target.value)}
                                                className="bg-transparent border-none p-0 text-xl font-bold focus:ring-0 w-full placeholder:opacity-50 text-gradient-accent"
                                                placeholder="Track Title"
                                                title="Track Title"
                                            />
                                            <p className="text-[10px] text-text-secondary truncate opacity-60 uppercase tracking-tighter">ID: {file.fileId}</p>
                                        </div>

                                        {file.audioBuffer && (
                                            <SpotCheckWaveform
                                                audioBuffer={file.audioBuffer}
                                                onPlayStateChange={(playing) => {
                                                    if (playing) onPlayBuffer?.(file.audioBuffer!);
                                                    else onPlayBuffer?.(null);
                                                }}
                                            />
                                        )}
                                    </div>
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-[10px] uppercase tracking-wider text-text-secondary">BPM</label>
                                            <input
                                                type="text"
                                                value={trackData.bpm}
                                                onChange={(e) => handleTrackChange(file.fileId!, 'bpm', e.target.value)}
                                                className="glass-input py-1 text-sm border-accent-cyan/20"
                                                title="Beats Per Minute"
                                                placeholder="BPM"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] uppercase tracking-wider text-text-secondary">Key</label>
                                            <input
                                                type="text"
                                                value={trackData.key}
                                                onChange={(e) => handleTrackChange(file.fileId!, 'key', e.target.value)}
                                                className="glass-input py-1 text-sm border-accent-cyan/20 text-accent-cyan font-bold"
                                                title="Musical Key"
                                                placeholder="Key"
                                            />
                                        </div>
                                    </div>
                                </div>

                                <div className="lg:w-2/3 grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-[10px] uppercase tracking-wider text-text-secondary">Moods</label>
                                        <input
                                            type="text"
                                            value={trackData.mood}
                                            onChange={(e) => handleTrackChange(file.fileId!, 'mood', e.target.value)}
                                            className="glass-input py-1 text-sm"
                                            title="Mood Tags"
                                            placeholder="e.g. Energetic"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] uppercase tracking-wider text-text-secondary">Genre</label>
                                        <input
                                            type="text"
                                            value={trackData.genre}
                                            onChange={(e) => handleTrackChange(file.fileId!, 'genre', e.target.value)}
                                            className="glass-input py-1 text-sm"
                                            title="Genre Tags"
                                            placeholder="e.g. Cinematic"
                                        />
                                    </div>
                                    <div className="md:col-span-2">
                                        <label className="text-[10px] uppercase tracking-wider text-text-secondary">Instruments</label>
                                        <input
                                            type="text"
                                            value={trackData.instruments}
                                            onChange={(e) => handleTrackChange(file.fileId!, 'instruments', e.target.value)}
                                            className="glass-input py-1 text-sm"
                                            title="Instrumentation"
                                            placeholder="e.g. Strings, Synth"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="sticky bottom-8 z-50 px-4">
                <div className="max-w-4xl mx-auto glass-panel p-4 flex justify-between items-center shadow-2xl border-white/10">
                    <div className="flex items-center gap-4 text-sm text-text-secondary">
                        <CheckCircle2 className="text-green-400" size={20} />
                        <span>Ready to embed {files.length} tracks</span>
                    </div>
                    <button
                        onClick={handleSubmit}
                        disabled={isProcessing}
                        className="glass-button primary min-w-[200px]"
                    >
                        {isProcessing ? (
                            <div className="flex items-center gap-2">
                                <div className="w-5 h-5 rounded-full border-2 border-white/20 border-t-white animate-spin"></div>
                                Embedding All...
                            </div>
                        ) : (
                            <>
                                <Save size={18} />
                                Embed & Batch Process
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
