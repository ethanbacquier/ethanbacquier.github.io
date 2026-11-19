import numpy as np
from scipy.optimize import minimize
from joints import J
K=0.667/0.68
def T(p): p=np.asarray(p,float); return np.array([p[0]*K,(p[1]+0.32)*K+0.667,(p[2]+0.03)*K])
def R(e):
  x,y,z=e; cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
  Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]]);Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]);Rz=np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
  return Rx@Ry@Rz
import os
HIPS_Y=float(os.environ.get('HY',0.37)); HIPS_Z=0.0
TGT=[float(x) for x in os.environ.get('TGT','0.12,0.665,0.40').split(',')]
DIR=np.array([float(x) for x in os.environ.get('DIR','0,-0.35,0.94').split(',')]); DIR/=np.linalg.norm(DIR)
EDGE=[float(x) for x in os.environ.get('EDGE','0.3,0.66').split(',')]
POSE={'hips':(0,0,0),'spine':(0.06,0,0),'chest':(0.04,0,0)}
def fk(side,ua,la,h):
  sx=1 if side=='L' else -1
  M=np.eye(3); p=np.array([0,HIPS_Y,HIPS_Z+T(J['hips'][1])[2]])
  chain=[('hips',None),('spine',None),('chest',None),('ua'+side,ua),('la'+side,la),('h'+side,h)]
  pts={}; prev=None
  for n,rot in chain:
    if prev is not None: p=p+M@(T(J[n][1])-T(J[prev][1]))
    M=M@R(rot if rot is not None else POSE[n]); pts[n]=(p.copy(),M.copy()); prev=n
  tip=p+M@(T(J['h'+side][2])-T(J['h'+side][1]))
  return pts,tip
def cost(x,side='L'):
  sx=1 if side=='L' else -1
  ua=(x[0],x[1],x[2]); la=(x[3],x[4],0); h=(x[5],x[6],x[7])
  pts,tip=fk(side,ua,la,h)
  w=pts['h'+side][0]; e=pts['la'+side][0]
  tgt=np.array([sx*TGT[0],TGT[1],TGT[2]])
  c=100*np.sum((w-tgt)**2)
  d=tip-w; d/=np.linalg.norm(d)
  c+=2*np.sum((d-DIR)**2)
  # forearm above desk edge z=0.31
  for t in np.linspace(0,1,8):
    q=e+(w-e)*t
    if q[2]>EDGE[0]: c+=200*max(0,EDGE[1]-q[1])**2
  c+=50*max(0,abs(0.2)-sx*e[0])**2  # elbow outside torso
  c+=0.02*np.sum(np.array(x)**2)
  return c
def main():
  best=None
  for s in range(30):
    x0=np.random.default_rng(s).normal(0,0.8,8)
    r=minimize(cost,x0,method='Nelder-Mead',options={'maxiter':20000,'xatol':1e-5,'fatol':1e-8})
    r=minimize(cost,r.x,method='BFGS')
    if best is None or r.fun<best.fun: best=r
  x=best.x; print('cost',best.fun)
  pts,tip=fk('L',x[0:3],(x[3],x[4],0),x[5:8])
  print('wrist',pts['hL'][0].round(3),'elbow',pts['laL'][0].round(3),'shoulder',pts['uaL'][0].round(3))
  print('ua',x[0:3].round(3).tolist(),'la',[round(x[3],3),round(x[4],3),0],'hand',x[5:8].round(3).tolist())

if __name__=='__main__': main()
