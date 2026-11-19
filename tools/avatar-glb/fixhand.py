# Mains : le modèle IA a peint en noir les creux entre les doigts (poing fermé à l'origine). On repeint ces texels
# couleur peau à partir de la peau voisine (convolution normalisée), seulement sur les faces des mains.
import sys, numpy as np, trimesh
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter, binary_dilation
from sitmeasure import W, names, m
src_out=sys.argv[1]
tex=m.visual.material.baseColorTexture.convert('RGB'); Wt,Ht=tex.size
a=np.asarray(tex).astype(np.float32)/255
uv=np.asarray(m.visual.uv); F=np.asarray(m.faces)
hw=W[:,[names.index('hL'),names.index('hR')]].sum(1)[F].min(1)
zone=hw>0.85
mk=Image.new('L',(Wt,Ht),0); d=ImageDraw.Draw(mk)
for f in np.where(zone)[0]: d.polygon([(uv[k,0]*Wt,(1-uv[k,1])*Ht) for k in F[f]],fill=255,outline=255)
mask=binary_dilation(np.asarray(mk)>0,iterations=2)
lum=a@[0.3,0.59,0.11]; warm=a[...,0]-a[...,2]
skin=(warm>0.08)&(lum>0.35)
bad=mask&~skin
bad=binary_dilation(bad,iterations=2)&mask
good=mask&skin&~bad
print('repeints',bad.sum(),'peau',good.sum())
S=6
num=np.stack([gaussian_filter(a[...,i]*good,S) for i in range(3)],-1); den=gaussian_filter(good.astype(np.float32),S)[...,None]
fill=num/np.maximum(den,1e-4); fill[den[...,0]<1e-3]=np.median(a[good],0)
out=a.copy(); out[bad]=fill[bad]
img=Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8))
m.visual.material=trimesh.visual.material.PBRMaterial(baseColorTexture=img,metallicFactor=0.0,roughnessFactor=0.6)
open(src_out,'wb').write(trimesh.exchange.gltf.export_glb(trimesh.Scene(m),include_normals=True))
img.crop((0,0,Wt,Ht)).save('hand_tex.png')
