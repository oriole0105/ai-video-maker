// Type declaration for the SLIDE_COMPONENT webpack alias.
// The actual file is user's slide_NN.tsx, injected by remotion_render.js at bundle time.
declare module 'SLIDE_COMPONENT' {
  import React from 'react'
  const component: React.FC<{
    audioPath: string
    durationFrames: number
    fps: number
    width?: number
    height?: number
  }>
  export default component
}
