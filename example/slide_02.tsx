/**
 * slide_02.tsx — Remotion 動畫投影片範例
 *
 * 這個 component 會被 remotion_render.js 渲染成 segment_02.mp4。
 * 效果：標題從下方淡入 → 條列點逐一飛入
 *
 * 可用的 Remotion hooks：
 *   useCurrentFrame()   → 當前幀號（從 0 開始）
 *   useVideoConfig()    → { fps, durationInFrames, width, height }
 *   interpolate(value, inputRange, outputRange, options)
 *   spring({ frame, fps, config, durationInFrames })
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

interface Props {
  audioPath: string
  durationFrames: number
  fps: number
  width?: number
  height?: number
}

const Slide: React.FC<Props> = () => {
  const frame = useCurrentFrame()
  const { fps } = useVideoConfig()

  // 標題：前 20 幀從下方淡入
  const titleProgress = spring({
    frame,
    fps,
    config: { damping: 200, stiffness: 120, mass: 0.5 },
    durationInFrames: 20,
  })
  const titleY = interpolate(titleProgress, [0, 1], [60, 0])

  // 條列點：每隔 12 幀飛入一個
  const bulletOpacities = BULLETS.map((_, i) => {
    const startFrame = 20 + i * 12
    return spring({
      frame: Math.max(0, frame - startFrame),
      fps,
      config: { damping: 180, stiffness: 100, mass: 0.6 },
      durationInFrames: 18,
    })
  })

  return (
    <AbsoluteFill style={styles.container}>
      {/* 背景裝飾圓 */}
      <div style={styles.bgCircle} />

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
                opacity: bulletOpacities[i],
                transform: `translateX(${interpolate(bulletOpacities[i], [0, 1], [-40, 0])}px)`,
              }}
            >
              {text}
            </li>
          ))}
        </ul>
      </div>

      {/* 底部強調線 */}
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

// ── Styles ────────────────────────────────────────────────────────────

const styles = {
  container: {
    background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%)',
    fontFamily: '"Noto Sans TC", "PingFang TC", system-ui, -apple-system, sans-serif',
    color: '#e2e8f0',
    overflow: 'hidden',
    position: 'relative' as const,
  },
  bgCircle: {
    position: 'absolute' as const,
    top: -200,
    right: -200,
    width: 600,
    height: 600,
    borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)',
    pointerEvents: 'none' as const,
  },
  pageNum: {
    position: 'absolute' as const,
    top: 48,
    right: 72,
    fontSize: 28,
    fontWeight: 700,
    color: 'rgba(99,102,241,0.6)',
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
    marginBottom: 48,
    color: '#f1f5f9',
    letterSpacing: '-0.02em',
  },
  list: {
    paddingLeft: 56,
    margin: 0,
  },
  bullet: {
    fontSize: 40,
    lineHeight: 1.6,
    marginBottom: 20,
    color: '#e2e8f0',
  },
  bottomLine: {
    position: 'absolute' as const,
    bottom: 0,
    left: 0,
    right: 0,
    height: 6,
    background: 'linear-gradient(90deg, #6366f1, #818cf8, #6366f1)',
    transformOrigin: 'left center',
  },
} as const
