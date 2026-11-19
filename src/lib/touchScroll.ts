import { useEffect, useState } from 'react';

/**
 * Vrai pendant qu'on fait défiler la page au doigt (écran tactile uniquement), et jusqu'à 180 ms après
 * le dernier mouvement (fin de l'élan compris). Les scènes 3D cessent alors de se redessiner : le
 * canevas défile avec la page, géré par le navigateur hors du fil principal, avec sa dernière image.
 * Sur iPhone, chaque rendu WebGL pendant le défilement suffisait à le faire saccader.
 */
const IDLE_MS = 180;

let scrolling = false;
let timer = 0;
let bound = false;
const listeners = new Set<(v: boolean) => void>();

function set(v: boolean) {
  if (v === scrolling) return;
  scrolling = v;
  listeners.forEach((fn) => fn(v));
}

function bump() {
  set(true);
  window.clearTimeout(timer);
  timer = window.setTimeout(() => set(false), IDLE_MS);
}

function bind() {
  if (bound) return;
  bound = true;
  window.addEventListener('scroll', bump, { passive: true });
}

export function useTouchScrolling(enabled = true): boolean {
  const [value, setValue] = useState(false);
  useEffect(() => {
    if (!enabled || !window.matchMedia('(pointer: coarse)').matches) return;
    bind();
    listeners.add(setValue);
    setValue(scrolling);
    return () => {
      listeners.delete(setValue);
      setValue(false);
    };
  }, [enabled]);
  return value;
}
