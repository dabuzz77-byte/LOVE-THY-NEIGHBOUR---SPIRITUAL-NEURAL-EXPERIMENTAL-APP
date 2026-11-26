"""Self-contained canvas preview for the generated 7.83 Hz matrix carrier.

The unified Tk application is implemented in sovereign_engine.py. This small
HTML preview has no CDN or network dependencies and makes no system-sensor
claims because browser canvas code cannot read operating-system telemetry.
"""

html_content = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Hydrogen Atom · Matrix Preview</title>
<style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#050b13;color:#e9f5ff;font:13px Consolas,monospace}
canvas{display:block;width:100%;height:100%}
.hud{position:absolute;left:18px;top:16px;padding:12px 15px;border:1px solid #18344b;background:#07101be8;line-height:1.7}
.accent{color:#42e8ff}
</style>
</head>
<body>
<canvas id="matrix"></canvas>
<div class="hud">HYDROGEN ATOM · VISUAL PREVIEW<br><span class="accent">SOFTWARE CARRIER</span> · 7.83 Hz<br><span id="phase">PHASE · —</span><br>Canvas preview · no system telemetry</div>
<script>
const canvas=document.getElementById('matrix'),ctx=canvas.getContext('2d'),phaseLabel=document.getElementById('phase');
let width=0,height=0,particles=[];
function resize(){const dpr=Math.min(devicePixelRatio||1,2);width=innerWidth;height=innerHeight;canvas.width=width*dpr;canvas.height=height*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);particles=Array.from({length:100},()=>({a:Math.random()*Math.PI*2,r:.15+Math.random()*.36,s:.15+Math.random()*.45,z:.6+Math.random()*1.8}));}
function frame(now){requestAnimationFrame(frame);const t=now/1000,phase=2*Math.PI*7.83*t,s=Math.sin(phase),cx=width*.5,cy=height*.57,scale=Math.min(width,height);
ctx.fillStyle='#050b13';ctx.fillRect(0,0,width,height);
for(let x=12;x<width;x+=28)for(let y=12;y<height;y+=28){const dx=x-cx,dy=y-cy,d=Math.hypot(dx,dy)+1,w=Math.sin(phase+d*.035)*7;ctx.fillStyle=`rgba(66,232,255,${Math.max(.06,.42-d/Math.max(width,height))})`;ctx.fillRect(x+dx/d*w,y+dy/d*w,2,2);}
for(let k=0;k<3;k++){const r=scale*(.14+k*.045)+Math.sin(phase+k)*4;ctx.beginPath();ctx.arc(cx,cy,r,0,Math.PI*2);ctx.strokeStyle=k?'#18344b':'#42e8ff';ctx.lineWidth=k?1:2;ctx.stroke();}
ctx.beginPath();ctx.arc(cx,cy,7,0,Math.PI*2);ctx.fillStyle='#e9f5ff';ctx.fill();
for(const p of particles){p.a+=p.s*.002;const r=scale*p.r,x=cx+Math.cos(p.a+phase*.01)*r,y=cy+Math.sin(p.a+phase*.01)*r*.55;ctx.beginPath();ctx.arc(x,y,p.z,0,Math.PI*2);ctx.fillStyle='#42e8ff';ctx.fill();}
const wrappedPhase=((phase%(2*Math.PI))+2*Math.PI)%(2*Math.PI);phaseLabel.textContent=`PHASE · ${wrappedPhase.toFixed(2)} rad`;
}
addEventListener('resize',resize);resize();requestAnimationFrame(frame);
</script>
</body>
</html>"""
