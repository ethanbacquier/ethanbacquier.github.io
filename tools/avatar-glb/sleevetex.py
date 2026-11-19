# Manches : la texture IA avait peint des taches gris clair (contact poignet / hanche) sur l'avant-bras.
# On ramène les texels de manche trop clairs vers la teinte de la manche (sans toucher la peau ni le reste).
import sys, io, numpy as np, pygltflib
from PIL import Image, ImageDraw, ImageFilter
src,out=sys.argv[1],sys.argv[2]; D=float(sys.argv[3]) if len(sys.argv)>3 else 0.03
g=pygltflib.GLTF2().load(src); blob=g.binary_blob()
def acc(i):
  a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
  dt={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a.componentType]
  n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]
  return np.frombuffer(blob,dt,a.count*n,(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,n) if not bv.byteStride else None
skin=g.skins[0]; jn=[g.nodes[j].name for j in skin.joints]
img_bv=g.bufferViews[g.images[0].bufferView]
im=Image.open(io.BytesIO(blob[img_bv.byteOffset or 0:(img_bv.byteOffset or 0)+img_bv.byteLength])).convert('RGB')
T=np.asarray(im).astype(np.float32)/255; H,Wd=T.shape[:2]
mask=Image.new('L',(Wd,H),0); dr=ImageDraw.Draw(mask)
fore=[i for i,n in enumerate(jn) if n in ('laL','laR','hL','hR')]
print('joints',jn)
for mesh in g.meshes:
  p=mesh.primitives[0]; at=p.attributes
  UV=acc(at.TEXCOORD_0); J=acc(at.JOINTS_0); Wt=acc(at.WEIGHTS_0); F=acc(p.indices).reshape(-1,3)
  fw=np.zeros(len(UV))
  for k in range(4): fw+=np.where(np.isin(J[:,k],fore),Wt[:,k],0)
  for f in F:
    if fw[f].mean()>0.6:
      dr.polygon([(UV[v,0]*Wd,UV[v,1]*H) for v in f],fill=255)
M=np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>0
lum=T@[0.3,0.59,0.11]; skin_=(T[...,0]-T[...,2]>0.15)&(lum>0.5); M&=~skin_
med=np.median(T[M],0); ml=med@[0.3,0.59,0.11]; print('manche',(med*255).round(),'texels',M.sum())
excess=np.clip(lum-ml-D,0,None)
k=np.where(M,np.clip(excess/0.08,0,1),0)[...,None]
# couleur cible : la teinte médiane, éclairée comme l'original jusqu'à ml+D
tgt=med*((ml+D)/ml)
T2=T*(1-k)+np.minimum(T,tgt)*k
# fondu doux du masque
km=np.asarray(Image.fromarray((M*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)))[...,None]/255
T3=T*(1-km)+T2*km
import os
if os.environ.get('RED'): T3=np.where(M[...,None],np.array([1,0,0.]),T3)
buf=io.BytesIO(); Image.fromarray((np.clip(T3,0,1)*255).astype(np.uint8)).save(buf,'PNG'); data=buf.getvalue()
nb=bytearray(blob); 
while len(nb)%4: nb.append(0)
off=len(nb); nb.extend(data)
g.bufferViews.append(pygltflib.BufferView(buffer=0,byteOffset=off,byteLength=len(data)))
g.images[0].bufferView=len(g.bufferViews)-1
g.buffers[0].byteLength=len(nb); g.set_binary_blob(bytes(nb)); g.save(out); print('ok')
