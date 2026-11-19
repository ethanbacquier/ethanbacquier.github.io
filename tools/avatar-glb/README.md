# Chaîne de fabrication de `public/assets/avatar/avatar.glb`

Outils lancés une fois (pas dans le build). Python 3 avec `trimesh numpy scipy pillow networkx pygltflib`, et `bpy` (Blender en module Python, `pip install bpy`) pour les poids.

1. **Modèle de départ** : Hunyuan3D-2 (Tencent), en local sur le PC d'Ethan (Pinokio, « Hunyuan3D-2 (Full) », profil 32 Go de RAM, 50 étapes, octree 512), à partir du visuel de concept choisi par Ethan. Export GLB avec texture, sans simplification (~40 000 faces).
2. **Retouche de la texture** (la forme n'est jamais touchée) :
   - `python3 improve2.py brut.glb doux.glb` : couleurs lissées à l'intérieur de chaque zone (peau, cheveux, tissu, blanc), bords nets entre zones ;
   - `python3 streak.py doux.glb meche.glb 0.004` : la mèche blanche repeinte sur tout son relief ;
   - `python3 clothfix2.py meche.glb propre.glb 0.26` : taches claires du sweat sous les bras (zones cachées que les bras dévoilent en bougeant).
3. **Poids du squelette** : `python3 -c "import sys;sys.argv=['x','--','propre.glb','poids.npz'];exec(open('bl_weights.py').read())"` (os de `joints.py`, chaleur de Blender après fusion des sommets).
4. **Bras séparés du corps** : `python3 cut.py 1.0 coupe.glb 15` (lit le modèle et `w_heat.npz` comme `sitmeasure.py`, écrit `w_cut.npz`). Le modèle IA soude la main à la cuisse et l'avant-bras à la taille : bras levé, ces faces s'étiraient en « filet » et montraient la peau. Sous l'aisselle (y < 1,0), poids francs, faces de jonction doublées (une copie suit le corps, l'autre le bras, rien ne change au repos) et bords cousus (bouchons couleur sweat arrondis autour de l’axe du bras pour garder le volume de la manche, cachés au repos).
5. **Squelette dans le GLB** : `python3 bake.py coupe.glb w_cut.npz avatar-rig.glb`. Os aux noms de `avatar.js`, rotations nulles au repos, mis à l'échelle (pieds à 0, bassin à 0,667).
6. **Compression** : `npx @gltf-transform/cli optimize avatar-rig.glb avatar.glb --no-simplify --texture-size 2048 --texture-compress webp --compress meshopt`.
7. **Pose assise** : `python3 ik.py` calcule les angles des bras (`SIT_ARM` dans `src/three/avatarGlb.ts`) pour que les poignets tombent sur le clavier du bureau.
