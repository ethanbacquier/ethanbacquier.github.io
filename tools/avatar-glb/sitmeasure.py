import numpy as np, trimesh, json, sys
from scipy.spatial import cKDTree
from joints import J
from ik import T, R
m=list(trimesh.load('../hy/soft3c.glb',process=False).geometry.values())[0]
P=np.asarray(m.vertices); d=np.load('w_heat.npz'); names=list(d['names'])
dist,idx=cKDTree(d['co']).query(P,k=3); w=1/(dist+1e-5); w/=w.sum(1,keepdims=True); W=(d['W'][idx]*w[...,None]).sum(1)
V=np.array([T(p) for p in P]); H={n:T(J[n][1]) for n in names}
def pose(rot, hipsY, hipsZ=0.0):
  G={}
  for n in names:  # parents before children in dict order
    p=J[n][0]; r=R(rot.get(n,(0,0,0)))
    if p is None: G[n]=(r, np.array([0,hipsY,H['hips'][2]+hipsZ]))
    else:
      Rp,pp=G[p]; G[n]=(Rp@r, pp+Rp@(H[n]-H[p]))
  out=np.zeros_like(V)
  for i,n in enumerate(names):
    Rb,pb=G[n]; out+=W[:,i:i+1]*((V-H[n])@Rb.T+pb)
  return out,G
if __name__=='__main__':
  rot=json.loads(sys.argv[1]); hy=float(sys.argv[2])
  out,G=pose(rot,hy)
  def rng(mask,lab): s=out[mask]; print(lab,'y',s[:,1].min().round(3),s[:,1].max().round(3),'z',s[:,2].min().round(3),s[:,2].max().round(3))
  lab=W.argmax(1)
  for n in ['hips','ulL','llL','fL','hL','laL','head']: rng(lab==names.index(n),n)
  print('wristL',G['hL'][1].round(3),'elbowL',G['laL'][1].round(3),'shoulderL',G['uaL'][1].round(3))
