# Chaîne de fabrication de `public/assets/avatar/avatar.glb`

Outils lancés une fois (pas dans le build). Python 3 avec `trimesh numpy scipy pillow networkx pygltflib`, et `bpy` (Blender en module Python, `pip install bpy`) pour les poids.

1. **Modèle de départ** : Hunyuan3D-2 (Tencent), en local sur le PC d'Ethan (Pinokio, « Hunyuan3D-2 (Full) », profil 32 Go de RAM, 50 étapes, octree 512), à partir du visuel de concept choisi par Ethan. Export GLB avec texture, sans simplification (~40 000 faces).
2. **Retouche de la texture** (la forme n'est jamais touchée) :
   - `python3 improve2.py brut.glb doux.glb` : couleurs lissées à l'intérieur de chaque zone (peau, cheveux, tissu, blanc), bords nets entre zones ;
   - `python3 streak.py doux.glb meche.glb 0.004` : la mèche blanche repeinte sur tout son relief ;
   - `python3 clothfix2.py meche.glb propre.glb 0.26` : taches claires du sweat sous les bras (zones cachées que les bras dévoilent en bougeant).
3. **Poids du squelette** : `python3 -c "import sys;sys.argv=['x','--','propre.glb','poids.npz'];exec(open('bl_weights.py').read())"` (os de `joints.py`, chaleur de Blender après fusion des sommets).
4. **Squelette dans le GLB** : `python3 bake.py propre.glb poids.npz avatar-rig.glb`. Os aux noms de `avatar.js`, rotations nulles au repos, mis à l'échelle (pieds à 0, bassin à 0,667).
5. **Compression** : `npx @gltf-transform/cli optimize avatar-rig.glb avatar.glb --no-simplify --texture-size 2048 --texture-compress webp --compress meshopt`.
6. **Pose assise** : `python3 ik.py` calcule les angles des bras (`SIT_ARM` dans `src/three/avatarGlb.ts`) pour que les poignets tombent sur le clavier du bureau.
