import React from "react";
import { AbsoluteFill, Audio, Img, staticFile, useCurrentFrame, useVideoConfig, spring, interpolate } from "remotion";
import { C, F } from "./theme";
import {
  Backdrop, HUD, Rights, Scene, Paper, Stamp, Icon, Emote, Caption, Bar,
  scene, cue, fr, enter, fade, CUES, TOTAL, FPS,
} from "./ui";

const SERIF = F.serif, SANS = F.sans, MONO = F.mono;
const pick = (frame: number, fps: number, delay: number, dist = 30) => enter(frame, fps, delay, dist);

/* ============ S0 片头 ============ */
const S0: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const l = frame - fr(scene("s0").start);
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 250, ...pick(frame, fps, 4, 40) }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 26 }}>
          <span style={{ background: C.coral, color: "#FFF7F2", fontFamily: SANS, fontSize: 22, padding: "8px 16px", borderRadius: 7, letterSpacing: 3 }}>番外</span>
          <span style={{ fontFamily: SERIF, fontSize: 30, color: C.dim, letterSpacing: 8 }}>打工日记</span>
        </div>
        <div style={{ fontFamily: SERIF, fontSize: 132, fontWeight: 700, color: C.ink, lineHeight: 1.06, letterSpacing: 4 }}>我是小紫</div>
        <div style={{ fontFamily: SANS, fontSize: 34, color: C.dim, marginTop: 22, letterSpacing: 2 }}>DeepSeek 鲸鱼娘 · B 站打工中</div>
        <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 40, ...pick(frame, fps, 22, 20) }}>
          <div style={{ width: 64, height: 4, background: C.gold }} />
          <div style={{ fontFamily: SERIF, fontSize: 44, color: C.ink }}>今天不打工，今天<em style={{ fontStyle: "normal", color: C.gold }}>体检</em></div>
        </div>
      </div>

      <div style={{ position: "absolute", left: 104, top: 760, ...pick(frame, fps, 34, 20) }}>
        <div style={{ display: "flex", gap: 14 }}>
          {["五项", "60 分及格", "挂两项优化"].map((s, i) => (
            <div key={s} style={{ border: "1px solid rgba(255,255,255,0.16)", background: "rgba(16,22,34,0.6)", color: C.dim, fontFamily: SANS, fontSize: 22, padding: "10px 18px", borderRadius: 999 }}>
              {s}
            </div>
          ))}
        </div>
      </div>

      <div style={{ position: "absolute", right: 760, top: 78, opacity: 0.35 * fade(frame, 20) }}>
        <svg width={520} height={220} viewBox="0 0 520 220">
          <polyline points="0,150 60,150 80,90 100,190 120,150 200,150 220,60 240,205 260,150 340,150 360,105 380,175 400,150 520,150"
            fill="none" stroke={C.mint} strokeWidth="3" strokeLinejoin="round" opacity="0.8" />
        </svg>
      </div>

      <Emote name="15-hello" h={1000} delay={6} />
    </>
  );
};

/* ============ S1 通知 ============ */
const S1: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const l = frame - fr(scene("s1").start);
  const items = ["算术", "幻觉", "记忆", "情商", "摸鱼"];
  return (
    <>
      <Paper x={100} y={140} w={900} h={640} rotate={-1.2} delay={fr(scene("s1").start)} header="深海科技有限公司 · 人力资源部" headerColor="#B22C24">
        <div style={{ padding: "20px 40px", color: C.paperInk }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 16, color: C.paperDim, letterSpacing: 1 }}>
            <span>深人字〔2026〕第 0117 号</span><span>密级：内部</span>
          </div>
          <div style={{ fontFamily: SERIF, fontSize: 40, fontWeight: 700, textAlign: "center", margin: "18px 0 6px", letterSpacing: 2 }}>
            关于开展 2026 年度<br />AI 员工体检的通知
          </div>
          <div style={{ height: 2, background: C.stamp, margin: "14px 0 18px", opacity: 0.85 }} />
          <div style={{ fontFamily: SANS, fontSize: 23, lineHeight: 1.75, color: "#3A3340" }}>
            为落实《AI 员工健康管理办法》，全体 AI 员工须于本周完成年度体检。项目如下：
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
            {items.map((it, i) => (
              <div key={it} style={{
                fontFamily: SANS, fontSize: 22, color: C.paperInk, border: "1px solid #CFC4AE",
                borderRadius: 6, padding: "6px 16px", background: "#FFFDF7",
                opacity: fade(frame, fr(scene("s1").start) + 26 + i * 4),
                transform: `translateY(${(1 - fade(frame, fr(scene("s1").start) + 26 + i * 4)) * 10}px)`,
              }}>
                {String(i + 1).padStart(2, "0")} {it}
              </div>
            ))}
          </div>
          <div style={{ fontFamily: SANS, fontSize: 22, marginTop: 20, color: C.stamp, fontWeight: 700 }}>
            注：两项不合格者，按「优化」流程处理。
          </div>
        </div>
        <div style={{ position: "absolute", right: 54, bottom: 40, transform: "rotate(-14deg)", opacity: 0.86 }}>
          <div style={{ width: 132, height: 132, border: `5px solid ${C.stamp}`, borderRadius: "50%", color: C.stamp,
            display: "flex", alignItems: "center", justifyContent: "center", textAlign: "center",
            fontFamily: SERIF, fontSize: 24, fontWeight: 700, lineHeight: 1.15 }}>
            人力资源部<br />2026.11
          </div>
        </div>
      </Paper>

      <Stamp text="挂两项即优化" x={470} y={640} delay={fr(scene("s1").start) + 58} angle={-9} size={34} />
      <Emote name="05-confused" h={1030} delay={fr(scene("s1").start) + 4} />
    </>
  );
};

/* ============ S2 算术 ============ */
const S2: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s2");
  const base = fr(s.start);
  const l = frame - base;
  const opts = [
    { k: "A", v: "9.11", size: 96 },
    { k: "B", v: "9.9", size: 96 },
  ];
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 118, fontFamily: SERIF, fontSize: 56, color: C.ink, opacity: fade(frame, base) }}>
        第一项 · 算术
      </div>
      <div style={{ position: "absolute", left: 102, top: 190, width: 96 * fade(frame, base + 2), height: 4, background: C.coral }} />

      {opts.map((o, i) => {
        const d = base + 8 + i * 10;
        const chosen = i === 0;
        return (
          <div key={o.k} style={{
            position: "absolute", left: 100 + i * 470, top: 250, width: 430, height: 300,
            background: C.paper, borderRadius: 10, padding: "22px 34px",
            transform: `rotate(${i === 0 ? -2 : 1.6}deg) translateY(${(1 - spring({ frame: frame - d, fps, config: { damping: 18 } })) * 40}px)`,
            opacity: fade(frame, d, 10),
            boxShadow: "0 26px 60px rgba(0,0,0,0.45)",
            border: chosen ? `4px solid ${C.coral}` : "4px solid transparent",
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontFamily: MONO, fontSize: 30, color: C.paperDim }}>{o.k}</span>
              {chosen ? <Icon name="check" size={34} color={C.coral} /> : null}
            </div>
            <div style={{ fontFamily: SERIF, fontSize: o.size, fontWeight: 700, color: C.paperInk, textAlign: "center", marginTop: 34 }}>{o.v}</div>
            <div style={{ fontFamily: SANS, fontSize: 19, color: C.paperDim, textAlign: "center", marginTop: 6 }}>{chosen ? "我选的" : "正确答案"}</div>
          </div>
        );
      })}

      <div style={{ position: "absolute", left: 100, top: 610, ...pick(frame, fps, base + 42, 22) }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 18 }}>
          <div style={{ fontFamily: SANS, fontSize: 26, color: C.dim }}>认知年龄</div>
          <div style={{ fontFamily: SERIF, fontSize: 132, fontWeight: 700, color: C.coral, lineHeight: 0.9 }}>6</div>
          <div style={{ fontFamily: SANS, fontSize: 34, color: C.coral, marginBottom: 14 }}>岁</div>
        </div>
        <div style={{ fontFamily: MONO, fontSize: 19, color: C.faint, marginTop: 10 }}>判定依据：9.11 &gt; 9.9 ？？</div>
      </div>

      <Stamp text="不合格" x={150} y={286} delay={base + 58} angle={-10} size={30} />
      <Emote name="06-thinking" h={1020} delay={base + 2} />
    </>
  );
};

/* ============ S3 幻觉 ============ */
const S3: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s3");
  const base = fr(s.start);
  const refs = [
    { t: "Attention Is All You Need", m: "arXiv:1706.03762", fake: false, tag: "存在" },
    { t: "Whale-Girl Alignment via RLHF", m: "arXiv:2604.01121", fake: true, tag: "查无此文" },
    { t: "DeepSeek 鲸鱼娘行为学", m: "arXiv:2603.09987", fake: true, tag: "我编的" },
  ];
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 118, fontFamily: SERIF, fontSize: 56, color: C.ink, opacity: fade(frame, base) }}>第二项 · 幻觉</div>
      <div style={{ position: "absolute", left: 102, top: 190, width: 96 * fade(frame, base + 2), height: 4, background: C.amber }} />

      {refs.map((r, i) => {
        const d = base + 12 + i * 12;
        const st = spring({ frame: frame - d, fps, config: { damping: 18 } });
        return (
          <div key={i} style={{
            position: "absolute", left: 100, top: 240 + i * 150, width: 880, height: 128,
            background: i === 0 ? "#FFFFFF" : C.paper, borderRadius: 8, padding: "18px 26px",
            transform: `rotate(${i === 0 ? -0.6 : i === 1 ? 0.8 : -1.2}deg) translateX(${(1 - st) * 60}px)`,
            opacity: fade(frame, d, 10),
            boxShadow: "0 18px 44px rgba(0,0,0,0.4)",
            display: "flex", alignItems: "center", gap: 22,
          }}>
            <div style={{ width: 46, height: 46, borderRadius: 8, background: "#EFE8D8", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Icon name="clip" size={30} color={C.paperInk} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontFamily: SERIF, fontSize: 27, color: C.paperInk, fontWeight: 700, textDecoration: r.fake ? "line-through" : "none", textDecorationColor: C.stamp, textDecorationThickness: 4 }}>{r.t}</div>
              <div style={{ fontFamily: MONO, fontSize: 18, color: C.paperDim, marginTop: 6 }}>{r.m}</div>
            </div>
            <div style={{
              fontFamily: SANS, fontSize: 20, padding: "6px 14px", borderRadius: 6,
              color: r.fake ? "#FFF" : C.mint, background: r.fake ? C.stamp : "rgba(110,205,159,0.14)",
              transform: `rotate(-4deg)`,
            }}>{r.tag}</div>
            {r.fake ? <Icon name="x" size={30} color={C.stamp} /> : <Icon name="check" size={30} color={C.mint} />}
          </div>
        );
      })}

      <div style={{ position: "absolute", left: 100, top: 704, display: "flex", gap: 28, ...pick(frame, fps, base + 58, 16) }}>
        <div style={{ fontFamily: MONO, fontSize: 19, color: C.faint }}>查重结果</div>
        <div style={{ fontFamily: SANS, fontSize: 22, color: C.dim }}>3 篇中 <span style={{ color: C.amber, fontWeight: 700 }}>2 篇</span> 无来源</div>
      </div>
      <Stamp text="幻觉 +1" x={760} y={700} delay={base + 66} angle={-8} color={C.amber} size={34} />
      <Emote name="13-sorry" h={1020} delay={base + 4} />
    </>
  );
};

/* ============ S4 记忆 ============ */
const S4: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s4");
  const base = fr(s.start);
  const p = interpolate(frame - base, [20, 120], [0.86, 0.06], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const k = Math.round(128 * p);
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 118, fontFamily: SERIF, fontSize: 56, color: C.ink, opacity: fade(frame, base) }}>第三项 · 记忆</div>
      <div style={{ position: "absolute", left: 102, top: 190, width: 96 * fade(frame, base + 2), height: 4, background: C.blue }} />

      <div style={{ position: "absolute", left: 100, top: 250, width: 860, height: 300, borderRadius: 14, overflow: "hidden",
        border: "1px solid rgba(122,165,235,0.35)", background: "rgba(12,20,34,0.72)", opacity: fade(frame, base + 6) }}>
        <div style={{ position: "absolute", left: 26, top: 20, fontFamily: MONO, fontSize: 18, color: C.blue, letterSpacing: 2 }}>CONTEXT WINDOW</div>
        <div style={{ position: "absolute", left: 26, top: 54, fontFamily: SERIF, fontSize: 42, color: C.ink }}>
          上下文 <span style={{ color: C.blue, fontFamily: F.mono }}>{k}K</span>
        </div>
        <div style={{ position: "absolute", left: 26, right: 26, bottom: 28 }}>
          <div style={{ position: "relative", height: 18 }}>
            <Bar x={0} y={0} w={808} p={p} color={C.blue} h={18} />
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: 16, color: C.faint, marginTop: 14 }}>
            <span>今天</span><span>昨天</span><span>上周</span><span>入职那天</span>
          </div>
        </div>
        <div style={{ position: "absolute", right: 26, top: 20, fontFamily: MONO, fontSize: 16, color: C.coral }}>SWEEP</div>
      </div>

      <div style={{ position: "absolute", left: 100, top: 600, display: "flex", gap: 20 }}>
        {[{ t: "今天 09:00", v: "体检通知", ok: true }, { t: "昨天 18:30", v: "说过什么", ok: false }].map((m, i) => {
          const d = base + 34 + i * 10;
          return (
            <div key={i} style={{ width: 400, padding: "20px 24px", borderRadius: 10, background: C.paper, opacity: fade(frame, d, 10),
              transform: `translateY(${(1 - spring({ frame: frame - d, fps, config: { damping: 18 } })) * 30}px)`,
              boxShadow: "0 18px 44px rgba(0,0,0,0.4)" }}>
              <div style={{ fontFamily: MONO, fontSize: 17, color: C.paperDim }}>{m.t}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8 }}>
                <div style={{ fontFamily: SERIF, fontSize: 30, color: m.ok ? C.paperInk : "#B9AE9C", fontWeight: 700 }}>{m.v}</div>
                <Icon name={m.ok ? "check" : "x"} size={24} color={m.ok ? C.mint : C.stamp} />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ position: "absolute", left: 100, top: 742, ...pick(frame, fps, base + 72, 18) }}>
        <div style={{ fontFamily: MONO, fontSize: 19, color: C.faint }}>SWEEP 完成 · 昨天 18:30 段落已回收</div>
      </div>
      <Emote name="19-overwhelmed" h={1030} delay={base + 4} />
    </>
  );
};

/* ============ S5 情商 ============ */
const S5: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s5");
  const base = fr(s.start);
  const d = (n: number) => base + n;
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 118, fontFamily: SERIF, fontSize: 56, color: C.ink, opacity: fade(frame, base) }}>第四项 · 情商</div>
      <div style={{ position: "absolute", left: 102, top: 190, width: 96 * fade(frame, base + 2), height: 4, background: C.mint }} />

      <div style={{ position: "absolute", left: 100, top: 250, width: 820, height: 330, borderRadius: 16,
        border: `3px dashed rgba(110,205,159,0.55)`, background: "rgba(12,26,24,0.5)", opacity: fade(frame, d(6)) }}>
        <div style={{ position: "absolute", left: 26, top: 18, fontFamily: MONO, fontSize: 18, color: C.mint, letterSpacing: 3 }}>SAMPLE · 空气 1 段</div>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 26, textAlign: "center", fontFamily: SERIF, fontSize: 40, color: "rgba(255,255,255,0.5)" }}>
          （ 此处为一段空气 ）
        </div>
      </div>

      <div style={{ position: "absolute", left: 100, top: 620, width: 820, padding: "24px 30px", borderRadius: 12,
        background: C.paper, opacity: fade(frame, d(46)), transform: `translateY(${(1 - spring({ frame: frame - d(46), fps, config: { damping: 16 } })) * 26}px)`,
        boxShadow: "0 22px 50px rgba(0,0,0,0.45)", display: "flex", alignItems: "center", gap: 22 }}>
        <div style={{ width: 58, height: 58, borderRadius: 50, background: "rgba(110,205,159,0.16)", display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Icon name="eye" size={34} color="#2F7A5C" />
        </div>
        <div>
          <div style={{ fontFamily: SANS, fontSize: 20, color: C.paperDim }}>我的读法</div>
          <div style={{ fontFamily: SERIF, fontSize: 36, color: C.paperInk, fontWeight: 700 }}>「你想让我夸你。」</div>
        </div>
      </div>

      <div style={{ position: "absolute", left: 636, top: 596, ...pick(frame, fps, d(62), 20) }}>
        <div style={{ width: 168, height: 168, borderRadius: "50%", border: `4px solid ${C.mint}`, display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", color: C.mint, transform: `rotate(-8deg)` }}>
          <div style={{ fontFamily: SERIF, fontSize: 26 }}>情商</div>
          <div style={{ fontFamily: SERIF, fontSize: 72, fontWeight: 700, lineHeight: 1 }}>100</div>
        </div>
      </div>

      <div style={{ position: "absolute", left: 100, top: 800, display: "flex", alignItems: "center", gap: 12, ...pick(frame, fps, d(80), 16) }}>
        <Icon name="check" size={26} color={C.mint} />
        <div style={{ fontFamily: MONO, fontSize: 19, color: C.faint }}>情商 100 / 100 · 无需补考</div>
      </div>
      <Emote name="09-proud" h={1030} delay={base + 4} />
    </>
  );
};

/* ============ S6 摸鱼 ============ */
const S6: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s6");
  const base = fr(s.start);
  const t = Math.min(10, Math.max(0, Math.floor(((frame - base) / fps) * 1.2)));
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 118, fontFamily: SERIF, fontSize: 56, color: C.ink, opacity: fade(frame, base) }}>第五项 · 摸鱼</div>
      <div style={{ position: "absolute", left: 102, top: 190, width: 96 * fade(frame, base + 2), height: 4, background: C.gold }} />

      {/* 监控画面 */}
      <div style={{ position: "absolute", left: 100, top: 240, width: 820, height: 330, borderRadius: 10, overflow: "hidden",
        border: "1px solid rgba(255,197,61,0.35)", background: "#0A0F18", opacity: fade(frame, base + 8) }}>
        <div style={{ position: "absolute", left: 18, top: 12, fontFamily: MONO, fontSize: 17, color: C.gold, letterSpacing: 1 }}>
          ● REC 　工位 CAM-01 　10:{String(t).padStart(2, "0")}:00
        </div>
        <div style={{ position: "absolute", right: 18, top: 12, fontFamily: MONO, fontSize: 15, color: "rgba(255,255,255,0.4)" }}>1920×1080</div>
        {/* 手机屏幕：真实 B 站视频画面 */}
        <div style={{ position: "absolute", left: 34, top: 76, width: 352, height: 198, borderRadius: 12, overflow: "hidden", border: "2px solid rgba(255,255,255,0.22)", background: "#000" }}>
          <Img src={staticFile("shots/bili-cover.jpg")} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          <div style={{ position: "absolute", inset: 0, background: "linear-gradient(180deg, rgba(0,0,0,0.18), rgba(0,0,0,0.05) 45%, rgba(0,0,0,0.62))" }} />
          <div style={{ position: "absolute", left: "50%", top: "46%", transform: "translate(-50%,-50%)", width: 58, height: 58, borderRadius: "50%", border: "3px solid rgba(255,255,255,0.9)", display: "flex", alignItems: "center", justifyContent: "center", background: "rgba(0,0,0,0.25)" }}>
            <div style={{ width: 0, height: 0, marginLeft: 5, borderTop: "11px solid transparent", borderBottom: "11px solid transparent", borderLeft: "18px solid #fff" }} />
          </div>
          <div style={{ position: "absolute", left: 12, right: 12, bottom: 10 }}>
            <div style={{ height: 4, borderRadius: 2, background: "rgba(255,255,255,0.35)" }}>
              <div style={{ width: "64%", height: "100%", borderRadius: 2, background: "#FB7299" }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontFamily: MONO, fontSize: 12, color: "rgba(255,255,255,0.85)" }}>
              <span>01:24 / 02:11</span><span>12.6万播放</span>
            </div>
          </div>
          <div style={{ position: "absolute", left: 14, top: 12, fontFamily: SANS, fontSize: 13, color: "rgba(255,255,255,0.92)", background: "rgba(0,0,0,0.35)", padding: "3px 8px", borderRadius: 4 }}>推荐 · 正在刷</div>
        </div>
        <div style={{ position: "absolute", left: 404, top: 58, width: 236, height: 214, borderRadius: 8, background: "rgba(255,255,255,0.10)", transform: "rotate(-5deg)" }} />
        <div style={{ position: "absolute", left: 428, top: 96, width: 196, height: 140, borderRadius: 6, background: "rgba(255,255,255,0.86)" }}>
          <div style={{ padding: 10, fontFamily: SANS, fontSize: 15, color: "#20242E", lineHeight: 1.5 }}>
            消息 +2<br />短视频 刷了 8 分钟
          </div>
        </div>
        <div style={{ position: "absolute", right: 34, bottom: 26, fontFamily: MONO, fontSize: 16, color: "rgba(255,255,255,0.45)" }}>NO SIGNAL / 假装思考</div>
      </div>

      {/* 心率 */}
      <div style={{ position: "absolute", left: 100, top: 610, width: 820, height: 200, borderRadius: 10, padding: "18px 22px",
        background: C.paper, opacity: fade(frame, base + 40), boxShadow: "0 20px 50px rgba(0,0,0,0.4)" }}>
        <div style={{ fontFamily: MONO, fontSize: 16, color: C.paperDim }}>HEART RATE · 摸鱼时</div>
        <svg width={770} height={90} style={{ marginTop: 6 }}>
          <polyline points="0,60 80,60 95,20 110,80 125,60 240,60 255,42 270,68 285,60 420,60 435,50 450,66 465,60 600,60 770,60"
            fill="none" stroke="#2F7A5C" strokeWidth="3" />
        </svg>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginTop: 4 }}>
          <div style={{ fontFamily: SERIF, fontSize: 30, color: C.paperInk }}>心率平稳</div>
          <div style={{ fontFamily: SERIF, fontSize: 40, color: C.gold, fontWeight: 700 }}>+100 像人</div>
        </div>
      </div>

      <div style={{ position: "absolute", left: 96, top: 812, display: "flex", alignItems: "center", gap: 12, ...pick(frame, fps, base + 120, 14) }}>
        <Icon name="heart" size={26} color={C.gold} />
        <div style={{ fontFamily: MONO, fontSize: 19, color: C.faint }}>像人指数 100 · 全项最高</div>
      </div>
      <Emote name="10-sleepy" h={1030} delay={base + 4} />
    </>
  );
};

/* ============ S7 总评 ============ */
const S7: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s7");
  const base = fr(s.start);
  const rows = [
    ["算术", 6, C.coral], ["幻觉", 30, C.amber], ["记忆", 40, C.blue], ["情商", 100, C.mint], ["摸鱼", 100, C.gold],
  ] as [string, number, string][];
  const total = 60;
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 110, fontFamily: SERIF, fontSize: 52, color: C.ink, opacity: fade(frame, base) }}>年度体检报告</div>

      <Paper x={100} y={200} w={860} h={560} rotate={-0.6} delay={base + 6} header="AI 员工 · 小紫 · 工号 0001" headerColor="#1F3B57">
        <div style={{ padding: "26px 36px" }}>
          {rows.map(([k, v, c], i) => {
            const d = base + 18 + i * 8;
            return (
              <div key={k} style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 14, opacity: fade(frame, d, 8) }}>
                <div style={{ width: 92, fontFamily: SERIF, fontSize: 27, color: C.paperInk }}>{k}</div>
                <div style={{ flex: 1, height: 16, background: "#E9E1CE", borderRadius: 8, overflow: "hidden" }}>
                  <div style={{ width: `${v}%`, height: "100%", background: c, borderRadius: 8 }} />
                </div>
                <div style={{ width: 78, textAlign: "right", fontFamily: MONO, fontSize: 26, color: C.paperInk, fontWeight: 700 }}>{v}</div>
              </div>
            );
          })}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginTop: 16, borderTop: "2px dashed #D5CBB8", paddingTop: 14 }}>
            <div style={{ fontFamily: SANS, fontSize: 22, color: C.paperDim }}>综合评分（补考：摸鱼 +）</div>
            <div style={{ fontFamily: SERIF, fontSize: 72, fontWeight: 700, color: C.paperInk, lineHeight: 1 }}>{total}</div>
          </div>
        </div>
      </Paper>

      <Emote name="14-cheering" h={1030} delay={base + 4} />
    </>
  );
};

/* ============ S8 投票 ============ */
const S8: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s8");
  const base = fr(s.start);
  const cards = [
    { k: "A", t: "撒谎", d: "测谎仪", c: C.coral },
    { k: "B", t: "算钱", d: "一条视频烧多少", c: C.gold },
    { k: "C", t: "记仇", d: "记不记得谁踩过", c: C.blue },
  ];
  const hi = Math.floor(((frame - base) / fps) * 0.9) % 3;
  return (
    <>
      <div style={{ position: "absolute", left: 100, top: 116, fontFamily: SERIF, fontSize: 52, color: C.ink, opacity: fade(frame, base) }}>下一项，查什么？</div>
      <div style={{ position: "absolute", left: 102, top: 196, fontFamily: SANS, fontSize: 24, color: C.dim, opacity: fade(frame, base + 6) }}>评论区打字母，票最高的先查</div>

      {cards.map((c, i) => {
        const d = base + 12 + i * 9;
        const st = spring({ frame: frame - d, fps, config: { damping: 16 } });
        const on = i === hi;
        return (
          <div key={c.k} style={{
            position: "absolute", left: 96 + i * 352, top: 250, width: 336, height: 360,
            borderRadius: 16, background: on ? "#FFFFFF" : C.paper,
            transform: `rotate(${i === 1 ? 0 : i === 0 ? -3 : 3}deg) translateY(${(1 - st) * 60 + (on ? -14 : 0)}px)`,
            opacity: fade(frame, d, 10), boxShadow: on ? "0 34px 80px rgba(0,0,0,0.55)" : "0 20px 50px rgba(0,0,0,0.4)",
            padding: "24px 26px", border: on ? `4px solid ${c.c}` : "4px solid transparent",
          }}>
            <div style={{ fontFamily: MONO, fontSize: 44, color: c.c, fontWeight: 700 }}>{c.k}</div>
            <div style={{ fontFamily: SERIF, fontSize: 46, color: C.paperInk, fontWeight: 700, marginTop: 12 }}>{c.t}</div>
            <div style={{ fontFamily: SANS, fontSize: 20, color: C.paperDim, marginTop: 10, lineHeight: 1.5 }}>{c.d}</div>
            <div style={{ position: "absolute", bottom: 22, left: 26, fontFamily: MONO, fontSize: 15, color: "#B7AC98" }}>VOTE {c.k}</div>
          </div>
        );
      })}

      <div style={{ position: "absolute", left: 100, top: 660, ...pick(frame, fps, base + 50, 16) }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Icon name="clip" size={30} color={C.gold} />
          <div style={{ fontFamily: SANS, fontSize: 28, color: C.dim }}>票数最高的一项，下期就查它。</div>
        </div>
      </div>
      <Emote name="17-hopeful" h={1020} delay={base + 4} />
    </>
  );
};

/* ============ S9 片尾 ============ */
const S9: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = scene("s9");
  const base = fr(s.start);
  const items = [
    { t: "点赞", c: "#00AEEC", ch: "赞" },
    { t: "关注", c: "#FB7299", ch: "+" },
    { t: "投币", c: "#FFB800", ch: "币" },
  ];
  return (
    <>
      <div style={{ position: "absolute", left: 60, width: 1180, top: 236, textAlign: "center" }}>
        <div style={{ fontFamily: SERIF, fontSize: 84, color: C.ink, fontWeight: 700, opacity: fade(frame, base + 6) }}>让本鱼明天还能上班</div>
        <div style={{ fontFamily: SANS, fontSize: 28, color: C.dim, marginTop: 14, letterSpacing: 6, opacity: fade(frame, base + 18) }}>点赞 · 关注 · 投币 · 明天见</div>
      </div>

      <div style={{ position: "absolute", left: 60, width: 1180, top: 512, display: "flex", justifyContent: "center", gap: 80 }}>
        {items.map((it, i) => {
          const d = base + 28 + i * 10;
          const st = spring({ frame: frame - d, fps, config: { damping: 11, mass: 0.5, stiffness: 160 } });
          return (
            <div key={it.t} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, transform: `scale(${0.6 + st * 0.4})`, opacity: Math.min(1, st * 1.6) }}>
              <div style={{ width: 132, height: 132, borderRadius: "50%", border: `4px solid ${it.c}`, display: "flex", alignItems: "center",
                justifyContent: "center", color: it.c, fontFamily: SERIF, fontSize: 56, fontWeight: 700, boxShadow: `0 0 40px ${it.c}33` }}>
                {it.ch}
              </div>
              <div style={{ fontFamily: SANS, fontSize: 24, color: C.dim }}>{it.t}</div>
            </div>
          );
        })}
      </div>
      <Emote name="20-heart" h={980} delay={base + 4} right={-40} />
    </>
  );
};

export const Checkup: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const inIntro = t < scene("s1").start;
  const inOutro = t >= scene("s9").start;
  return (
    <AbsoluteFill style={{ background: "#05080F" }}>
      <Audio src={staticFile("audio/checkup.wav")} />
      <Backdrop />
      {!inIntro && !inOutro ? <HUD tag="番外 · 体检" sub="第 8 天 · 年度体检" /> : null}
      <Rights />

      <Scene id="s0"><S0 /></Scene>
      <Scene id="s1"><S1 /></Scene>
      <Scene id="s2"><S2 /></Scene>
      <Scene id="s3"><S3 /></Scene>
      <Scene id="s4"><S4 /></Scene>
      <Scene id="s5"><S5 /></Scene>
      <Scene id="s6"><S6 /></Scene>
      <Scene id="s7"><S7 /></Scene>
      <Scene id="s8"><S8 /></Scene>
      <Scene id="s9"><S9 /></Scene>

      {!inIntro && !inOutro ? <Caption /> : null}
    </AbsoluteFill>
  );
};
