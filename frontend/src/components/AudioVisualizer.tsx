import { useEffect, useRef } from "react";

interface Props {
  audioRef: React.RefObject<HTMLAudioElement | null>;
  isPlaying: boolean;
  channelSlug: string | null;
}

type AudioContextConstructor = new (options?: AudioContextOptions) => AudioContext;

function getAudioContext(): AudioContextConstructor {
  const win = window as Window & {
    AudioContext?: AudioContextConstructor;
    webkitAudioContext?: AudioContextConstructor;
  };
  if (win.AudioContext) return win.AudioContext;
  if (win.webkitAudioContext) return win.webkitAudioContext;
  throw new Error("AudioContext not supported");
}

function getChannelColors(slug: string | null): [string, string] {
  if (!slug) return ["#6366f1", "#818cf8"];
  if (slug.includes("lofi") || slug.includes("lo-fi")) return ["#7c3aed", "#a855f7"];
  if (slug.includes("anime")) return ["#ec4899", "#f472b6"];
  if (slug.includes("jazz")) return ["#d97706", "#fbbf24"];
  if (slug.includes("game")) return ["#059669", "#34d399"];
  return ["#6366f1", "#818cf8"];
}

// Track AudioContext per audio element to avoid "already connected" errors
const sourceNodeMap = new WeakMap<HTMLAudioElement, MediaElementAudioSourceNode>();
const audioContextMap = new WeakMap<HTMLAudioElement, AudioContext>();

export function AudioVisualizer({ audioRef, isPlaying, channelSlug }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number | null>(null);
  const dataArrayRef = useRef<Uint8Array<ArrayBuffer> | null>(null);
  const stopAnimRef = useRef(false);

  // Set up AudioContext and AnalyserNode
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    let AudioCtx: AudioContextConstructor;
    try {
      AudioCtx = getAudioContext();
    } catch {
      return;
    }

    // Reuse or create context
    let ctx = audioContextMap.get(audio);
    if (!ctx || ctx.state === "closed") {
      ctx = new AudioCtx();
      audioContextMap.set(audio, ctx);
    }

    // Reuse or create source node (can only create one per audio element)
    let source = sourceNodeMap.get(audio);
    if (!source) {
      audio.crossOrigin = "anonymous";
      source = ctx.createMediaElementSource(audio);
      sourceNodeMap.set(audio, source);
    }

    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    analyser.smoothingTimeConstant = 0.8;
    source.connect(analyser);
    analyser.connect(ctx.destination);

    const bufferLength = analyser.frequencyBinCount;
    dataArrayRef.current = new Uint8Array(bufferLength) as Uint8Array<ArrayBuffer>;
    analyserRef.current = analyser;

    return () => {
      // Do not close ctx here — reused across re-renders
      analyser.disconnect();
    };
  }, [audioRef]);

  // Animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    const analyser = analyserRef.current;
    const dataArray = dataArrayRef.current;

    if (!canvas || !analyser || !dataArray) return;

    const ctx2d = canvas.getContext("2d");
    if (!ctx2d) return;

    stopAnimRef.current = false;

    const [colorFrom, colorTo] = getChannelColors(channelSlug);
    const BAR_COUNT = 64;

    const draw = () => {
      if (stopAnimRef.current) return;

      rafRef.current = requestAnimationFrame(draw);

      const W = canvas.width;
      const H = canvas.height;

      ctx2d.clearRect(0, 0, W, H);

      if (!isPlaying) {
        return;
      }

      analyser.getByteFrequencyData(dataArray);

      // Sample BAR_COUNT evenly from the frequency data
      const step = Math.floor(dataArray.length / BAR_COUNT);
      const barWidth = (W / BAR_COUNT) * 0.7;
      const gap = (W / BAR_COUNT) * 0.3;
      const centerY = H / 2;

      for (let i = 0; i < BAR_COUNT; i++) {
        const value = dataArray[i * step] / 255;
        const barH = value * centerY * 0.9;
        const x = i * (barWidth + gap);

        // Gradient for bar
        const grad = ctx2d.createLinearGradient(0, centerY - barH, 0, centerY);
        grad.addColorStop(0, colorTo);
        grad.addColorStop(1, colorFrom);

        // Glow
        ctx2d.shadowBlur = 15;
        ctx2d.shadowColor = colorTo;
        ctx2d.globalAlpha = parseFloat(
          getComputedStyle(document.documentElement)
            .getPropertyValue("--viz-glow-opacity")
            .trim() || "0.6"
        );

        // Upper bar
        ctx2d.fillStyle = grad;
        ctx2d.fillRect(x, centerY - barH, barWidth, barH);

        // Mirror (lower)
        ctx2d.save();
        ctx2d.shadowBlur = 0;
        ctx2d.globalAlpha = parseFloat(
          getComputedStyle(document.documentElement)
            .getPropertyValue("--viz-mirror-opacity")
            .trim() || "0.3"
        );
        ctx2d.fillStyle = grad;
        ctx2d.fillRect(x, centerY, barWidth, barH);
        ctx2d.restore();
      }

      // Reset
      ctx2d.globalAlpha = 1;
      ctx2d.shadowBlur = 0;

      // Center line
      ctx2d.fillStyle = "rgba(255, 255, 255, 0.15)";
      ctx2d.fillRect(0, centerY - 0.5, W, 1);
    };

    draw();

    return () => {
      stopAnimRef.current = true;
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      // Clear canvas on stop
      const c = canvasRef.current;
      if (c) {
        const c2d = c.getContext("2d");
        c2d?.clearRect(0, 0, c.width, c.height);
      }
    };
  }, [isPlaying, channelSlug]);

  // Resize canvas to match display size
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const observer = new ResizeObserver(() => {
      canvas.width = canvas.offsetWidth;
      canvas.height = canvas.offsetHeight;
    });
    observer.observe(canvas);
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    return () => observer.disconnect();
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="viz-canvas"
      role="img"
      aria-label="オーディオビジュアライザー"
    />
  );
}
