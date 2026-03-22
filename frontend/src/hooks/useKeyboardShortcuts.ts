import { useEffect } from "react";

interface KeyboardShortcutsOptions {
  onTogglePlay: () => void;
  onVolumeUp: () => void;
  onVolumeDown: () => void;
  onMute: () => void;
  onSelectChannel: (index: number) => void;
}

export function useKeyboardShortcuts({
  onTogglePlay,
  onVolumeUp,
  onVolumeDown,
  onMute,
  onSelectChannel,
}: KeyboardShortcutsOptions) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Skip when typing in inputs/textareas
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      switch (e.key) {
        case " ":
          e.preventDefault();
          onTogglePlay();
          break;
        case "ArrowUp":
          e.preventDefault();
          onVolumeUp();
          break;
        case "ArrowDown":
          e.preventDefault();
          onVolumeDown();
          break;
        case "m":
        case "M":
          onMute();
          break;
        case "1":
        case "2":
        case "3":
        case "4":
        case "5":
        case "6":
        case "7":
        case "8":
        case "9":
          onSelectChannel(parseInt(e.key) - 1);
          break;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onTogglePlay, onVolumeUp, onVolumeDown, onMute, onSelectChannel]);
}
