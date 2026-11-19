import sys, numpy as np, trimesh
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, binary_dilation
src,dst,TH=sys.argv[1],sys.argv[2],float(sys.argv[3])
m=list(trimesh.load(src,process=False).geometry.values())[0]
tex=m.visual.material.baseColorTexture.convert('RGB'); W,H=tex.size
a=np.asarray(tex).astype(np.float32)/255
uv=np.asarray(m.visual.uv); F=np.asarray(m.faces); cen=m.triangles_center
zone=(cen[:,1]>-0.45)&(cen[:,1]<0.22)&(np.abs(cen[:,0])>0.1)
mk=Image.new('L',(W,H),0); d=ImageDraw.Draw(mk)
for f in np.where(zone)[0]:
  d.polygon([(uv[k,0]*W,(1-uv[k,1])*H) for k in F[f]],fill=255,outline=255)
mask=np.asarray(mk)>0
lum=a@[0.3,0.59,0.11]; warm=a[...,0]-a[...,2]
skin=(warm>0.1)&(lum>0.25)
skin=binary_dilation(skin,iterations=3)
bad=mask&~skin&(lum>TH)
bad=binary_dilation(bad,iterations=2)&mask&~skin
good=mask&~bad&~skin
print('bad px',bad.sum(),'good',good.sum())
S=8; out=a.copy()
num=np.stack([gaussian_filter(a[...,i]*good,S) for i in range(3)],-1); den=gaussian_filter(good.astype(np.float32),S)[...,None]
fill=num/np.maximum(den,1e-4)
# fallback for areas far from good texels
med=np.median(a[good],0); far=den[...,0]<1e-3
fill[far]=med
out[bad]=fill[bad]
img=Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8))
m.visual.material=trimesh.visual.material.PBRMaterial(baseColorTexture=img,metallicFactor=0.0,roughnessFactor=0.6)
trimesh.Scene(m).export(dst)
