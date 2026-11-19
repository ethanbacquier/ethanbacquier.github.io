// Avatar généré par IA (image → 3D), retouché et équipé d'un squelette : fichier public/assets/avatar/avatar.glb.
// Les os portent les mêmes noms que les articulations de l'avatar en code (hips, spine, chest, neck, head,
// uaL/R, laL/R, hL/R, ulL/R, llL/R, fL/R), avec des rotations nulles au repos : les poses de avatar.js
// (idlePose, sitPose, wavePose) s'appliquent telles quelles. Échelle déjà calée au bake : pieds à y = 0,
// bassin à y = 0.667, comme l'avatar en code.
import * as THREE from 'three';
import type { GLTF } from 'three/addons/loaders/GLTFLoader.js';
import type { Avatar } from './avatar.js';

export const AVATAR_GLB = `${import.meta.env.BASE_URL}assets/avatar/avatar.glb`;

export function avatarFromGltf(gltf: GLTF): Avatar {
  const root = new THREE.Group();
  root.name = 'Avatar';
  root.add(gltf.scene);
  const bones: Record<string, THREE.Object3D> = {};
  gltf.scene.traverse((o) => {
    if ((o as THREE.Bone).isBone) bones[o.name] = o;
    const m = o as THREE.SkinnedMesh;
    if (m.isMesh) {
      m.frustumCulled = false; // la boîte englobante d'un maillage animé ne suit pas la pose
      const mat = m.material as THREE.MeshStandardMaterial;
      mat.roughness = 0.62;
      mat.metalness = 0;
    }
  });
  const none = () => {};
  const noFingers = () => ({ fingers: [] as [THREE.Group, THREE.Group][], thumb: [new THREE.Group(), new THREE.Group()] as [THREE.Group, THREE.Group] });
  const limb = (s: 'L' | 'R') => ({
    ua: bones['ua' + s] as THREE.Group, la: bones['la' + s] as THREE.Group, hand: bones['h' + s] as THREE.Group, fingers: noFingers(),
  });
  const leg = (s: 'L' | 'R') => ({ ul: bones['ul' + s] as THREE.Group, ll: bones['ll' + s] as THREE.Group, foot: bones['f' + s] as THREE.Group });
  return {
    root,
    hips: bones.hips as THREE.Group,
    spine: bones.spine as THREE.Group,
    chest: bones.chest as THREE.Group,
    neck: bones.neck as THREE.Group,
    head: bones.head as THREE.Group,
    torso: new THREE.Object3D(), // respiration : portée par le buste (pose), pas par une échelle du torse
    eyes: [],
    arms: { L: limb('L'), R: limb('R') },
    legs: { L: leg('L'), R: leg('R') },
    setGaze: none,
    setBlink: none,
    setSmile: none,
  };
}

type Pose = Record<string, [number, number, number]> & { hipsY: number; breath: number };
const set = (P: Pose, k: string, x: number, y: number, z: number) => { const a = P[k]; a[0] = x; a[1] = y; a[2] = z; };

// Assis en train de taper, pour les proportions de ce modèle (grosse tête, bras courts) : buste presque droit,
// poignets au-dessus du clavier, avant-bras au-dessus du bord du bureau. Angles des bras trouvés par
// optimisation numérique sur ce squelette (à recalculer si le bureau ou le squelette changent).
const SIT_ARM = { ua: [-1.007, -0.196, -0.352], la: [-0.31, -0.172], hand: [0.129, 0.077, 0.332] };
export function sitPoseGlb(t: number, P: Pose) {
  const b = Math.sin(t * 1.7);
  const tapL = Math.max(0, Math.sin(t * 12.3) * Math.sin(t * 3.7 + 1));
  const tapR = Math.max(0, Math.sin(t * 11.1 + 2) * Math.sin(t * 2.9));
  set(P, 'hips', 0, 0, 0);
  set(P, 'spine', 0.06, 0, 0);
  set(P, 'chest', 0.04 + 0.01 * b, 0, 0);
  set(P, 'neck', 0.03, 0, 0);
  set(P, 'head', 0.1 + 0.02 * Math.sin(t * 2.1), 0.05 * Math.sin(t * 0.4), 0);
  for (const [side, sx, tap] of [['L', 1, tapL], ['R', -1, tapR]] as const) {
    const drift = 0.03 * Math.sin(t * 0.7 + sx);
    const { ua, la, hand } = SIT_ARM;
    set(P, 'ua' + side, ua[0], sx * ua[1] + drift, sx * ua[2]);
    set(P, 'la' + side, la[0] - 0.04 * tap, sx * la[1], 0);
    set(P, 'h' + side, hand[0] + 0.12 * tap, sx * hand[1], sx * hand[2]);
  }
  set(P, 'ulL', -1.5, 0, 0.04); set(P, 'ulR', -1.5, 0, -0.04);
  set(P, 'llL', 1.45, 0, 0); set(P, 'llR', 1.45, 0, 0);
  set(P, 'fL', 0.05, 0, 0); set(P, 'fR', 0.05, 0, 0);
  P.hipsY = 0.37;
  P.breath = b;
}

// Salut : main droite levée à côté du visage (la grosse tête cachait la main du salut de l'ancien avatar).
export function wavePoseGlb(t: number, P: Pose, idle: (t: number, P: Pose) => void) {
  idle(t, P);
  const swing = Math.sin(t * 9);
  set(P, 'uaR', -1.2, 0.3 + 0.08 * swing, -0.9);
  set(P, 'laR', -1.1, 0, -0.25 + 0.2 * swing);   // balancement surtout vers l'extérieur : la main ne touche pas la joue
  set(P, 'hR', 0.2, 0, 0.12 * swing);
  set(P, 'head', P.head[0], P.head[1], P.head[2] - 0.05);
}
