# Un seul GLB, plusieurs maillages sur le même squelette : « rest » = maillage d'origine (poids lissés, parfait bras
# le long du corps), « splitR » = bras droit séparé du corps (salut), « split » = les deux bras séparés (assis).
# Le site affiche l'un ou l'autre selon la pose (avatarGlb.ts : setSplit).
# Usage : python3 merge.py origine.glb splitR=bras-droit.glb split=deux-bras.glb sortie.glb
import sys, pygltflib, numpy as np
a=pygltflib.GLTF2().load(sys.argv[1]); out=sys.argv[-1]
blob=bytearray(a.binary_blob())
def copy_acc(i,b,bb):
  acc=b.accessors[i]; bv=b.bufferViews[acc.bufferView]
  data=bb[(bv.byteOffset or 0):(bv.byteOffset or 0)+bv.byteLength]
  while len(blob)%4: blob.append(0)
  off=len(blob); blob.extend(data)
  a.bufferViews.append(pygltflib.BufferView(buffer=0,byteOffset=off,byteLength=len(data),byteStride=bv.byteStride,target=bv.target))
  na=pygltflib.Accessor(**{k:v for k,v in acc.__dict__.items() if k in ('byteOffset','componentType','normalized','count','type','max','min')})
  na.bufferView=len(a.bufferViews)-1; a.accessors.append(na); return len(a.accessors)-1
for arg in sys.argv[2:-1]:
  name,f=arg.split('=')
  b=pygltflib.GLTF2().load(f); bb=b.binary_blob()
  p=b.meshes[0].primitives[0]; at=p.attributes
  prim=pygltflib.Primitive(attributes=pygltflib.Attributes(POSITION=copy_acc(at.POSITION,b,bb),NORMAL=copy_acc(at.NORMAL,b,bb),TEXCOORD_0=copy_acc(at.TEXCOORD_0,b,bb),JOINTS_0=copy_acc(at.JOINTS_0,b,bb),WEIGHTS_0=copy_acc(at.WEIGHTS_0,b,bb)),indices=copy_acc(p.indices,b,bb),material=a.meshes[0].primitives[0].material)
  a.meshes.append(pygltflib.Mesh(name=name,primitives=[prim])); a.meshes[0].name='rest'
  mn=[i for i,n in enumerate(a.nodes) if n.mesh is not None][0]; a.nodes[mn].name='rest'
  a.nodes.append(pygltflib.Node(name=name,mesh=len(a.meshes)-1,skin=a.nodes[mn].skin))
  a.scenes[0].nodes.append(len(a.nodes)-1)
a.buffers[0].byteLength=len(blob); a.set_binary_blob(bytes(blob)); a.save(out); print('ok')
