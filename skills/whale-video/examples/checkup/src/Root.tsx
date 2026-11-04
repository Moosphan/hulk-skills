import React from "react";
import { Composition } from "remotion";
import { Checkup } from "./Checkup";
import TL from "../public/data/checkup_timeline.json";

const total = (TL as any).total as number;

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Checkup"
    component={Checkup}
    durationInFrames={Math.round(total * 30)}
    fps={30}
    width={1920}
    height={1080}
  />
);
