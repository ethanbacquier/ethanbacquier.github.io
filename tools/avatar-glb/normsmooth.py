# Capuche et col : le maillage IA est facetté (petites marches d'ombre sur le bord de la capuche).
# On lisse seulement les normales (la forme et la silhouette ne bougent pas), dans la zone du col, hors tête.
import sys, os, numpy as np, pygltflib
from scipy.spatial import cKDTree
src,out=sys.argv[1],sys.argv[2]; R=float(sys.argv[3]) if len(sys.argv)>3 else 0.012
Y0,Y1,XW=[float(x) for x in os.environ.get('ZONE','1.1,1.36,0.26').split(',')]
g=pygltflib.GLTF2().load(src); blob=bytearray(g.binary_blob())
def view(i):
  a=g.accessors[i]; bv=g.bufferViews[a.bufferView]
  dt={5126:np.float32,5125:np.uint32,5123:np.uint16,5121:np.uint8}[a.componentType]
  n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a.type]; off=(bv.byteOffset or 0)+(a.byteOffset or 0)
  return np.frombuffer(blob,dt,a.count*n,off).reshape(a.count,n), off
jn=[g.nodes[j].name for j in g.skins[0].joints]; H=jn.index('head')
for mesh in g.meshes:
  at=mesh.primitives[0].attributes
  P,_=view(at.POSITION); N,noff=view(at.NORMAL); J,_=view(at.JOINTS_0); W,_=view(at.WEIGHTS_0)
  hw=(np.where(J==H,W,0)).sum(1)
  z=(P[:,1]>Y0)&(P[:,1]<Y1)&(np.abs(P[:,0])<XW)&(hw<0.3)
  # fondu aux bords de la zone
  e=np.minimum.reduce([(P[:,1]-Y0)/0.03,(Y1-P[:,1])/0.03,(XW-np.abs(P[:,0]))/0.03,(0.3-hw)/0.3]); e=np.clip(e,0,1)
  idx=np.where(z)[0]; tr=cKDTree(P[idx]); NN=N.copy().astype(np.float64)
  for k,lst in zip(idx,tr.query_ball_point(P[idx],R)):
    n=N[idx[lst]].sum(0); n/=np.linalg.norm(n)+1e-9
    m=N[k]*(1-e[k])+n*e[k]; NN[k]=m/(np.linalg.norm(m)+1e-9)
  blob[noff:noff+NN.size*4]=NN.astype(np.float32).tobytes()
  print(mesh.name,len(idx))
g.set_binary_blob(bytes(blob)); g.save(out); print('ok')
