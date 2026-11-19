import sys, numpy as np, trimesh
from PIL import Image, ImageDraw
src, dst, T = sys.argv[1], sys.argv[2], float(sys.argv[3])
m = list(trimesh.load(src).geometry.values())[0]
tex = m.visual.material.baseColorTexture.convert('RGB'); W, H = tex.size
a = np.asarray(tex).astype(np.float32) / 255
uv = np.asarray(m.visual.uv); F = np.asarray(m.faces)
uvf = uv[F].mean(1)
px = np.clip((uvf[:, 0] * (W - 1)).astype(int), 0, W - 1); py = np.clip(((1 - uvf[:, 1]) * (H - 1)).astype(int), 0, H - 1)
c = a[py, px]; lum = c @ [0.3, 0.59, 0.11]; warm = c[:, 0] - c[:, 2]
v = np.asarray(m.vertices); key = np.round(v, 6); uq, inv = np.unique(key, axis=0, return_inverse=True); inv = inv.ravel()
w = trimesh.Trimesh(uq, inv[F], process=False)
sm = w.copy(); trimesh.smoothing.filter_laplacian(sm, lamb=0.5, iterations=60)
disp = np.einsum('ij,ij->i', w.vertices - sm.vertices, w.vertex_normals)
fdisp = disp[w.faces].mean(1)
cen = w.triangles_center
head = cen[:, 1] > 0.35
white = head & (lum > 0.6) & (warm < 0.12)
# plus grande composante blanche sur la tête = la mèche
adj = w.face_adjacency
import networkx as nx
G = nx.Graph(); G.add_edges_from(adj[white[adj[:, 0]] & white[adj[:, 1]]])
comps = sorted(nx.connected_components(G), key=len, reverse=True)
seed = set(comps[0]); print('streak faces', len(seed), 'center', cen[list(seed)].mean(0).round(3))
sc = cen[list(seed)].mean(0); rad = np.linalg.norm(cen[list(seed)] - sc, axis=1).max()
# croissance : faces voisines en relief (au-dessus de la surface lissée), pas trop loin de la mèche
grow = set(seed); frontier = set(seed)
nbrs = [[] for _ in range(len(w.faces))]
for i, j in adj: nbrs[i].append(j); nbrs[j].append(i)
while frontier:
    nf = set()
    for f in frontier:
        for g in nbrs[f]:
            if g in grow: continue
            if fdisp[g] > T and np.linalg.norm(cen[g] - sc) < rad * 1.35 and lum[g] > 0.25 and warm[g] > -1:
                nf.add(g)
    grow |= nf; frontier = nf
add = np.array(sorted(grow - seed)); print('added', len(add))
# repeint ces faces en blanc dans la texture (avec un petit débord)
img = tex.copy(); d = ImageDraw.Draw(img)
white_col = tuple((np.median(c[list(seed)], axis=0) * 255).astype(int))
for f in np.r_[add, np.array(list(seed))].astype(int):
    pts = [(uv[k, 0] * W, (1 - uv[k, 1]) * H) for k in F[f]]
    d.polygon(pts, fill=white_col, outline=white_col)
m.visual.material = trimesh.visual.material.PBRMaterial(baseColorTexture=img, metallicFactor=0.0, roughnessFactor=0.6)
trimesh.Scene(m).export(dst)
