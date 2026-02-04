"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";

export function InstallPrompt() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
      setShow(true);
    };

    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === "accepted") {
      setDeferredPrompt(null);
      setShow(false);
    }
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-5 fade-in duration-500">
      <div className="bg-card border border-border rounded-xl shadow-lg p-4 max-w-sm flex items-center gap-4">
        <div className="bg-primary/10 p-2 rounded-lg">
          <span className="text-2xl">📱</span>
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-sm">Install App</h3>
          <p className="text-xs text-muted-foreground">
            Install WaitTime Canada for easier access.
          </p>
        </div>
        <div className="flex gap-2">
           <button
            onClick={() => setShow(false)}
            className="text-xs text-muted-foreground hover:text-foreground px-2"
          >
            Later
          </button>
          <button
            onClick={handleInstall}
            className="px-3 py-1.5 bg-primary text-primary-foreground text-xs font-medium rounded-md hover:bg-primary/90 transition-colors"
          >
            Install
          </button>
        </div>
      </div>
    </div>
  );
}
