export type RGB = number[];
export type Quality = {area:number; cohesion:number; blur:number; clipped:number; glare:number};
export type Limits = {min_area:number; max_area:number; min_blur:number; max_clipped:number; max_glare:number; min_cohesion:number};
export type Model = {mean:number[]; scale:number[]; coefficients:number[]; intercept:number; platt_coefficient:number; platt_intercept:number; threshold:number; band:number};
export const methods = ['none','chromaticity','gray_world','white_patch','sclera','skin'] as const;
export type Method = typeof methods[number];
export const quantile = (a:number[], q:number):number => {
  const b = [...a].sort((x,y)=>x-y); if (!b.length) return NaN;
  const p=(b.length-1)*q, i=Math.floor(p); return b[i]+(b[Math.min(i+1,b.length-1)]-b[i])*(p-i);
};
const mean=(a:number[])=>a.reduce((x,y)=>x+y,0)/a.length;
export const linear=(rgb:RGB):RGB=>rgb.map(v=>{const x=v/255; return x<=0.04045?x/12.92:((x+0.055)/1.055)**2.4;});
export function lab(x:RGB):RGB {
  const xyz=[(x[0]*.4124564+x[1]*.3575761+x[2]*.1804375)/.95047,
    x[0]*.2126729+x[1]*.7151522+x[2]*.0721750,
    (x[0]*.0193339+x[1]*.1191920+x[2]*.9503041)/1.08883];
  const f=xyz.map(v=>v>(6/29)**3?Math.cbrt(v):v/(3*(6/29)**2)+4/29);
  return [116*f[1]-16,500*(f[0]-f[1]),200*(f[1]-f[2])];
}
function morph(mask:number[], n:number, erode:boolean):number[] {
  return mask.map((_,i)=>{
    const x=i%n,y=Math.floor(i/n); let sum=0;
    for(let dy=-1;dy<=1;dy++) for(let dx=-1;dx<=1;dx++)
      if(x+dx>=0&&x+dx<n&&y+dy>=0&&y+dy<n) sum+=mask[(y+dy)*n+x+dx];
    return Number(erode?sum===9:sum>0);
  });
}
export function segment(rgb:RGB[], n:number):{mask:number[]; cohesion:number} {
  const candidate=rgb.map(p=>{const c=lab(linear(p)); return Number(c[1]>12&&c[0]>20&&c[0]<90&&Math.min(...p)<245&&Math.max(...p)>30);});
  const clean=morph(morph(morph(morph(candidate,n,true),n,false),n,false),n,true);
  const seen=new Uint8Array(n*n); let largest:number[]=[];
  for(let i=0;i<clean.length;i++) {
    if(!clean[i]||seen[i]) continue;
    const queue=[i]; seen[i]=1;
    for(let at=0;at<queue.length;at++) {
      const k=queue[at], x=k%n,y=Math.floor(k/n);
      const neighbors=[...(x>0?[k-1]:[]),...(x<n-1?[k+1]:[]),...(y>0?[k-n]:[]),...(y<n-1?[k+n]:[])];
      for(const j of neighbors) if(clean[j]&&!seen[j]){seen[j]=1;queue.push(j);}
    }
    if(queue.length>largest.length) largest=queue;
  }
  const mask=Array(n*n).fill(0) as number[]; largest.forEach(i=>mask[i]=1);
  return {mask,cohesion:largest.length/Math.max(clean.reduce((a,b)=>a+b,0),1)};
}
export function normalize(x:RGB[], method:Method, n:number, references=true):RGB[]|null {
  if(method==='none') return x.map(p=>[...p]);
  if(method==='chromaticity') return x.map(p=>p.map(v=>v/Math.max(p.reduce((a,b)=>a+b,0),1e-8)));
  let ref:RGB;
  if(method==='gray_world') {
    ref=[0,1,2].map(c=>mean(x.map(p=>p[c])));
    return x.map(p=>p.map((v,c)=>Math.min(1,Math.max(0,v*mean(ref)/Math.max(ref[c],1e-8)))));
  }
  if(method==='white_patch') ref=[0,1,2].map(c=>quantile(x.map(p=>p[c]),.95));
  else {
    if(!references) return null;
    const selected=x.filter((p,i)=>{
      const [l,a,b]=lab(p);
      if(method==='sclera') return l>65&&l<95&&Math.abs(a)<8&&Math.abs(b)<15;
      const xx=i%n, yy=Math.floor(i/n), edge=xx<n*.2||xx>=n*.8||yy<n*.2||yy>=n*.8;
      return edge&&l>30&&l<85&&a>3&&a<20&&b>8&&b<35;
    });
    if(selected.length<n*n*.01) return null;
    ref=[0,1,2].map(c=>quantile(selected.map(p=>p[c]),.5));
  }
  return x.map(p=>p.map((v,c)=>Math.min(1,Math.max(0,v/Math.max(ref[c],1e-8)))));
}
export function features(x:RGB[],mask:number[]):number[] {
  const roi=x.filter((_,i)=>mask[i]); if(!roi.length) return Array(10).fill(NaN) as number[];
  const colors=roi.map(lab), out:number[]=[];
  for(let c=0;c<3;c++){const v=colors.map(p=>p[c]);out.push(quantile(v,.5),quantile(v,.75)-quantile(v,.25));}
  out.push(quantile(roi.map(p=>p[0]/Math.max(p[1],1e-8)),.5),quantile(roi.map(p=>Math.log((p[0]+1e-8)/(p[1]+1e-8))),.5));
  const sat=roi.map(p=>(Math.max(...p)-Math.min(...p))/Math.max(Math.max(...p),1e-8));
  out.push(quantile(sat,.5),quantile(sat,.75)-quantile(sat,.25)); return out;
}
export function analyze(rgb:RGB[], n:number, method:Method='none', references=true) {
  const {mask,cohesion}=segment(rgb,n), lin=rgb.map(linear);
  const lum=lin.map(p=>p[0]*.2126+p[1]*.7152+p[2]*.0722), lap:number[]=[];
  for(let y=1;y<n-1;y++)for(let x=1;x<n-1;x++){const i=y*n+x;if(mask[i])lap.push(-4*lum[i]+lum[i-1]+lum[i+1]+lum[i-n]+lum[i+n]);}
  const roi=rgb.filter((_,i)=>mask[i]); const m=lap.length?mean(lap):0;
  const quality:Quality={area:roi.length/(n*n),cohesion,blur:lap.length?mean(lap.map(v=>(v-m)**2)):0,
    clipped:roi.length?roi.filter(p=>Math.min(...p)<=5||Math.max(...p)>=250).length/roi.length:1,
    glare:rgb.filter(p=>Math.min(...p)>=245).length/(n*n)};
  const normalized=normalize(lin,method,n,references);
  return {mask,quality,normalized,features:normalized?features(normalized,mask):Array(10).fill(NaN) as number[]};
}
export function failures(q:Quality,l:Limits):string[] {
  const out:string[]=[];
  if(q.area<l.min_area||q.area>l.max_area)out.push('eyelid');
  if(q.blur<l.min_blur)out.push('blur');
  if(q.clipped>l.max_clipped)out.push('exposure');
  if(q.glare>l.max_glare)out.push('glare');
  if(q.cohesion<l.min_cohesion)out.push('cohesion');return out;
}
export function predict(f:number[],m:Model):number {
  const z=m.intercept+f.reduce((s,v,i)=>s+(v-m.mean[i])/m.scale[i]*m.coefficients[i],0);
  return 1/(1+Math.exp(-(z*m.platt_coefficient+m.platt_intercept)));
}
