# Un seul GLB, deux maillages sur le même squelette : « rest » = maillage d'origine (poids lissés, parfait bras
# le long du corps), « split » = bras séparés du corps (cut.py, propre bras levé ou assis). Le site affiche l'un
# ou l'autre selon la pose (avatarGlb.ts : setSplit).
import sys, pygltflib, numpy as np
a=pygltflib.GLTF2().load(sys.argv[1]); b=pygltflib.GLTF2().load(sys.argv[2]); out=sys.argv[3]
blob=bytearray(a.binary_blob()); bb=b.binary_blob()
def copy_acc(i):
  acc=b.accessors[i]; bv=b.bufferViews[acc.bufferView]
  data=bb[(bv.byteOffset or 0):(bv.byteOffset or 0)+bv.byteLength]
  while len(blob)%4: blob.append(0)
  off=len(blob); blob.extend(data)
  a.bufferViews.append(pygltflib.BufferView(buffer=0,byteOffset=off,byteLength=len(data),byteStride=bv.byteStride,target=bv.target))
  na=pygltflib.Accessor(**{k:v for k,v in acc.__dict__.items() if k in ('byteOffset','componentType','normalized','count','type','max','min')})
  na.bufferView=len(a.bufferViews)-1; a.accessors.append(na); return len(a.accessors)-1
p=b.meshes[0].primitives[0]; at=p.attributes
prim=pygltflib.Primitive(attributes=pygltflib.Attributes(POSITION=copy_acc(at.POSITION),NORMAL=copy_acc(at.NORMAL),TEXCOORD_0=copy_acc(at.TEXCOORD_0),JOINTS_0=copy_acc(at.JOINTS_0),WEIGHTS_0=copy_acc(at.WEIGHTS_0)),indices=copy_acc(p.indices),material=a.meshes[0].primitives[0].material)
a.meshes.append(pygltflib.Mesh(name='split',primitives=[prim])); a.meshes[0].name='rest'
mn=[i for i,n in enumerate(a.nodes) if n.mesh is not None][0]; a.nodes[mn].name='rest'
a.nodes.append(pygltflib.Node(name='split',mesh=len(a.meshes)-1,skin=a.nodes[mn].skin))
a.scenes[0].nodes.append(len(a.nodes)-1)
a.buffers[0].byteLength=len(blob); a.set_binary_blob(bytes(blob)); a.save(out); print('ok')
