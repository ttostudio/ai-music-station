interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="glass-card p-6 max-w-md w-full mx-4 space-y-4 slide-up">
        <h3 className="text-lg font-bold text-white">{title}</h3>
        <p style={{ color: 'var(--text-secondary)' }}>{message}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all"
          >
            キャンセル
          </button>
          <button
            onClick={onConfirm}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white hover:from-red-400 hover:to-red-500 transition-all shadow-lg shadow-red-500/25"
          >
            削除
          </button>
        </div>
      </div>
    </div>
  );
}
