#!/usr/bin/env node
'use strict'
/**
 * remotion_render.js — ai-video-maker 動畫頁面渲染工具
 *
 * CLI: node remotion_render.js --tsx <path> --audio <path> --output <path>
 *              [--fps 30] [--crf 23] [--concurrency 4] [--width 1920] [--height 1080]
 *
 * 流程:
 *   1. 以 webpack alias 將 SLIDE_COMPONENT → 使用者的 slide_NN.tsx
 *   2. @remotion/bundler bundle 整個 remotion/src/SlideEntry.tsx
 *   3. @remotion/renderer renderMedia → 無聲 MP4（避免 AAC corrupted bitstream）
 *   4. FFmpeg 混入 MP3 音訊 → 最終 segment_NN.mp4
 *
 * 需求:
 *   remotion/ 目錄已完成 npm install（node_modules/@remotion 存在）
 */

const path = require('path')
const fs = require('fs')
const fsp = require('fs/promises')
const { spawn } = require('child_process')
const crypto = require('crypto')

const REMOTION_DIR = path.join(__dirname, 'remotion')
const REMOTION_NM  = path.join(REMOTION_DIR, 'node_modules')
const SLIDE_ENTRY  = path.join(REMOTION_DIR, 'src', 'SlideEntry.tsx')

// ── 安裝確認 ──────────────────────────────────────────────────────────

function checkInstalled() {
  const marker = path.join(REMOTION_NM, '@remotion', 'renderer', 'package.json')
  if (!fs.existsSync(marker)) {
    console.error('[remotion_render] 錯誤: Remotion 尚未安裝。')
    console.error(`請執行: cd "${REMOTION_DIR}" && npm install`)
    process.exit(1)
  }
}

// ── 工具函式 ──────────────────────────────────────────────────────────

function rRequire(pkg) {
  try { return require(path.join(REMOTION_NM, pkg)) }
  catch { return require(pkg) }
}

function contentHash(str) {
  return crypto.createHash('md5').update(str).digest('hex').slice(0, 8)
}

function getAudioDuration(audioPath) {
  return new Promise((resolve) => {
    const proc = spawn('ffprobe', [
      '-v', 'error', '-show_entries', 'format=duration',
      '-of', 'csv=p=0', audioPath,
    ], { stdio: ['ignore', 'pipe', 'pipe'] })
    let out = ''
    proc.stdout.on('data', d => { out += d })
    proc.on('close', () => resolve(parseFloat(out.trim()) || 5))
    proc.on('error', () => resolve(5))
  })
}

async function mixAudio(videoPath, audioPath, outputPath) {
  await new Promise((resolve, reject) => {
    const proc = spawn('ffmpeg', [
      '-y', '-i', videoPath, '-i', audioPath,
      '-map', '0:v', '-map', '1:a',
      '-c:v', 'copy',
      '-c:a', 'aac', '-b:a', '192k', '-ar', '44100', '-ac', '2',
      '-shortest', outputPath,
    ], { stdio: ['ignore', 'pipe', 'pipe'] })
    let stderr = ''
    proc.stderr.on('data', d => { stderr += d })
    proc.on('error', reject)
    proc.on('close', code => {
      if (code !== 0) reject(new Error(`FFmpeg mixAudio 失敗:\n${stderr.slice(-400)}`))
      else resolve()
    })
  })
}

// ── Bundle（per-TSX 內容快取）─────────────────────────────────────────

const _bundleCache = new Map()

async function getBundleForSlide(tsxPath) {
  const code = await fsp.readFile(tsxPath, 'utf8')
  const cacheKey = `${tsxPath}:${contentHash(code)}`

  const cached = _bundleCache.get(cacheKey)
  if (cached && fs.existsSync(path.join(cached, 'index.html'))) {
    console.log('[remotion_render] 使用 bundle 快取')
    return cached
  }

  console.log('[remotion_render] 打包元件...')
  const { bundle } = rRequire('@remotion/bundler')

  const location = await bundle({
    entryPoint: SLIDE_ENTRY,
    webpackOverride: (config) => ({
      ...config,
      resolve: {
        ...config.resolve,
        alias: {
          ...(config.resolve?.alias || {}),
          'SLIDE_COMPONENT': tsxPath,
        },
        modules: [
          ...((config.resolve?.modules) || ['node_modules']),
          REMOTION_NM,
        ],
      },
    }),
  })

  _bundleCache.set(cacheKey, location)
  console.log('[remotion_render] 打包完成')
  return location
}

// ── 引數解析 ──────────────────────────────────────────────────────────

function parseArgs() {
  const args = process.argv.slice(2)
  const result = { fps: 30, crf: 23, concurrency: 4, width: 1920, height: 1080 }
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--tsx':         result.tsx         = args[++i]; break
      case '--audio':       result.audio       = args[++i]; break
      case '--output':      result.output      = args[++i]; break
      case '--fps':         result.fps         = parseInt(args[++i]); break
      case '--crf':         result.crf         = parseInt(args[++i]); break
      case '--concurrency': result.concurrency = parseInt(args[++i]); break
      case '--width':       result.width       = parseInt(args[++i]); break
      case '--height':      result.height      = parseInt(args[++i]); break
    }
  }
  if (!result.tsx || !result.output) {
    console.error('Usage: node remotion_render.js --tsx <path> --audio <path> --output <path>')
    console.error('  [--fps 30] [--crf 23] [--concurrency 4] [--width 1920] [--height 1080]')
    process.exit(1)
  }
  return result
}

// ── 主流程 ────────────────────────────────────────────────────────────

async function main() {
  checkInstalled()
  const { tsx, audio, output, fps, crf, concurrency, width, height } = parseArgs()

  const tsxPath    = path.resolve(tsx)
  const outputPath = path.resolve(output)

  if (!fs.existsSync(tsxPath)) {
    console.error(`[remotion_render] 找不到 TSX 檔案: ${tsxPath}`)
    process.exit(1)
  }

  // 取得音訊時長
  let durationSec = 5
  let audioPath   = ''
  if (audio) {
    const resolved = path.resolve(audio)
    if (fs.existsSync(resolved)) {
      audioPath   = resolved
      durationSec = await getAudioDuration(audioPath)
    } else {
      console.warn(`[remotion_render] 找不到音訊: ${resolved}，使用預設 5 秒`)
    }
  }

  const durationFrames = Math.ceil(durationSec * fps) + 1  // +1 幀安全邊距
  console.log(`[remotion_render] ${path.basename(tsxPath)}: ${durationSec.toFixed(1)}s → ${durationFrames} 幀 (@${fps}fps)`)

  // Bundle
  const serveUrl = await getBundleForSlide(tsxPath)

  // Remotion selectComposition + renderMedia（無聲，音訊由 FFmpeg 混入）
  const { selectComposition, renderMedia } = rRequire('@remotion/renderer')
  const inputProps = { audioPath: '', durationFrames, fps, width, height }

  const composition = await selectComposition({
    serveUrl,
    id: 'SlideAnimation',
    inputProps,
    chromiumOptions: { disableWebSecurity: true },
  })

  const tmpPath = outputPath.replace(/\.mp4$/, '_remotion_tmp.mp4')
  let lastPct = -1

  console.log('[remotion_render] 開始渲染...')
  await renderMedia({
    composition,
    serveUrl,
    codec: 'h264',
    outputLocation: tmpPath,
    inputProps,
    crf,
    concurrency,
    chromiumOptions: { disableWebSecurity: true },
    onProgress: ({ progress }) => {
      const pct = Math.floor((progress ?? 0) * 100)
      if (pct !== lastPct && pct % 20 === 0) {
        console.log(`[remotion_render] 渲染 ${pct}%`)
        lastPct = pct
      }
    },
  })

  // 混入音訊
  if (audioPath) {
    console.log('[remotion_render] 混入音訊...')
    await mixAudio(tmpPath, audioPath, outputPath)
    await fsp.unlink(tmpPath).catch(() => {})
  } else {
    await fsp.rename(tmpPath, outputPath)
  }

  console.log(`[remotion_render] 完成: ${path.basename(outputPath)}`)
}

main().catch(err => {
  console.error('[remotion_render] 渲染失敗:', err.message || err)
  process.exit(1)
})
