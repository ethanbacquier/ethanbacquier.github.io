import bpy, sys, numpy as np
sys.path.insert(0,'.')
from joints import J
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src, merge_vertices=False)
mesh=[o for o in bpy.context.scene.objects if o.type=='MESH'][0]
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True); bpy.context.view_layer.objects.active=mesh
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0015)
bpy.ops.mesh.delete_loose()
bpy.ops.object.mode_set(mode='OBJECT')
print('verts after merge',len(mesh.data.vertices))
B=lambda p:(p[0],-p[2],p[1])
arm=bpy.data.armatures.new('rig'); ao=bpy.data.objects.new('rig',arm); bpy.context.scene.collection.objects.link(ao)
bpy.context.view_layer.objects.active=ao; bpy.ops.object.mode_set(mode='EDIT')
for n,(p,h,t) in J.items():
  b=arm.edit_bones.new(n); b.head=B(h); b.tail=B(t)
for n,(p,h,t) in J.items():
  if p: arm.edit_bones[n].parent=arm.edit_bones[p]
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); ao.select_set(True)
bpy.context.view_layer.objects.active=ao
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
names=list(J); V=len(mesh.data.vertices)
W=np.zeros((V,len(names)),np.float32)
gi={g.index:names.index(g.name) for g in mesh.vertex_groups}
co=np.zeros((V,3))
for v in mesh.data.vertices:
  co[v.index]=(v.co.x,v.co.z,-v.co.y)
  for g in v.groups: W[v.index,gi[g.group]]=g.weight
print('unweighted',(W.sum(1)==0).sum(),'of',V)
np.savez(out,co=co,W=W,names=np.array(names))
