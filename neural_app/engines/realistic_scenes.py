"""Photographic solar/Earth material and a volumetric hydrogen density study.

NASA imagery is bundled locally; no runtime image downloads are performed.
The solar image is an SDO 304 Å false-color reference, not a live measurement.
"""
import math,random,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageChops
from .scenes import SceneRenderer,mix

ASSETS=Path(__file__).resolve().parents[2]/'assets'

class RealisticSceneRenderer(SceneRenderer):
    def backdrop(self,w,h,preset):
        key=(w,h,'realistic')
        if self.background_key==key:return self.background.copy()
        yy,xx=np.mgrid[0:h,0:w];cloud=np.exp(-((xx/w-.55)**2/.35+(yy/h-.58)**2/.18))
        arr=np.zeros((h,w,3),dtype=np.uint8)
        for c,(base,gain) in enumerate(((2,4),(5,7),(10,12))):arr[:,:,c]=base+cloud*gain
        image=Image.fromarray(arr);d=ImageDraw.Draw(image);rng=random.Random(9102)
        for _ in range(max(80,w*h//5000)):
            x=rng.randrange(w);y=rng.randrange(h);b=rng.randrange(22,99)
            d.point((x,y),fill=(int(b*.78),int(b*.88),b))
        self.background=image;self.background_key=key;return image.copy()

    def photographic(self,kind,r):
        r=int(r);key=('photographic',kind,r)
        if key in self.assets:return self.assets[key]
        source=Image.open(ASSETS/('sun-sdo-304.jpg' if kind=='sun' else 'earth-blue-marble.jpg')).convert('RGB')
        if kind=='sun':source=source.crop((25,25,999,975))
        else:source=source.crop((25,25,775,775))
        size=2*r;source=source.resize((size,size),Image.Resampling.LANCZOS)
        a=np.asarray(source,dtype=np.float32)/255
        yy,xx=np.mgrid[-1:1:complex(size),-1:1:complex(size)];rr=np.sqrt(xx*xx+yy*yy)
        if kind=='sun':
            # Maintain actual solar texture and color; brighten faint coronal detail.
            a=np.power(a,.85);alpha=np.clip(a.max(2)*3.5,0,1)*np.clip((1.05-rr)*35,0,1)
        else:
            z=np.sqrt(np.clip(1-rr*rr,0,1));light=np.clip(-.66*xx-.18*yy+.55*z,0,1)
            a*=np.clip(.12+light[:,:,None]*1.15,0,1)
            # Blue grazing atmosphere, smoothly blended instead of hard drawn rings.
            rim=np.power(np.clip(1-z,0,1),5)*np.clip(.5-.3*xx,0,1)
            a+=rim[:,:,None]*np.array([.035,.12,.25])
            alpha=np.clip((.995-rr)*size/2,0,1)
        rgba=np.concatenate((np.clip(a*255,0,255),alpha[:,:,None]*255),axis=2).astype(np.uint8)
        result=Image.fromarray(rgba);self.assets[key]=result
        return result

    def atom(self,image,cx,cy,r,t):
        key=('density',int(r))
        if key not in self.assets:
            size=int(r*3.1);yy,xx=np.mgrid[-1.55:1.55:complex(size),-1.55:1.55:complex(size)]
            radius=np.sqrt(xx*xx+yy*yy)
            rng=np.random.default_rng(1042)
            # Projected radial density with fine grain gives volume without Bohr orbit rings.
            density=np.exp(-3.8*radius)*np.clip(1+.15*np.sin(xx*27+yy*9)+rng.normal(0,.08,xx.shape),.5,1.5)
            alpha=np.clip(density*190,0,180)
            rgba=np.zeros((size,size,4),dtype=np.uint8)
            rgba[:,:,:3]=[94,172,226];rgba[:,:,3]=alpha.astype(np.uint8)
            cloud=Image.fromarray(rgba).filter(ImageFilter.GaussianBlur(.4));self.assets[key]=cloud
        cloud=self.assets[key];image.paste(cloud,(round(cx-cloud.width/2),round(cy-cloud.height/2)),cloud)
        layer=Image.new('RGBA',image.size);d=ImageDraw.Draw(layer);rng=random.Random(83)
        # Sparse density samples: visual demonstration, not detected particles.
        for i in range(800):
            angle=rng.random()*math.tau;distance=min(r*1.5,rng.gammavariate(2,r*.16))
            x=cx+math.cos(angle)*distance;y=cy+math.sin(angle)*distance*.8
            a=int(25+100*math.exp(-distance/r));d.point((x,y),fill=(116,194,237,a))
        image.paste(layer,(0,0),layer)
        glow=Image.new('RGBA',image.size);d=ImageDraw.Draw(glow)
        d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=(221,239,255,200));image.paste(glow.filter(ImageFilter.GaussianBlur(5)),(0,0),glow.filter(ImageFilter.GaussianBlur(5)))
        ImageDraw.Draw(image).ellipse((cx-1.5,cy-1.5,cx+1.5,cy+1.5),fill=(240,249,255))

    def sun(self,image,cx,cy,r,t):
        sphere=self.photographic('sun',r*1.12);size=sphere.width
        self.light(image,cx,cy,r*1.45,(163,47,15))
        image.paste(sphere,(round(cx-size/2),round(cy-size/2)),sphere)

    def earth(self,image,cx,cy,r,t):
        sphere=self.photographic('earth',r);size=sphere.width
        self.light(image,cx,cy,r*1.13,(10,31,57));image.paste(sphere,(round(cx-size/2),round(cy-size/2)),sphere)

    def render(self,width,height,preset='Cosmos',bits='',previous='',bus_events=(),pointer=None,detail='Balanced',now=None):
        if preset not in ('Cosmos','Overview'):return super().render(width,height,preset,bits,previous,bus_events,pointer,detail,now)
        w=max(600,int(width));h=max(260,int(height));t=time.monotonic()-self.epoch if now is None else now
        image=self.backdrop(w,h,preset);cy=h*.54;radius=h*.30
        positions=(w*.22,w*.53,w*.82)
        self.atom(image,positions[0],cy,radius*.92,t);self.sun(image,positions[1],cy,radius,t);self.earth(image,positions[2],cy,radius*.93,t)
        d=ImageDraw.Draw(image)
        labels=(('HYDROGEN','PROJECTED ELECTRON DENSITY'),('STELLAR','NASA / SDO · 304 Å REFERENCE'),('EARTH','NASA / BLUE MARBLE'))
        for x,(name,caption) in zip(positions,labels):
            d.text((x,h*.91),name,font=self.f(max(10,int(w/108)),True),fill=(160,182,201),anchor='mm')
            d.text((x,h*.962),caption,font=self.f(max(8,int(w/155)),True),fill=(76,99,121),anchor='mm')
        # Thin live transport arcs belong to app state; photos are fixed references.
        activity=bits.count('1')/max(1,len(bits))
        for left,right in zip(positions,positions[1:]):
            y=h*.79;points=[(left+(right-left)*i/100,y+math.sin(i/100*math.pi)*h*.045) for i in range(101)]
            d.line(points,fill=(20,44,57),width=1)
            for n in range(2):
                u=(t*.045+n*.5)%1;x=left+(right-left)*u;py=y+math.sin(u*math.pi)*h*.045
                value=int(75+activity*75);d.ellipse((x-1,py-1,x+1,py+1),fill=(value//2,value,value))
        self.last_size=(w,h)
        return image
