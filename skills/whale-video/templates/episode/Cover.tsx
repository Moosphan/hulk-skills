import React from "react";
import { AbsoluteFill, Img, staticFile, useVideoConfig, useCurrentFrame } from "remotion";
import { Backdrop } from "./ui";
const SER='"Songti SC",serif'; const SANS='"PingFang SC",sans-serif';
export const Cover:React.FC<{day:string;l1:string;l2:string;sub:string;chibi:string;compliance?:string}> = ({day,l1,l2,sub,chibi,compliance="含 AI 生成内容 · 非官方二创"})=>{
  const {width,height}=useVideoConfig(); const f=useCurrentFrame(); const s=width/1920;
  return <AbsoluteFill style={{overflow:"hidden"}}>
    <Backdrop/>
    <Img src={staticFile(chibi)} style={{position:"absolute",right:-20*s,bottom:-60*s,height:height*1.12}}/>
    <div style={{position:"absolute",left:96*s,top:97*s}}>
      <div style={{display:"flex",gap:18*s,alignItems:"center"}}>
        <span style={{background:"#7C5CE0",color:"#fff",fontFamily:SANS,fontSize:26*s,fontWeight:600,padding:`${5*s}px ${14*s}px`,borderRadius:5*s}}>{day}</span>
        <span style={{border:"2px solid #fff",color:"#fff",fontFamily:SANS,fontSize:26*s,fontWeight:600,padding:`${5*s}px ${14*s}px`,borderRadius:5*s}}>打工日记</span>
      </div>
      <div style={{fontFamily:SER,fontSize:180*s,fontWeight:900,color:"#FAF7F0",marginTop:26*s,lineHeight:1.16}}>{l1}</div>
      <div style={{marginTop:30*s}}><span style={{background:"#E2584A",color:"#fff",fontFamily:SER,fontSize:180*s,fontWeight:900,padding:`${14*s}px ${26*s}px`}}>{l2}</span></div>
      <div style={{fontFamily:SANS,fontSize:58*s,fontWeight:600,color:"#E2E7F2",marginTop:34*s}}>{sub}</div>
    </div>
    <div style={{position:"absolute",right:96*s,top:54*s,background:"rgba(3,6,12,.72)",padding:`${8*s}px ${16*s}px`,borderRadius:8*s,fontFamily:SANS,fontSize:26*s,color:"#CED4E0"}}>{compliance}</div>
  </AbsoluteFill>;
};
