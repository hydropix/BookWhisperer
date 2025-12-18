import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ToastContainer, ToastProps, ToastType } from '../components/Toast';

interface ToastContextType {
  showToast: (type: ToastType, message: string, description?: string, duration?: number) => void;
  success: (message: string, description?: string) => void;
  error: (message: string, description?: string) => void;
  warning: (message: string, description?: string) => void;
  info: (message: string, description?: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastProps[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (type: ToastType, message: string, description?: string, duration?: number) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: ToastProps = {
        id,
        type,
        message,
        description,
        duration,
        onClose: removeToast,
      };

      setToasts((prev) => [...prev, newToast]);
    },
    [removeToast]
  );

  const success = useCallback(
    (message: string, description?: string) => {
      showToast('success', message, description);
    },
    [showToast]
  );

  const error = useCallback(
    (message: string, description?: string) => {
      showToast('error', message, description, 7000); // Errors stay longer
    },
    [showToast]
  );

  const warning = useCallback(
    (message: string, description?: string) => {
      showToast('warning', message, description);
    },
    [showToast]
  );

  const info = useCallback(
    (message: string, description?: string) => {
      showToast('info', message, description);
    },
    [showToast]
  );

  return (
    <ToastContext.Provider value={{ showToast, success, error, warning, info }}>
      {children}
      <ToastContainer toasts={toasts} onClose={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
}
