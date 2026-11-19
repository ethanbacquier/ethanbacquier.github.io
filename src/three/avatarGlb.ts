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
  const meshes: Record<string, THREE.Object3D> = {};
  gltf.scene.traverse((o) => {
    if ((o as THREE.Bone).isBone) bones[o.name] = o;
    const m = o as THREE.SkinnedMesh;
    if (m.isMesh) {
      meshes[o.name] = o;
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
    // Trois maillages sur le même squelette (tools/avatar-glb/merge.py) : « rest » (maillage d'origine, parfait bras
    // le long du corps), « splitR » (bras droit séparé du corps : salut) et « split » (les deux bras : assis).
    // Un bras séparé laisse une fente s'il reste le long du corps : on ne sépare que les bras qui s'en écartent.
    setSplit: (mode: 'rest' | 'R' | 'both') => {
      if (!meshes.rest) return;
      const pick = mode === 'both' ? meshes.split : mode === 'R' ? meshes.splitR : meshes.rest;
      const shown = pick ?? meshes.rest;
      for (const k of ['rest', 'splitR', 'split']) if (meshes[k]) meshes[k].visible = meshes[k] === shown;
    },
  };
}

type Pose = Record<string, [number, number, number]> & { hipsY: number; breath: number };
const set = (P: Pose, k: string, x: number, y: number, z: number) => { const a = P[k]; a[0] = x; a[1] = y; a[2] = z; };

const smooth = (x: number) => { const c = Math.min(1, Math.max(0, x)); return c * c * (3 - 2 * c); };
// Hasard déterministe (même animation à chaque visite, aucune allocation).
const hash = (n: number) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
// Rafales de frappe : ~0 pendant les pauses (relire l'écran), ~1 pendant la saisie.
function typingActivity(t: number) {
  const n = 0.5 + 0.35 * Math.sin(t * 0.37) + 0.25 * Math.sin(t * 0.91 + 1.3);
  return smooth((n - 0.3) / 0.25);
}
// Pression d'une touche (0 → 1 → 0 en ~0,25 s, courbes douces : pas d'à-coup), à des instants tirés au hasard sur une grille de 0,15 s :
// rythme irrégulier, jamais mécanique, et décalé d'une main à l'autre (graine différente).
function keyPress(t: number, seed: number) {
  const step = 0.15, k = Math.floor(t / step);
  let d = 0;
  for (let j = k - 2; j <= k; j++) {
    if (hash(j * 1.618 + seed) > 0.5) continue;                   // une case sur deux environ : pas de frappe
    const t0 = (j + 0.7 * hash(j + seed * 3.7)) * step, u = t - t0;
    if (u < 0 || u > 0.3) continue;
    const env = u < 0.07 ? smooth(u / 0.07) : Math.exp(-(u - 0.07) * 16);  // enfoncée en douceur, relâchée plus lentement
    d += env * (0.55 + 0.45 * hash(j * 2.3 + seed));
  }
  return Math.min(1, d);
}

// Assis en train de taper, pour les proportions de ce modèle (grosse tête, bras courts) : buste presque droit,
// poignets au-dessus du clavier, avant-bras au-dessus du bord du bureau. Angles des bras trouvés par
// optimisation numérique sur ce squelette (tools/avatar-glb/ik.py, à recalculer si le bureau ou le squelette
// changent) ; hauteurs mesurées sur le maillage déformé (tools/avatar-glb/sitmeasure.py).
const SIT_ARM = { ua: [-1.17, -0.089, -0.371], la: [-0.042, -0.157], hand: [-0.007, 0.03, 0.348] };
export function sitPoseGlb(t: number, P: Pose) {
  const b = Math.sin(t * 1.7);
  set(P, 'hips', 0, 0, 0);
  set(P, 'spine', 0.06, 0, 0);
  set(P, 'chest', 0.04 + 0.01 * b, 0.03 * Math.sin(t * 0.9), 0);   // le buste suit un peu les mains
  set(P, 'neck', 0.03, 0, 0);
  set(P, 'head', 0.1 + 0.02 * Math.sin(t * 2.1), 0.05 * Math.sin(t * 0.4), 0);
  const act = typingActivity(t);
  for (const [side, sx, seed] of [['L', 1, 0], ['R', -1, 5.3]] as const) {
    // Frappe réaliste sans doigts articulés : les mains restent posées au-dessus des touches, chaque touche est
    // une petite pression rapide du poignet (quelques degrés), à des instants irréguliers, par rafales, avec des
    // pauses où les mains se reposent. Les mains se déplacent à peine sur le clavier, lentement.
    const press = act * keyPress(t, seed);
    const drift = 0.025 * Math.sin(t * 0.31 + seed) + 0.012 * Math.sin(t * 0.83 + seed * 2);
    const reach = 0.015 * Math.sin(t * 0.47 + seed * 3);
    const rest = 1 - act;                                    // en pause, poignets un peu plus bas et détendus
    const { ua, la, hand } = SIT_ARM;
    set(P, 'ua' + side, ua[0] - reach + 0.02 * rest, sx * (ua[1] + drift), sx * ua[2]);
    set(P, 'la' + side, la[0] + reach + 0.02 * press, sx * la[1], 0);
    set(P, 'h' + side, hand[0] + 0.075 * press + 0.05 * rest, sx * (hand[1] + 0.03 * Math.sin(t * 0.6 + seed)), sx * hand[2]);
  }
  set(P, 'ulL', -1.5, 0, 0.04); set(P, 'ulR', -1.5, 0, -0.04);
  set(P, 'llL', 1.45, 0, 0); set(P, 'llR', 1.45, 0, 0);
  set(P, 'fL', 0.05, 0, 0); set(P, 'fR', 0.05, 0, 0);
  P.hipsY = 0.435;   // fesses et cuisses sur l'assise (DESK_LAYOUT.seat), pieds au sol
  P.breath = b;
}

// Salut : avant-bras levé, main à hauteur d'épaule à côté du visage, bras presque le long du corps (lever tout
// le bras étirait le sweat sous l'aisselle et sortait de l'emplacement).
export function wavePoseGlb(t: number, P: Pose, idle: (t: number, P: Pose) => void) {
  idle(t, P);
  const swing = Math.sin(t * 9);
  set(P, 'uaR', -0.5 + 0.04 * swing, 0, -0.15);                  // haut du bras contre le flanc : rien ne s'ouvre sous l'aisselle
  set(P, 'laR', -1.95, 0, -0.22 + 0.17 * swing);                 // avant-bras levé qui balance, sans passer devant le menton
  set(P, 'hR', 0, 0.3, 0.15 * swing);
  set(P, 'head', P.head[0], P.head[1], P.head[2] - 0.05);
}

// Mélange de deux rotations par le plus court chemin (quaternions) : un mélange angle par angle faisait passer
// le bras du salut très loin sur le côté, hors du cadre, en étirant l'aisselle. Écrit le résultat dans a.
const qa = new THREE.Quaternion(), qb = new THREE.Quaternion(), ea = new THREE.Euler(), eb = new THREE.Euler();
export function slerpJoint(a: [number, number, number], b: [number, number, number], w: number) {
  qa.setFromEuler(ea.set(a[0], a[1], a[2]));
  qb.setFromEuler(eb.set(b[0], b[1], b[2]));
  ea.setFromQuaternion(qa.slerp(qb, w));
  a[0] = ea.x; a[1] = ea.y; a[2] = ea.z;
}

// Entrée et sortie du salut en deux temps : l'avant-bras se plie d'abord (la main remonte devant le buste),
// puis le bras se lève. Sans ça, le bras tendu passait loin sur le côté, hors de l'emplacement de l'avatar.
export function blendWave(idle: Pose, wave: Pose, ww: number) {
  const fold = smooth(ww / 0.45), lift = smooth((ww - 0.3) / 0.7);
  slerpJoint(idle.laR, wave.laR, fold);
  slerpJoint(idle.hR, wave.hR, fold);
  slerpJoint(idle.uaR, wave.uaR, lift);
  slerpJoint(idle.head, wave.head, ww);
}
