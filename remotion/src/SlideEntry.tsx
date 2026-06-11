// remotion/src/SlideEntry.tsx
// Per-slide render entry point.
// 'SLIDE_COMPONENT' is a webpack alias injected by remotion_render.js during bundling.
import React from 'react'
import {Composition, registerRoot} from 'remotion'
import SlideComponent from 'SLIDE_COMPONENT'

interface SlideProps {
  audioPath: string
  durationFrames: number
  fps: number
  width?: number
  height?: number
}

const SlideRoot: React.FC = () => (
  <Composition
    id="SlideAnimation"
    component={SlideComponent}
    durationInFrames={300}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={{
      audioPath: '',
      durationFrames: 300,
      fps: 30,
      width: 1920,
      height: 1080,
    } as SlideProps}
    calculateMetadata={({props}) => ({
      durationInFrames: Math.max((props as SlideProps).durationFrames || 300, 1),
      fps: (props as SlideProps).fps || 30,
      width: (props as SlideProps).width || 1920,
      height: (props as SlideProps).height || 1080,
    })}
  />
)

registerRoot(SlideRoot)
