# Sépare bras et corps là où le modèle IA les a soudés (main contre la cuisse, coude et avant-bras contre la taille).
# Sous l'aisselle : poids francs (bras ou corps), faces de jonction doublées (une copie suit le corps, l'autre le
# bras : rien ne change au repos), puis les deux bords ouverts sont cousus (bouchons cachés au repos).
import numpy as np, trimesh, sys
from collections import defaultdict
from scipy.spatial import cKDTree
from sitmeasure import W as W0, names, V as VT, m
src_out=sys.argv[2]; YCUT=float(sys.argv[1]); SMOOTH=int(sys.argv[3]) if len(sys.argv)>3 else 0; KEEP_BRIDGE=int(sys.argv[4]) if len(sys.argv)>4 else 0
F0=np.asarray(m.faces); P0=np.asarray(m.vertices); UV0=np.asarray(m.visual.uv); N0=np.asarray(m.vertex_normals)
_,first,pid=np.unique(np.round(P0,6),axis=0,return_index=True,return_inverse=True); pid=pid.ravel()
P=P0[first]; Wo=W0[first].copy(); VTw=VT[first]
N=np.zeros_like(P); np.add.at(N,pid,N0); N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12
F=pid[F0]; CUV=UV0[F0]            # faces soudées, UV par coin
ix=names.index; arm={s:[ix('ua'+s),ix('la'+s),ix('h'+s)] for s in 'LR'}; armall=arm['L']+arm['R']
low=VTw[:,1]<YCUT
grp=np.zeros(len(P),int)
for k,s in enumerate('LR'): grp[low&(Wo[:,arm[s]].sum(1)>0.5)]=k+1
grp[~low]=-1
W=Wo.copy()
def only(w,keep):
  k=np.zeros(len(names)); k[keep]=1; x=w*k; return x/x.sum() if x.sum()>1e-6 else None
body=[i for i in range(len(names)) if i not in armall]
for v in np.where(low)[0]:
  W[v]=only(Wo[v],arm['LR'[grp[v]-1]] if grp[v]>0 else body) if (only(Wo[v],arm['LR'[grp[v]-1]] if grp[v]>0 else body) is not None) else Wo[v]
fg=grp[F]; armin=(fg>0).any(1); bodyin=(fg==0).any(1)
cut=armin&bodyin&~(fg==-1).all(1)
print('faces de jonction',cut.sum())
cutv=np.unique(F[cut])
NP=list(P); NW=list(W); NN=list(N); dup_body={}; dup_arm={}
bodyv=np.where(grp==0)[0]; tb=cKDTree(P[bodyv])
for v in cutv:
  if grp[v]>0:   # copie « corps » d'un sommet du bras
    w=only(Wo[v],body); w=w if w is not None else W[bodyv[tb.query(P[v])[1]]]
    dup_body[v]=len(NP); NP.append(P[v]); NW.append(w); NN.append(N[v])
  elif grp[v]==0:
    s='L' if P[v,0]>0 else 'R'; av=np.where(grp==(1 if s=='L' else 2))[0]
    w=only(Wo[v],arm[s]); w=w if w is not None else W[av[cKDTree(P[av]).query(P[v])[1]]]
    dup_arm[v]=len(NP); NP.append(P[v]); NW.append(w); NN.append(N[v])
NF=[f for f in F[~cut]]; NC=[c for c in CUV[~cut]]
# Faces de jonction supprimées (le site affiche le maillage d'origine bras le long du corps : rien à cacher au repos).
# KEEP_BRIDGE=1 : ancienne variante, faces doublées (une copie par côté), qui laissait une « aile » sur le flanc.
if KEEP_BRIDGE:
  for f,c in zip(F[cut],CUV[cut]):
    NF.append([dup_body.get(v,v) for v in f]); NC.append(c)
    NF.append([dup_arm.get(v,v) for v in f]); NC.append(c)
NF=np.array(NF); NC=np.array(NC)
# bords ouverts
cnt=defaultdict(int); dirs={}
for f in NF:
  for i in range(3):
    a,b=f[i],f[(i+1)%3]; cnt[(min(a,b),max(a,b))]+=1; dirs[(a,b)]=1
dupset=set(dup_body.values())|set(dup_arm.values())|set(cutv)
bnd=[(a,b) for (a,b) in dirs if cnt[(min(a,b),max(a,b))]==1 and (a in dupset or b in dupset)]
print('arêtes de bord',len(bnd))
nxt=defaultdict(list)
for a,b in bnd: nxt[a].append(b)
used=set(); loops=[]
for e in bnd:
  if e in used: continue
  loop=[e[0]]; cur=e
  while cur not in used:
    used.add(cur); c=cur[1]; loop.append(c)
    cand=[n for n in nxt[c] if (c,n) not in used]
    if not cand: break
    cur=(c,cand[0])
  if loop[-1]==loop[0]: loops.append(loop[:-1])
print('boucles',[len(l) for l in loops])
tex=np.asarray(m.visual.material.baseColorTexture.convert('RGB')).astype(np.float32)/255; Ht,Wt=tex.shape[:2]
def colat(u): return tex[min(Ht-1,int((1-u[1])*Ht)),min(Wt-1,int(u[0]*Wt))]
NP=np.array(NP); NW=np.array(NW); NN=np.array(NN)
side_of=lambda v: 'arm' if (v in dup_arm.values() or (v<len(grp) and grp[v]>0)) else ('body' if (v in dup_body.values() or (v<len(grp) and grp[v]==0)) else 'top')
capF=[]; capUV=[]
from joints import J
def axis_pt(p,want,sx):
  # point de l'axe le plus proche : os du bras (épaule → main) ou axe vertical du buste
  if want=='body': return np.array([0.0,p[1],-0.03])
  s='L' if sx>0 else 'R'; best=None
  for n in ('ua'+s,'la'+s,'h'+s):
    h,t=np.array(J[n][1],float),np.array(J[n][2],float); ab=t-h
    u=np.clip((p-h)@ab/(ab@ab),0,1); q=h+u*ab
    if best is None or np.linalg.norm(p-q)<np.linalg.norm(p-best): best=q
  return best
ROWS=5; BULGE_ARM=1.0; BULGE_BODY=1.0  # côté buste : bombé comme le flanc (au repos, le site affiche le maillage d’origine)
def zip_strip(run,outward,uvpick,want='arm',sx=1):
  # Bouchon arrondi : entre les deux brins, des rangées de points sur un arc autour de l'axe du bras (ou du buste),
  # au rayon de la surface voisine, pour que le dessous de la manche garde son volume au lieu d'être plat.
  global NP,NW,NN
  pts=NP[run]; L=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
  mid=int(np.searchsorted(L,L[-1]/2)); a=run[:mid+1]; b=run[mid:][::-1]
  rungs=[]; i=j=0
  def rung(va,vb):
    global NP,NW,NN
    pa,pb=NP[va],NP[vb]; row=[va]; P2=[];W2=[]
    for k in range(1,ROWS):
      s_=k/ROWS; c=(1-s_)*pa+s_*pb; o=axis_pt(c,want,sx); v=c-o
      ra=np.linalg.norm(pa-axis_pt(pa,want,sx)); rb=np.linalg.norm(pb-axis_pt(pb,want,sx))
      if np.linalg.norm(v)>1e-5: c=c+(BULGE_ARM if want=='arm' else BULGE_BODY)*(o+v/np.linalg.norm(v)*((1-s_)*ra+s_*rb)-c)
      P2.append(c); W2.append((1-s_)*NW[va]+s_*NW[vb]); row.append(len(NP)+len(P2)-1)
    row.append(vb)
    if P2:
      NP=np.vstack([NP,P2]); NW=np.vstack([NW,W2]); NN=np.vstack([NN,np.zeros((len(P2),3))])
    return row
  rungs.append(rung(a[0],b[0]))
  while i<len(a)-1 or j<len(b)-1:
    if j>=len(b)-1 or (i<len(a)-1 and np.linalg.norm(NP[a[i+1]]-NP[b[j]])<np.linalg.norm(NP[a[i]]-NP[b[j+1]])): i+=1
    else: j+=1
    rungs.append(rung(a[i],b[j]))
  for R0,R1 in zip(rungs[:-1],rungs[1:]):
    for m in range(ROWS):
      for t in ([R0[m],R0[m+1],R1[m+1]],[R0[m],R1[m+1],R1[m]]):
        if len(set(t))<3: continue
        q=NP[t]; n=np.cross(q[1]-q[0],q[2]-q[0]); c=q.mean(0)
        if n@(c-axis_pt(c,want,sx))<0: t=t[::-1]
        capF.append(t); capUV.append(uvpick)
# texel du sweat : coin sombre le plus proche de la couleur médiane des faces voisines
nearF=np.isin(NF,list(cutv)).any(1)
cols=np.array([[colat(u) for u in c] for c in NC[nearF]]).reshape(-1,3); uvs=NC[nearF].reshape(-1,2)
lum=cols@[0.3,0.59,0.11]; dark=lum<0.2; med=np.median(cols[dark],0)
uvpick=uvs[dark][np.argmin(np.linalg.norm(cols[dark]-med,axis=1))]; print('couleur bouchon',(med*255).round())
for loop in loops:
  sx=1 if NP[loop,0].mean()>0 else -1
  lab=np.array([side_of(v) for v in loop]); n=len(loop)
  for want,outward in (('arm',np.array([-sx,0,0.])),('body',np.array([sx,0,0.]))):
    inr=(lab==want)|(lab=='top')
    for st in [k for k in range(n) if inr[k] and not inr[k-1]]:
      run=[]; k=st
      while inr[k%n] and len(run)<n: run.append(loop[k%n]); k+=1
      if len(run)>=3:
        # bord en dents de scie (ligne des poids à 50 %) : on le lisse le long du brin (copies seulement)
        mv=[k for k in range(1,len(run)-1) if run[k]>=len(grp)]
        for it in range(SMOOTH):
          Q=NP[run].copy()
          for k in mv: NP[run[k]]=0.5*Q[k]+0.25*(Q[k-1]+Q[k+1])
        zip_strip(run,outward,uvpick,want,sx); print(' bouchon',want,len(run))
# sommets propres aux bouchons (normales lissées sur le bouchon)
capF=np.array(capF); remap={}; CP=[];CW=[]
for v in np.unique(capF): remap[v]=len(NP)+len(CP); CP.append(NP[v]); CW.append(NW[v])
capF2=np.vectorize(remap.get)(capF)
CN=np.zeros((len(CP),3))
for t in capF:
  q=NP[t]; n=np.cross(q[1]-q[0],q[2]-q[0])
  for v in t: CN[remap[v]-len(NP)]+=n
CN/=np.linalg.norm(CN,axis=1,keepdims=True)+1e-12
NP=np.vstack([NP,CP]); NW=np.vstack([NW,CW]); NN=np.vstack([NN,CN])
NF=np.vstack([NF,capF2]); NC=np.vstack([NC,np.repeat(np.array(capUV)[:,None,:],3,1)])
# maillage final : un sommet par (sommet soudé, UV)
key={}; OP=[];OU=[];ON=[];OW=[];OF=np.zeros_like(NF)
for fi in range(len(NF)):
  for c in range(3):
    v=NF[fi,c]; u=tuple(np.round(NC[fi,c],7)); k=(v,u)
    if k not in key: key[k]=len(OP); OP.append(NP[v]); OU.append(NC[fi,c]); ON.append(NN[v]); OW.append(NW[v])
    OF[fi,c]=key[k]
OP=np.array(OP);OU=np.array(OU);ON=np.array(ON);OW=np.array(OW,np.float32)
out=trimesh.Trimesh(OP,OF,vertex_normals=ON,process=False)
out.visual=trimesh.visual.TextureVisuals(uv=OU,material=m.visual.material)
open(src_out,'wb').write(trimesh.exchange.gltf.export_glb(trimesh.Scene(out),include_normals=True))
np.savez('w_cut.npz',co=OP,W=OW,names=np.array(names))
print('ok',len(OP),len(OF))
