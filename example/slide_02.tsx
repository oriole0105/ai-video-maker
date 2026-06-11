/**
 * slide_02.tsx — Remotion 動畫投影片範例（warm-amber 主題）
 *
 * 效果：標題淡入 → 四個條列點依旁白時長比例逐一飛入
 *
 * 重點設計原則：
 *   - 顏色必須與 slides.md 的 theme 一致（warm-amber）
 *   - 動畫觸發點以 durationFrames 的比例計算，而非絕對幀號
 *     → 條列點在旁白進行到 20%、38%、56%、74% 時出現
 *     → 無論旁白長短，動畫都自然分散在整個時長裡
 */
import React from 'react'
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion'

const BULLETS = [
  '要錄教學影片，但對著麥克風說話說不順',
  '投影片改了一頁，整部影片要重新錄過',
  '環境有雜音，錄出來效果差強人意',
  '時間成本高：準備 + 錄製 + 剪輯，動輒半天',
]

// 每個條列點在整個時長中的出現時機（比例值 0~1）
const BULLET_CUES = [0.20, 0.38, 0.56, 0.74]

interface Props {
  audioPath: string
  durationFrames: number
  fps: number
  width?: number
  height?: number
}

const Slide: React.FC<Props> = ({ durationFrames }) => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  // 標題：開場前 20 幀 spring 進場
  const titleProgress = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 120, mass: 0.5 },
    durationInFrames: 20,
  })
  const titleY = interpolate(titleProgress, [0, 1], [50, 0])

  // 條列點：依比例觸發，spread 動畫到整個 durationFrames
  const bulletProgress = BULLET_CUES.map((cue) => {
    const startFrame = Math.round(durationFrames * cue)
    return spring({
      frame: Math.max(0, frame - startFrame),
      fps,
      config: { damping: 180, stiffness: 90, mass: 0.6 },
      durationInFrames: 20,
    })
  })

  return (
    <AbsoluteFill style={styles.container}>
      {/* 右上角暖色裝飾光暈 */}
      <div style={styles.bgGlow} />

      {/* 頁碼 */}
      <div style={styles.pageNum}>02</div>

      {/* 主要內容 */}
      <div style={styles.content}>
        <h1
          style={{
            ...styles.title,
            opacity: titleProgress,
            transform: `translateY(${titleY}px)`,
          }}
        >
          你有沒有這樣的困擾？
        </h1>

        <ul style={styles.list}>
          {BULLETS.map((text, i) => (
            <li
              key={i}
              style={{
                ...styles.bullet,
                opacity: bulletProgress[i],
                transform: `translateX(${interpolate(bulletProgress[i], [0, 1], [-40, 0])}px)`,
              }}
            >
              {text}
            </li>
          ))}
        </ul>
      </div>

      {/* 底部琥珀強調線，跟著標題一起展開 */}
      <div
        style={{
          ...styles.bottomLine,
          transform: `scaleX(${titleProgress})`,
        }}
      />
    </AbsoluteFill>
  )
}

export default Slide

// ── Styles（warm-amber 主題色）────────────────────────────────────────
// 對照 themes/warm-amber.css：
//   背景  #1c1208 → #2d1f0a
//   文字  #f0e6d3
//   強調  #f59e0b（琥珀）
//   副標  #fcd34d
// ─────────────────────────────────────────────────────────────────────

const styles = {
  container: {
    background: 'linear-gradient(160deg, #1c1208 0%, #2d1f0a 100%)',
    fontFamily: '"Noto Sans TC", "PingFang TC", system-ui, -apple-system, sans-serif',
    color: '#f0e6d3',
    overflow: 'hidden',
    position: 'relative' as const,
  },
  bgGlow: {
    position: 'absolute' as const,
    top: -150,
    right: -150,
    width: 500,
    height: 500,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(245,158,11,0.12) 0%, transparent 70%)',
    pointerEvents: 'none' as const,
  },
  pageNum: {
    position: 'absolute' as const,
    top: 48,
    right: 72,
    fontSize: 28,
    fontWeight: 700,
    color: 'rgba(245,158,11,0.5)',
    letterSpacing: '0.1em',
  },
  content: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    padding: '80px 120px',
    paddingTop: 100,
  },
  title: {
    fontSize: 72,
    fontWeight: 700,
    lineHeight: 1.25,
    marginBottom: 16,
    paddingBottom: 16,
    color: '#f59e0b',
    borderBottom: '2px solid #f59e0b',
    letterSpacing: '-0.01em',
  },
  list: {
    paddingLeft: 48,
    marginTop: 32,
  },
  bullet: {
    fontSize: 40,
    lineHeight: 1.7,
    marginBottom: 16,
    color: '#f0e6d3',
  },
  bottomLine: {
    position: 'absolute' as const,
    bottom: 0,
    left: 0,
    right: 0,
    height: 5,
    background: 'linear-gradient(90deg, #f59e0b, #fcd34d, #f59e0b)',
    transformOrigin: 'left center',
  },
} as const
