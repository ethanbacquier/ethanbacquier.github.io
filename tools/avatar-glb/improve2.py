# Retouche douce : forme d'origine intacte ; texture = couleurs d'origine lissées À L'INTÉRIEUR de chaque zone
# (peau, cheveux, tissu, blanc), frontières nettes entre zones. Les nuances restent, les bavures partent.
import sys, numpy as np, trimesh
from PIL import Image, ImageFilter
from scipy import ndimage
src, dst = sys.argv[1], sys.argv[2]
S1 = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5     # lissage dans les zones
m = list(trimesh.load(src).geometry.values())[0]
tex = m.visual.material.baseColorTexture.convert('RGB')
a = np.asarray(tex).astype(np.float32) / 255
H, W, _ = a.shape
med = np.asarray(tex.filter(ImageFilter.MedianFilter(5))).astype(np.float32) / 255
r_, g_, b_ = med[..., 0], med[..., 1], med[..., 2]
lum = 0.3 * r_ + 0.59 * g_ + 0.11 * b_; warm = r_ - b_
K = 4
lab = np.zeros((H, W), int)
lab[(lum < 0.3) & (warm > 0.035)] = 1
lab[((warm > 0.1) & (lum > 0.3)) | ((lum > 0.55) & (warm >= 0.09))] = 2
lab[(lum > 0.6) & (warm < 0.09)] = 3
oh = np.stack([ndimage.gaussian_filter((lab == k).astype(np.float32), 2.0) for k in range(K)])
lab = oh.argmax(0)
def absorb(lab, k, maxpx):
    cc, n = ndimage.label(lab == k)
    if n == 0: return lab
    sizes = ndimage.sum(np.ones_like(cc), cc, range(1, n + 1))
    for i, sz in enumerate(sizes, 1):
        if sz >= maxpx: continue
        reg = cc == i
        ring = ndimage.binary_dilation(reg, iterations=3) & ~reg
        vals = lab[ring]; vals = vals[vals != k]
        if len(vals): lab[reg] = np.bincount(vals, minlength=K).argmax()
    return lab
lab = absorb(lab, 3, 2500); lab = absorb(lab, 2, 1500); lab = absorb(lab, 1, 150); lab = absorb(lab, 0, 150)
# bords des yeux et des sourcils : les pixels de peau sombres collés à une zone foncée passent dans la zone foncée
dark = (lab <= 1)
near = ndimage.binary_dilation(dark, iterations=6)
fix = (lab == 2) & near & (lum < 0.52)
lab[fix] = np.where(ndimage.binary_dilation(lab == 1, iterations=6)[fix], 1, 0)
# et inversement : pixels clairs bavant dans les yeux → peau
fix2 = (lab <= 1) & (lum > 0.5) & (warm > 0.1)
lab[fix2] = 2
oh = np.stack([ndimage.gaussian_filter((lab == k).astype(np.float32), 1.2) for k in range(K)])
lab = oh.argmax(0)
# couleur de chaque zone : convolution normalisée (moyenne des seuls pixels de la zone)
out = np.zeros_like(a)
for k in range(K):
    mk = (lab == k).astype(np.float32)
    num = np.stack([ndimage.gaussian_filter(med[..., c] * mk, S1) for c in range(3)], -1)
    den = ndimage.gaussian_filter(mk, S1)[..., None]
    col = num / np.maximum(den, 1e-4)
    if k == 3: col = np.maximum(col, 0.86)               # mèche et baskets : blanc propre
    out[mk > 0] = col[mk > 0]
# frontières anti-crénelées (rendu en 4096)
big = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((2048, 2048), Image.LANCZOS)
newtex = big
newtex.save(dst.replace('.glb', '-tex.png'))
m.visual.material = trimesh.visual.material.PBRMaterial(baseColorTexture=newtex, metallicFactor=0.0, roughnessFactor=0.6)
trimesh.Scene(m).export(dst)
