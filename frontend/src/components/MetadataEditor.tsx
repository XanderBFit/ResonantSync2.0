import { useState } from 'react';
import { Download, FileText, CheckCircle2, Music, User, Mail, Tag, Activity } from 'lucide-react';

export interface AnalyzedData {
    title: string;
    artist: string;
    album: string;
    bpm: number;
    key: string;
    mood: string;
    genre: string;
    energy: string | number;
    valence: number;
    danceability: number;
    instruments: string[];
    vocalPresence: string;
    fileId?: string;
}

export interface MetadataEditorProps {
    initialData: AnalyzedData | null;
    onSave: (data: any) => void;
    onDownloadOneSheet: () => void;
    isProcessing: boolean;
}

export function MetadataEditor({ initialData, onSave, onDownloadOneSheet, isProcessing }: MetadataEditorProps) {
    const [formData, setFormData] = useState({
        title: initialData?.title || '',
        artist: initialData?.artist || '',
        album: initialData?.album || '',
        genre: initialData?.genre || '',
        bpm: initialData?.bpm?.toString() || '',
        key: initialData?.key || '',
        mood: initialData?.mood || '',
        energy: initialData?.energy?.toString() || '',
        valence: initialData?.valence?.toString() || '',
        danceability: initialData?.danceability?.toString() || '',
        instruments: initialData?.instruments?.join(', ') || '',
        vocalPresence: initialData?.vocalPresence || '',

        // DISCO Specific
        grouping: '',
        comments: '', // Where sync terms often go
        composer: '',
        publisher: '', // Declared One-Stop Publishing
        isrc: '',
        contactName: '',
        contactEmail: '',
        contactPhone: '',
        oneStop: false,
        explicit: false,
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value, type } = e.target as HTMLInputElement;
        const checked = (e.target as HTMLInputElement).checked;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSave(formData);
    };

    return (
        <div className="glass-panel p-8 w-full max-w-4xl mx-auto animate-fade-in relative overflow-hidden">

            {/* Decorative top bar */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-accent-cyan via-accent-blue to-accent-purple" />

            <div className="flex justify-between items-center mb-8">
                <div>
                    <h2 className="text-3xl font-bold mb-2">Track Editor</h2>
                    <p className="text-text-secondary">Verify AI analysis and complete DISCO metadata</p>
                </div>
                <button
                    type="button"
                    onClick={onDownloadOneSheet}
                    className="glass-button text-accent-purple border-accent-purple/30 hover:border-accent-purple/60 hover:bg-accent-purple/5"
                >
                    <FileText size={18} />
                    Export One-Sheet
                </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">

                {/* SECTION: AI Extracted / Core Audio */}
                <section className="p-6 bg-white/5 rounded-2xl border border-white/5">
                    <div className="flex items-center gap-2 mb-4 text-accent-cyan">
                        <Activity size={20} />
                        <h3 className="text-xl font-semibold">AI Analysis & Core</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Title</label>
                            <input type="text" name="title" value={formData.title} onChange={handleChange} className="glass-input" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Artist</label>
                            <input type="text" name="artist" value={formData.artist} onChange={handleChange} className="glass-input" required />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Album / EP</label>
                            <input type="text" name="album" value={formData.album} onChange={handleChange} className="glass-input" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Genre</label>
                            <input type="text" name="genre" value={formData.genre} onChange={handleChange} className="glass-input" />
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">BPM</label>
                                <div className="relative">
                                    <input type="number" name="bpm" value={formData.bpm} onChange={handleChange} className="glass-input pl-8" />
                                    <Music className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-accent-cyan w-4 h-4 opacity-70" />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Key</label>
                                <input type="text" name="key" value={formData.key} onChange={handleChange} className="glass-input border-accent-cyan/30 bg-accent-cyan/5 text-accent-cyan font-semibold" />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Mood</label>
                            <input type="text" name="mood" value={formData.mood} onChange={handleChange} className="glass-input" placeholder="e.g. Uplifting, Dark, Energetic" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Instruments</label>
                            <input type="text" name="instruments" value={formData.instruments} onChange={handleChange} className="glass-input" placeholder="e.g. Synth, 808, Electric Guitar" />
                        </div>
                        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Energy</label>
                                <input type="text" name="energy" value={formData.energy} onChange={handleChange} className="glass-input" placeholder="0.85" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Valence</label>
                                <input type="number" step="0.01" name="valence" value={formData.valence} onChange={handleChange} className="glass-input" placeholder="0.45" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Danceability</label>
                                <input type="number" step="0.01" name="danceability" value={formData.danceability} onChange={handleChange} className="glass-input" placeholder="0.9" />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Vocal</label>
                                <input type="text" name="vocalPresence" value={formData.vocalPresence} onChange={handleChange} className="glass-input" placeholder="Instrumental" />
                            </div>
                        </div>
                    </div>
                </section>

                {/* SECTION: DISCO & Sync */}
                <section className="p-6 bg-white/5 rounded-2xl border border-white/5">
                    <div className="flex items-center gap-2 mb-4 text-accent-blue">
                        <Tag size={20} />
                        <h3 className="text-xl font-semibold">Sync & Publishing (DISCO)</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Composer(s)</label>
                            <input type="text" name="composer" value={formData.composer} onChange={handleChange} className="glass-input" placeholder="Writers splits..." />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Publisher</label>
                            <input type="text" name="publisher" value={formData.publisher} onChange={handleChange} className="glass-input" placeholder="Publishing entities..." />
                        </div>
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-text-secondary mb-1">Grouping / Tags</label>
                            <input type="text" name="grouping" value={formData.grouping} onChange={handleChange} className="glass-input" placeholder="e.g. For Fans Of, Similar Artists..." />
                        </div>
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-text-secondary mb-1">Comments (Sync Terms & Story)</label>
                            <textarea name="comments" value={formData.comments} onChange={handleChange} rows={3} className="glass-input resize-none" placeholder="Add descriptions, sync notable placements, or 'One-Stop' info here..."></textarea>
                        </div>
                    </div>

                    <div className="flex items-center gap-6">
                        <label className="flex items-center gap-2 cursor-pointer group">
                            <div className="relative flex items-center justify-center w-5 h-5 rounded border border-white/20 group-hover:border-accent-blue transition-colors bg-black/20">
                                <input type="checkbox" name="oneStop" checked={formData.oneStop} onChange={handleChange} className="opacity-0 absolute" />
                                {formData.oneStop && <CheckCircle2 className="text-accent-blue w-4 h-4" />}
                            </div>
                            <span className="text-sm font-medium text-white group-hover:text-accent-blue transition-colors">Declared One-Stop</span>
                        </label>

                        <label className="flex items-center gap-2 cursor-pointer group">
                            <div className="relative flex items-center justify-center w-5 h-5 rounded border border-white/20 group-hover:border-red-400 transition-colors bg-black/20">
                                <input type="checkbox" name="explicit" checked={formData.explicit} onChange={handleChange} className="opacity-0 absolute" />
                                {formData.explicit && <CheckCircle2 className="text-red-400 w-4 h-4" />}
                            </div>
                            <span className="text-sm font-medium text-white group-hover:text-red-400 transition-colors">Explicit Content</span>
                        </label>
                    </div>
                </section>

                {/* SECTION: Contact Details */}
                <section className="p-6 bg-white/5 rounded-2xl border border-white/5">
                    <div className="flex items-center gap-2 mb-4 text-accent-purple">
                        <User size={20} />
                        <h3 className="text-xl font-semibold">Contact Information</h3>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Name</label>
                            <div className="relative">
                                <input type="text" name="contactName" value={formData.contactName} onChange={handleChange} className="glass-input pl-9" placeholder="Rep Name" />
                                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-4 h-4 opacity-50" />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Email</label>
                            <div className="relative">
                                <input type="email" name="contactEmail" value={formData.contactEmail} onChange={handleChange} className="glass-input pl-9" placeholder="email@agency.com" />
                                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary w-4 h-4 opacity-50" />
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Phone</label>
                            <input type="tel" name="contactPhone" value={formData.contactPhone} onChange={handleChange} className="glass-input" placeholder="+1 (555) 000-0000" />
                        </div>
                    </div>
                </section>

                {/* Form Actions */}
                <div className="pt-6 border-t border-white/10 flex justify-end gap-4">
                    <button type="button" className="glass-button text-text-secondary hover:text-white">
                        Cancel
                    </button>
                    <button type="submit" disabled={isProcessing} className="glass-button primary min-w-[200px]">
                        {isProcessing ? (
                            <>
                                <div className="w-5 h-5 rounded-full border-2 border-white/20 border-t-white animate-spin"></div>
                                Processing MP3...
                            </>
                        ) : (
                            <>
                                <Download size={18} />
                                Embed Tags & Download MP3
                            </>
                        )}
                    </button>
                </div>

            </form>
        </div>
    );
}
