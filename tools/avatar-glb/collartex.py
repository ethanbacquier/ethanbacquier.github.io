# Col et capuche : la texture IA y avait un bord peau / sweat en escalier, avec un liseré violet.
# Chaque texel de la zone du col est replacé en 3D (sur le maillage d'origine) ; la limite peau / sweat est lissée
# en 3D (majorité des voisins dans un rayon R), le liseré violet repasse en sweat, et chaque texel reprend la couleur
# moyenne de son côté dans le voisinage (l'ombrage peint est gardé à grande échelle).
import sys, io, os, numpy as np, pygltflib
from PIL import Image
from scipy.spatial import cKDTree
src,out=sys.argv[1],sys.argv[2]; R=float(sys.argv[3]) if len(sys.argv)>3 else 0.009
g=pygltflib.GLTF2().load(src); blob=g.binary_blob()
def acc(i):
  a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
  dt={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a.componentType]
  n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]
  return np.frombuffer(blob,dt,a.count*n,(bv.byteOffset or 0)+(a.byteOffset or 0)).reshape(a.count,n)
ibv=g.bufferViews[g.images[0].bufferView]
T=np.asarray(Image.open(io.BytesIO(blob[ibv.byteOffset or 0:(ibv.byteOffset or 0)+ibv.byteLength])).convert('RGB')).astype(np.float32)/255
H,Wd=T.shape[:2]
p=g.meshes[0].primitives[0]; P=acc(p.attributes.POSITION).astype(np.float64); UV=acc(p.attributes.TEXCOORD_0).astype(np.float64); F=acc(p.indices).reshape(-1,3)
Y0,Y1,XW=[float(x) for x in os.environ.get('ZONE','1.12,1.34,0.24').split(',')]
J=acc(p.attributes.JOINTS_0); Wj=acc(p.attributes.WEIGHTS_0); jn=[g.nodes[j].name for j in g.skins[0].joints]
hw=np.zeros(len(P))
for k in range(4): hw+=np.where(J[:,k]==jn.index('head'),Wj[:,k],0)
c=P[F].mean(1); sel=(c[:,1]>Y0)&(c[:,1]<Y1)&(np.abs(c[:,0])<XW)&(hw[F].max(1)<0.5)
print('faces',sel.sum(),'y',P[:,1].min(),P[:,1].max())
# rasterisation UV → position 3D par texel
pos=np.full((H,Wd,3),np.nan)
for f in F[sel]:
  uv=UV[f]*[Wd,H]; x0,y0=np.floor(uv.min(0)).astype(int); x1,y1=np.ceil(uv.max(0)).astype(int)
  xs,ys=np.meshgrid(np.arange(max(x0,0),min(x1+1,Wd)),np.arange(max(y0,0),min(y1+1,H)))
  q=np.stack([xs.ravel()+0.5,ys.ravel()+0.5],1); a,b,cc=uv
  M=np.array([b-a,cc-a]).T
  if abs(np.linalg.det(M))<1e-9: continue
  l=np.linalg.solve(M,(q-a).T).T; l0=1-l.sum(1); ok=(l>=-0.02).all(1)&(l0>=-0.02)
  if not ok.any(): continue
  w=np.c_[l0,l][ok]; pos[ys.ravel()[ok],xs.ravel()[ok]]=w@P[f]
m=~np.isnan(pos[...,0]); iy,ix=np.where(m); X=pos[iy,ix]; C=T[iy,ix]
lum=C@[0.3,0.59,0.11]
skin=(C[:,0]-C[:,2]>0.13)&(lum>0.33)
purple=((C[:,2]>C[:,0]+0.02)|(C[:,0]-C[:,2]>0.035))&~skin   # liseré violet ou brun (dégradé peau → sweat en escalier)
print('texels',len(X),'peau',skin.mean().round(3),'violet',purple.mean().round(3))
tr=cKDTree(X)
nb=tr.query_ball_point(X,R,workers=-1)
frac=np.array([skin[n].mean() for n in nb])
s=np.clip((frac-0.35)/0.3,0,1); s=s*s*(3-2*s)
# couleur de chaque côté : moyenne des voisins purs (rayon 2R)
nb2=tr.query_ball_point(X,2*R,workers=-1)
RC=float(os.environ.get('RC','0.016')); nb3=tr.query_ball_point(X,RC,workers=-1)   # sweat : taches claires peintes lissées sur ~1,5 cm
cs=C.copy(); cc_=C.copy()
for i,n in enumerate(nb2):
  n=np.array(n); sk=n[skin[n]]; cl=n[~skin[n]&~purple[n]]
  if len(sk): cs[i]=C[sk].mean(0)
  n3=np.array(nb3[i]); cl=n3[~skin[n3]&~purple[n3]]
  if len(cl): cc_[i]=C[cl].mean(0)
# garde le détail fin du texel s'il est déjà du bon côté (et pas violet)
keepS=skin&(s>0.5); keepC=~skin&~purple&(s<0.5)
cs[keepS]=0.5*cs[keepS]+0.5*C[keepS]; cc_[keepC]=0.75*cc_[keepC]+0.25*C[keepC]
new=cs*s[:,None]+cc_*(1-s[:,None])
T2=T.copy(); T2[iy,ix]=new
if os.environ.get('RED'): T2[iy,ix]=np.where(skin[:,None],[1,0,0],[0,0,1])
buf=io.BytesIO(); Image.fromarray((np.clip(T2,0,1)*255).astype(np.uint8)).save(buf,'PNG'); data=buf.getvalue()
nbb=bytearray(blob)
while len(nbb)%4: nbb.append(0)
off=len(nbb); nbb.extend(data)
g.bufferViews.append(pygltflib.BufferView(buffer=0,byteOffset=off,byteLength=len(data)))
g.images[0].bufferView=len(g.bufferViews)-1; g.images[0].mimeType='image/png'
g.buffers[0].byteLength=len(nbb); g.set_binary_blob(bytes(nbb)); g.save(out); print('ok')
