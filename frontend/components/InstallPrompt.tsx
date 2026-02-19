"use client";

import { useEffect, useState } from "react";
import { clsx } from "clsx";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string }>;
}

export function InstallPrompt() {
  const [deferredPrompt, setDeferredPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [show, setShow] = useState(false);

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
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
            Install Wait Time Canada for easier access.
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
