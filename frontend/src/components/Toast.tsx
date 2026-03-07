import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
    id: string;
    message: string;
    type: ToastType;
}

interface ToastProps {
    toasts: Toast[];
    onDismiss: (id: string) => void;
}

const icons = {
    success: <CheckCircle2 size={18} className="text-emerald-400 shrink-0" />,
    error: <XCircle size={18} className="text-red-400 shrink-0" />,
    info: <Info size={18} className="text-accent-cyan shrink-0" />,
};

const borders = {
    success: 'border-emerald-500/20',
    error: 'border-red-500/20',
    info: 'border-accent-cyan/20',
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: string) => void }) {
    useEffect(() => {
        const t = setTimeout(() => onDismiss(toast.id), 4000);
        return () => clearTimeout(t);
    }, [toast.id, onDismiss]);

    return (
        <div
            className={`flex items-center gap-3 glass-panel px-4 py-3 border ${borders[toast.type]} shadow-2xl animate-in slide-in-from-bottom-4 duration-300 min-w-[280px] max-w-sm`}
        >
            {icons[toast.type]}
            <span className="text-sm text-white flex-1">{toast.message}</span>
            <button onClick={() => onDismiss(toast.id)} aria-label="Dismiss notification" className="text-text-secondary hover:text-white ml-2 shrink-0">
                <X size={14} />
            </button>
        </div>
    );
}

export function ToastContainer({ toasts, onDismiss }: ToastProps) {
    return (
        <div className="fixed bottom-6 right-6 z-[200] flex flex-col gap-3 items-end pointer-events-none">
            {toasts.map(t => (
                <div key={t.id} className="pointer-events-auto">
                    <ToastItem toast={t} onDismiss={onDismiss} />
                </div>
            ))}
        </div>
    );
}

// Hook for easy toast usage anywhere
export function useToast() {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = (message: string, type: ToastType = 'info') => {
        const id = Math.random().toString(36).slice(2);
        setToasts(prev => [...prev, { id, message, type }]);
    };

    const dismiss = (id: string) => setToasts(prev => prev.filter(t => t.id !== id));

    return { toasts, addToast, dismiss };
}
