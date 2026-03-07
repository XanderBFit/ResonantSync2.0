import { useState, useEffect } from 'react';
import { Download, FileText, CheckCircle2, RotateCcw, Search } from 'lucide-react';

interface TagScannerProps {
    fileId: string;
    downloadUrl: string;
    oneSheetUrl: string;
    onReset: () => void;
}

export function TagScanner({ fileId, downloadUrl, oneSheetUrl, onReset }: TagScannerProps) {
    const [tags, setTags] = useState<Record<string, string>>({});
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchTags = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/tags/${fileId}`);
                if (res.ok) {
                    const data = await res.json();
                    setTags(data);
                }
            } catch (err) {
                console.error("Failed to fetch tags", err);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTags();
    }, [fileId]);

    return (
        <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-success/20 flex items-center justify-center text-success shrink-0">
                    <CheckCircle2 size={24} />
                </div>
                <div>
                    <h2 className="text-xl font-semibold text-text-primary">Mastering Complete</h2>
                    <p className="text-sm text-text-secondary">Your track has been analyzed and embedded with DISCO-compliant ID3v2 tags.</p>
                </div>
            </div>

            <div className="glass-panel p-6">
                <div className="flex items-center gap-2 mb-4">
                    <Search size={20} className="text-brand-primary" />
                    <h3 className="text-lg font-medium text-text-primary">Verified ID3 Output</h3>
                </div>

                {isLoading ? (
                    <div className="text-center py-6 text-text-secondary">Scanning embedded tags...</div>
                ) : (
                    <div className="bg-black/20 rounded-lg p-4 max-h-64 overflow-y-auto space-y-2 border border-white/5 font-mono text-sm shadow-inner">
                        {Object.entries(tags).length > 0 ? (
                            Object.entries(tags).map(([key, value]) => (
                                <div key={key} className="flex gap-4">
                                    <span className="text-brand-light font-bold min-w-[120px]">{key}</span>
                                    <span className="text-text-secondary break-words flex-1">{value}</span>
                                </div>
                            ))
                        ) : (
                            <div className="text-center text-text-secondary">No ID3 tags found.</div>
                        )}
                    </div>
                )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 pt-4 border-t border-white/5">
                <a
                    href={downloadUrl}
                    download
                    className="flex-1 btn-primary flex items-center justify-center gap-2 group text-white"
                >
                    <Download size={20} className="group-hover:-translate-y-1 transition-transform" />
                    Download MP3 (RTag)
                </a>

                <a
                    href={oneSheetUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="flex-1 btn-secondary flex items-center justify-center gap-2 group text-white hover:text-white"
                >
                    <FileText size={20} className="group-hover:-translate-y-1 transition-transform" />
                    View One-Sheet
                </a>
            </div>

            <div className="text-center mt-6">
                <button
                    onClick={onReset}
                    className="text-text-secondary hover:text-white transition-colors flex items-center gap-1 mx-auto"
                >
                    <RotateCcw size={16} />
                    Process Another Track
                </button>
            </div>
        </div>
    );
}
