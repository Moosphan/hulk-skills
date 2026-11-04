import React from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from "remotion";
import { C, F } from "./theme";
import TL from "../public/data/checkup_timeline.json";

export const CUES = (TL as any).cues as { id: string; text: string; start: number; dur: number; scene: string }[];
export const SCENES = (TL as any).scenes as { id: string; start: number; dur: number; end: number }[];
export const TOTAL = (TL as any).total as number;
export const FPS = 30;
export const scene = (id: string) => SCENES.find((s) => s.id === id)!;
export const cue = (id: string) => CUES.find((c) => c.id === id)!;
export const fr = (t: number) => Math.round(t * FPS);

const seed = (i: number) => {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
const BUBBLES = Array.from({ length: 34 }, (_, i) => ({
  x: seed(i + 3) * 1920,
  y: seed(i + 77) * 1080,
  r: 2 + seed(i + 141) * 7,
  sp: 8 + seed(i + 211) * 26,
  wob: seed(i + 311) * 6.28,
}));

export const Backdrop: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(175deg, ${C.sea1} 0%, ${C.sea0} 62%, #03060C 100%)` }}>
      {/* 水面光柱 */}
      {[0.16, 0.42, 0.72, 0.9].map((x, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: x * 1920 - 180,
            top: -260,
            width: 360 + i * 60,
            height: 1500,
            background:
              "linear-gradient(180deg, rgba(140,190,255,0.16), rgba(140,190,255,0.03) 55%, transparent 78%)",
            filter: "blur(38px)",
            transform: `rotate(${6 + i * 2 + Math.sin(t * 0.25 + i) * 2.4}deg) translateX(${Math.sin(t * 0.18 + i * 1.7) * 26}px)`,
            mixBlendMode: "screen",
          }}
        />
      ))}
      {/* 焦散：缓慢移动的光斑 */}
      <AbsoluteFill style={{ opacity: 0.5, mixBlendMode: "screen" }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              position: "absolute",
              left: 260 + i * 520 + Math.sin(t * 0.22 + i * 2) * 60,
              top: 120 + i * 160 + Math.cos(t * 0.18 + i) * 40,
              width: 620,
              height: 300,
              borderRadius: "50%",
              background: "radial-gradient(closest-side, rgba(120,180,255,0.13), transparent 70%)",
              filter: "blur(20px)",
            }}
          />
        ))}
      </AbsoluteFill>
      {/* 气泡 */}
      {BUBBLES.map((b, i) => {
        const y = ((b.y - t * b.sp) % 1180 + 1180) % 1180 - 60;
        const x = b.x + Math.sin(t * 0.6 + b.wob) * 12;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: b.r * 2,
              height: b.r * 2,
              borderRadius: "50%",
              border: "1px solid rgba(180,215,255,0.22)",
              background: "radial-gradient(closest-side, rgba(190,220,255,0.14), transparent)",
            }}
          />
        );
      })}
      {/* 远处鲸影 */}
      <svg width={1920} height={1080} style={{ position: "absolute", opacity: 0.16 }}>
        <path
          d="M120 900 C 300 830, 470 860, 600 905 C 660 925, 700 920, 730 900 C 720 940, 680 960, 620 958 C 470 954, 300 950, 120 920 Z"
          fill="#0E2A44"
        />
        <circle cx={700} cy={905} r={9} fill="#0E2A44" />
      </svg>
      <AbsoluteFill style={{ backgroundImage: "radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px)", backgroundSize: "72px 72px", opacity: 0.5 }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px 90px rgba(0,0,0,0.62)" }} />
    </AbsoluteFill>
  );
};

export const HUD: React.FC<{ tag: string; tagColor?: string; sub: string }> = ({ tag, tagColor = C.coral, sub }) => (
  <div style={{ position: "absolute", left: 92, top: 46, display: "flex", alignItems: "center", gap: 16 }}>
    <span style={{ fontFamily: F.serif, fontSize: 27, color: C.ink, letterSpacing: 1 }}>鲸鱼娘的打工日记</span>
    <span style={{ fontFamily: F.sans, fontSize: 19, color: "#FFF6F2", background: tagColor, padding: "6px 13px", borderRadius: 7, letterSpacing: 1 }}>
      {tag}
    </span>
    <span style={{ fontFamily: F.sans, fontSize: 18, color: C.faint }}>{sub}</span>
  </div>
);

export const Rights: React.FC = () => (
  <div style={{ position: "absolute", right: 92, top: 52, fontFamily: F.sans, fontSize: 17, color: "rgba(150,140,170,0.72)" }}>
    AI 生成内容 · 非官方二创
  </div>
);

export const enter = (frame: number, fps: number, delay: number, dist = 28) => {
  const s = spring({ frame: frame - delay, fps, config: { damping: 200, mass: 0.55 } });
  return { opacity: s, transform: `translateY(${(1 - s) * dist}px)` } as React.CSSProperties;
};

export const fade = (frame: number, delay: number, dur = 12) =>
  interpolate(frame - delay, [0, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

export const Scene: React.FC<{ id: string; children: React.ReactNode; bg?: number }> = ({ id, children }) => {
  const frame = useCurrentFrame();
  const s = scene(id);
  const a = interpolate(frame, [fr(s.start) - 6, fr(s.start) + 8, fr(s.end) - 8, fr(s.end) + 2], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ opacity: a }}>{children}</AbsoluteFill>;
};

// ---------- 纸感道具 ----------
export const Paper: React.FC<{
  x: number; y: number; w: number; h?: number; rotate?: number; delay?: number;
  header?: string; headerColor?: string; children?: React.ReactNode; style?: React.CSSProperties;
}> = ({ x, y, w, h, rotate = 0, delay = 0, header, headerColor = C.paperInk, children, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 18, mass: 0.6, stiffness: 130 }, durationInFrames: 20 });
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: w,
        height: h,
        background: C.paper,
        borderRadius: 8,
        boxShadow: "0 30px 70px rgba(0,0,0,0.5), 0 2px 0 rgba(255,255,255,0.4) inset",
        transform: `rotate(${rotate}deg) translateY(${(1 - s) * 40}px) scale(${0.97 + s * 0.03})`,
        opacity: s,
        overflow: "hidden",
        ...style,
      }}
    >
      {header ? (
        <div style={{ background: headerColor, color: C.paper, padding: "14px 26px", fontFamily: F.serif, fontSize: 24, letterSpacing: 3 }}>
          {header}
        </div>
      ) : null}
      {children}
    </div>
  );
};

export const Stamp: React.FC<{ text: string; x: number; y: number; delay?: number; angle?: number; color?: string; size?: number }> = ({
  text, x, y, delay = 0, angle = -12, color = C.stamp, size = 40,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 9, mass: 0.5, stiffness: 200 }, durationInFrames: 16 });
  const sc = interpolate(s, [0, 1], [2.1, 1]);
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `rotate(${angle}deg) scale(${sc})`,
        opacity: Math.min(1, s * 1.4),
        border: `5px solid ${color}`,
        color,
        padding: "10px 22px",
        fontFamily: F.serif,
        fontSize: size,
        fontWeight: 700,
        letterSpacing: 6,
        borderRadius: 6,
        opacity: 0.94,
      }}
    >
      {text}
    </div>
  );
};

export const Icon: React.FC<{ name: "cross" | "clip" | "brain" | "heart" | "eye" | "clock" | "flask" | "check" | "x"; size?: number; color?: string }> = ({
  name, size = 40, color = C.paperInk,
}) => {
  const p: Record<string, React.ReactNode> = {
    cross: <><rect x="9" y="3" width="6" height="18" rx="1.5" /><rect x="3" y="9" width="18" height="6" rx="1.5" /></>,
    clip: <><rect x="5" y="4" width="14" height="18" rx="2.5" /><rect x="9" y="2" width="6" height="4" rx="1.5" /><path d="M9 11h6M9 15h4" stroke={color} strokeWidth="1.6" fill="none" /></>,
    brain: <path d="M9 4a3 3 0 0 0-3 3 3 3 0 0 0-1 5.6V16a3 3 0 0 0 3 3h1v-3M15 4a3 3 0 0 1 3 3 3 3 0 0 1 1 5.6V16a3 3 0 0 1-3 3h-1v-3" fill="none" stroke={color} strokeWidth="1.8" />,
    heart: <path d="M12 20s-7-4.6-7-9.2A4 4 0 0 1 12 8a4 4 0 0 1 7 2.8C19 15.4 12 20 12 20z" />,
    eye: <><path d="M2 12s3.6-6 10-6 10 6 10 6-3.6 6-10 6-10-6-10-6z" fill="none" stroke={color} strokeWidth="1.8" /><circle cx="12" cy="12" r="2.6" /></>,
    clock: <><circle cx="12" cy="12" r="9" fill="none" stroke={color} strokeWidth="1.8" /><path d="M12 7v5l3.4 2" fill="none" stroke={color} strokeWidth="1.8" strokeLinecap="round" /></>,
    flask: <path d="M10 3h4M11 3v5l-5.4 9.2A2.4 2.4 0 0 0 7.7 21h8.6a2.4 2.4 0 0 0 2.1-3.8L13 8V3" fill="none" stroke={color} strokeWidth="1.8" />,
    check: <path d="M4 12.5l5 5L20 6.5" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" />,
    x: <path d="M5 5l14 14M19 5L5 19" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" />,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ display: "block" }}>
      <g fill={color}>{p[name]}</g>
    </svg>
  );
};

export const Emote: React.FC<{ name: string; h?: number; right?: number; delay?: number; scale?: number }> = ({
  name, h = 1010, right = -30, delay = 0, scale = 1,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 17, mass: 0.8 } });
  const bob = Math.sin((frame / fps) * Math.PI * 0.8) * 9;
  return (
    <Img
      src={staticFile(`emotes/${name}.png`)}
      style={{
        position: "absolute",
        right,
        bottom: -140 + bob,
        height: h,
        transform: `translateX(${(1 - s) * 90}px) scale(${(0.94 + s * 0.06) * scale})`,
        opacity: Math.min(1, s * 1.3),
        filter: "drop-shadow(0 40px 70px rgba(0,0,0,0.55))",
      }}
    />
  );
};

export const Caption: React.FC<{ y?: number }> = ({ y = 872 }) => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const c = CUES.find((x) => t >= x.start - 0.1 && t <= x.start + x.dur + 0.22);
  if (!c) return null;
  const local = t - c.start;
  const o = Math.min(1, Math.max(0, local / 0.14)) * Math.min(1, Math.max(0, (c.dur + 0.2 - local) / 0.18));
  return (
    <div
      style={{
        position: "absolute",
        left: 30,
        width: 1360,
        top: y,
        display: "flex",
        justifyContent: "center",
        opacity: o,
        transform: `translateY(${(1 - o) * 10}px)`,
      }}
    >
      <div
        style={{
          fontFamily: F.sans,
          fontSize: 44,
          maxWidth: 1300,
          textAlign: "center",
          fontWeight: 800,
          color: "#FFFFFF",
          letterSpacing: 1,
          padding: "6px 26px",
          textShadow: "0 4px 0 rgba(0,0,0,0.55), 0 0 18px rgba(0,0,0,0.65), 2px 0 0 #10131C, -2px 0 0 #10131C, 0 2px 0 #10131C, 0 -2px 0 #10131C",
          background: "linear-gradient(180deg, rgba(8,12,20,0) 0%, rgba(8,12,20,0.55) 50%, rgba(8,12,20,0) 100%)",
        }}
      >
        {c.text}
      </div>
    </div>
  );
};

export const Bar: React.FC<{ x: number; y: number; w: number; p: number; color: string; h?: number }> = ({ x, y, w, p, color, h = 14 }) => (
  <div style={{ position: "absolute", left: x, top: y, width: w, height: h, background: "rgba(255,255,255,0.10)", borderRadius: h }}>
    <div style={{ width: `${Math.max(0, Math.min(1, p)) * 100}%`, height: "100%", background: color, borderRadius: h }} />
  </div>
);
