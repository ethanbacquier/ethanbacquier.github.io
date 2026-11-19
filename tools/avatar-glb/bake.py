import sys, numpy as np, pygltflib, struct
from scipy.spatial import cKDTree
from joints import J
src, wfile, out = sys.argv[1:4]
d=np.load(wfile); names=list(d['names'])
g=pygltflib.GLTF2().load(src)
blob=bytearray(g.binary_blob())
prim=g.meshes[0].primitives[0]
acc=g.accessors[prim.attributes.POSITION]; bv=g.bufferViews[acc.bufferView]
P=np.frombuffer(blob,np.float32,acc.count*3,(bv.byteOffset or 0)+(acc.byteOffset or 0)).reshape(-1,3).copy()
# mesh node world transform: assume identity-ish; check
mn=[i for i,n in enumerate(g.nodes) if n.mesh is not None][0]
print('mesh node',g.nodes[mn])
if len(d['co'])==len(P) and np.abs(d['co']-P).max()<1e-6:
  W=d['W'].astype(np.float64)   # poids donnés sommet par sommet (cut2.py : copies superposées aux poids différents)
else:
 tree=cKDTree(d['co']); dist,idx=tree.query(P,k=3)

 w=1/(dist+1e-5); w/=w.sum(1,keepdims=True)
 W=(d['W'][idx]*w[...,None]).sum(1)
K=0.667/0.68
def T(p): p=np.asarray(p,np.float64); return np.stack([p[...,0]*K,(p[...,1]+0.32)*K+0.667,(p[...,2]+0.03)*K],-1)

import fixups; W=fixups.fix(P,W,names)
top=np.argsort(-W,1)[:,:4]; tw=np.take_along_axis(W,top,1); tw/=tw.sum(1,keepdims=True)
JO=top.astype(np.uint16); WE=tw.astype(np.float32)
def add(arr,comp,ctype,typ):
  while len(blob)%4: blob.append(0)
  off=len(blob); b=arr.tobytes(); blob.extend(b)
  g.bufferViews.append(pygltflib.BufferView(buffer=0,byteOffset=off,byteLength=len(b)))
  g.accessors.append(pygltflib.Accessor(bufferView=len(g.bufferViews)-1,componentType=ctype,count=len(arr),type=typ))
  return len(g.accessors)-1
NP=T(P).astype(np.float32); blob[(bv.byteOffset or 0)+(acc.byteOffset or 0):(bv.byteOffset or 0)+(acc.byteOffset or 0)+NP.nbytes]=NP.tobytes()
acc.min=NP.min(0).tolist(); acc.max=NP.max(0).tolist()
J2={n:(p,T(h),T(t)) for n,(p,h,t) in J.items()}
prim.attributes.JOINTS_0=add(JO,0,pygltflib.UNSIGNED_SHORT,'VEC4')
prim.attributes.WEIGHTS_0=add(WE,0,pygltflib.FLOAT,'VEC4')
# bones: identity rotations, translation relative to parent
base=len(g.nodes)
for n in names:
  p,h,t=J2[n]; ph=J2[p][1] if p else np.zeros(3)
  g.nodes.append(pygltflib.Node(name=n,translation=(h-ph).tolist(),children=[]))
for i,n in enumerate(names):
  p=J[n][0]
  if p: g.nodes[base+names.index(p)].children.append(base+i)
ibm=np.zeros((len(names),4,4),np.float32)
for i,n in enumerate(names):
  m=np.eye(4,dtype=np.float32); m[:3,3]=-J2[n][1]; ibm[i]=m.T  # column-major
g.skins=[pygltflib.Skin(joints=[base+i for i in range(len(names))],skeleton=base,inverseBindMatrices=add(ibm.reshape(-1,16),0,pygltflib.FLOAT,'MAT4'))]
g.nodes[mn].skin=0
g.scenes[0].nodes.append(base)
g.buffers[0].byteLength=len(blob); g.set_binary_blob(bytes(blob)); g.save(out)
print('ok',out)
