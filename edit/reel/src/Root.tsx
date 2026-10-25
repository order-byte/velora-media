import React from "react";
import { Composition } from "remotion";
import { Reel } from "./Reel";
import { Reel4 } from "./Reel4";
import { Final, FINAL_DUR } from "./Final";
import { DURATION, FPS } from "./lib";

export const Root: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
    <Composition id="Final" component={Final} durationInFrames={Math.round(FINAL_DUR * 30)} fps={30} width={1080} height={1920} />
    <Composition id="Reel4" component={Reel4} durationInFrames={DURATION} fps={FPS} width={1080} height={1920} />
  </>
);
