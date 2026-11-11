import { useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';

/**
 * Résolution adaptative : si la scène n'arrive plus à suivre la fréquence de l'écran, on baisse un peu
 * sa résolution (DPR) pour garder le maximum d'images par seconde ; on la remonte quand ça va mieux.
 * Sur une machine qui suit sans peine, rien ne change (netteté pleine).
 * - Mesure par fenêtres d'environ 1 s, en ignorant les pauses (canevas en « never », onglet caché).
 * - Nombre de changements limité : pas de va-et-vient qui ferait clignoter la scène.
 * À n'utiliser que dans un canevas qui dessine en continu (frameloop « always »).
 */
const RATES = [60, 75, 90, 100, 120, 144, 165, 240];

export function AdaptiveDpr({ max, min, step = 0.25 }: { max: number; min: number; step?: number }) {
  const setDpr = useThree((s) => s.setDpr);
  const m = useRef({ dpr: max, frames: 0, time: 0, best: 0, refresh: 60, low: 0, high: 0, changes: 0 });

  useEffect(() => {
    m.current.dpr = max;
  }, [max]);

  useFrame((_, delta) => {
    const s = m.current;
    if (delta > 0.25) return; // reprise après une pause : pas une vraie image lente
    s.frames++;
    s.time += delta;
    if (s.time < 1) return;
    const fps = s.frames / s.time;
    s.frames = 0;
    s.time = 0;
    // Fréquence de l'écran : la meilleure cadence vue, arrondie à la fréquence courante au-dessus
    // (une scène qui plafonne à 40 i/s sur un écran 60 Hz doit quand même être vue comme lente)
    s.best = Math.max(s.best, fps);
    s.refresh = RATES.find((r) => r >= s.best * 0.97) ?? 240;
    if (s.changes >= 6) return;

    if (fps < s.refresh * 0.85) {
      s.low++;
      s.high = 0;
    } else if (fps > s.refresh * 0.95) {
      s.high++;
      s.low = 0;
    } else {
      s.low = 0;
      s.high = 0;
    }

    if (s.low >= 2 && s.dpr > min) {
      s.dpr = Math.max(min, s.dpr - step);
      s.low = 0;
      s.changes++;
      setDpr(s.dpr);
    } else if (s.high >= 5 && s.dpr < max) {
      s.dpr = Math.min(max, s.dpr + step);
      s.high = 0;
      s.changes++;
      setDpr(s.dpr);
    }
  });
  return null;
}
