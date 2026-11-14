
import { useEffect, useRef } from "react";
import { reportIntegrityEvent } from "../api/security";

const VALID_EVENTS = [
  "TAB_SWITCH",
  "FULLSCREEN_EXIT",
  "COPY_PASTE",
];

const LOCAL_COOLDOWN_MS = 3000;

export default function useExamIntegrity(
  attemptId,
  enabled,
  onFrozen
) {
  const onFrozenRef = useRef(onFrozen);

  useEffect(() => {
    onFrozenRef.current = onFrozen;
  }, [onFrozen]);

  useEffect(() => {
    if (!enabled || !attemptId) return undefined;

    let disposed = false;
    let wasFullscreen = Boolean(document.fullscreenElement);
    const lastSent = new Map();

    async function report(type) {
      if (!VALID_EVENTS.includes(type)) return;

      const now = Date.now();
      const previous = lastSent.get(type) || 0;

      // Avoid duplicate browser notifications.
      if (now - previous < LOCAL_COOLDOWN_MS) return;
      lastSent.set(type, now);

      try {
        const response = await reportIntegrityEvent(
          attemptId,
          type
        );

        if (!disposed && response?.frozen) {
          onFrozenRef.current?.(type);
        }
      } catch (error) {
        if (!disposed) {
          console.warn(
            "Integrity event could not be reported:",
            error.message
          );
        }
      }
    }

    function handleVisibility() {
      if (document.visibilityState === "hidden") {
        report("TAB_SWITCH");
      }
    }

    function handleBlur() {
      // Fallback for switching away while page is visible.
      if (document.visibilityState === "visible") {
        report("TAB_SWITCH");
      }
    }

    function handleFullscreen() {
      const isFullscreen = Boolean(
        document.fullscreenElement
      );

      if (wasFullscreen && !isFullscreen) {
        report("FULLSCREEN_EXIT");
      }

      wasFullscreen = isFullscreen;
    }

    function handleClipboard() {
      report("COPY_PASTE");
    }

    document.addEventListener(
      "visibilitychange",
      handleVisibility
    );
    window.addEventListener("blur", handleBlur);
    document.addEventListener(
      "fullscreenchange",
      handleFullscreen
    );
    document.addEventListener("copy", handleClipboard);
    document.addEventListener("paste", handleClipboard);

    return () => {
      disposed = true;
      document.removeEventListener(
        "visibilitychange",
        handleVisibility
      );
      window.removeEventListener("blur", handleBlur);
      document.removeEventListener(
        "fullscreenchange",
        handleFullscreen
      );
      document.removeEventListener(
        "copy",
        handleClipboard
      );
      document.removeEventListener(
        "paste",
        handleClipboard
      );
    };
  }, [attemptId, enabled]);
}
