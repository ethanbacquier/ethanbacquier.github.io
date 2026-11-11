// CV en PDF, depuis tools/cv/cv.json (une seule source pour toutes les versions).
//   - 2 styles : « ats » (sobre, une colonne, lisible par les logiciels de tri)
//                « portfolio » (assorti au site, thème clair lavande)
//   - 3 accroches : stage, alternance, site (stage + alternance)
// Sorties : cv/*.pdf (versions ciblées à envoyer) et public/cv/ethan-bacquier-cv.pdf (bouton du site).
// Lancer : node scripts/gen-cv.mjs  (demande Playwright, comme gen-cursors.mjs)
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { frTypo } from './typo.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const data = JSON.parse(readFileSync(join(root, 'tools/cv/cv.json'), 'utf8'));
const buildDir = join(root, 'tools/cv/.build');
const font = (file) => pathToFileURL(join(root, 'node_modules/@fontsource-variable/inter/files', file)).href;

const esc = (s) =>
  frTypo(String(s)).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const fontFace = `
@font-face { font-family: 'Inter'; font-weight: 100 900; font-style: normal;
  src: url('${font('inter-latin-wght-normal.woff2')}') format('woff2'); unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }
@font-face { font-family: 'Inter'; font-weight: 100 900; font-style: normal;
  src: url('${font('inter-latin-ext-wght-normal.woff2')}') format('woff2'); unicode-range: U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF; }
@page { size: A4; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Inter', sans-serif; font-variant-ligatures: none; }
a { color: inherit; text-decoration: none; }
ul { list-style: none; }
`;

const contactItems = (c) => [
  { label: c.email, href: `mailto:${c.email}` },
  { label: c.city },
  { label: c.site, href: `https://${c.site}` },
  { label: c.linkedin, href: `https://www.${c.linkedin}` },
  { label: c.github, href: `https://${c.github}` },
];
const link = (it) => (it.href ? `<a href="${esc(it.href)}">${esc(it.label)}</a>` : esc(it.label));

/* ---------- Version ATS : une colonne, titres standard, texte noir ---------- */
function ats(v) {
  const section = (title, body) => `<section><h2>${esc(title)}</h2>${body}</section>`;
  const entry = (head, date, sub, text) => `
    <div class="entry">
      <div class="row"><h3>${head}${sub ? ` <span class="sub">· ${sub}</span>` : ''}</h3>${date ? `<span class="date">${esc(date)}</span>` : ''}</div>
      ${text ? `<p>${esc(text)}</p>` : ''}
    </div>`;
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>${esc(data.name)} · CV</title>
<style>${fontFace}
body { color: #111; font-size: 9pt; line-height: 1.36; padding: 11mm 15mm 0; }
header { border-bottom: 1.2pt solid #111; padding-bottom: 3.2mm; margin-bottom: 3.6mm; }
h1 { font-size: 22pt; font-weight: 800; letter-spacing: -0.02em; line-height: 1.1; }
.title { font-size: 11.5pt; font-weight: 600; margin-top: 1mm; }
.goal { font-weight: 600; margin-top: 1.6mm; }
.detail { color: #333; }
.contact { margin-top: 1.6mm; color: #222; }
.contact span + span::before { content: ' · '; }
section { margin-top: 2.5mm; }
h2 { font-size: 10pt; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; border-bottom: 0.6pt solid #999; padding-bottom: 0.8mm; margin-bottom: 1.6mm; }
.entry + .entry { margin-top: 1.5mm; }
.row { display: flex; justify-content: space-between; gap: 4mm; align-items: baseline; }
h3 { font-size: 9.8pt; font-weight: 700; }
.date { font-weight: 600; white-space: nowrap; }
.sub { color: #333; font-weight: 400; font-style: italic; }
.skills p + p, .plain p + p { margin-top: 0.8mm; }
b { font-weight: 700; }
</style></head><body>
<header>
  <h1>${esc(data.name)}</h1>
  <p class="title">${esc(v.title)}</p>
  <p class="goal">${esc(v.goal)}</p>
  <p class="detail">${esc(v.detail)}</p>
  <p class="contact">${contactItems(data.contact).map((it) => `<span>${link(it)}</span>`).join('')}</p>
</header>
${section('Profil', `<p>${esc(data.profile)}</p>`)}
${section('Formation', data.education.map((e) => entry(esc(e.title), e.date, esc(e.place), e.text)).join(''))}
${section('Projets', data.projects.map((p) => entry(
    `${esc(p.name)} <span class="sub">· ${esc(p.meta)}${p.link ? ` · ${link({ label: p.link, href: `https://${p.link}` })}` : ''}</span>`,
    null, null, `${p.text} Technologies : ${p.stack.replaceAll(' · ', ', ')}.`)).join(''))}
${section('Expérience', data.experience.map((e) => entry(esc(e.title), e.date, esc(e.place), e.text)).join(''))}
${section('Compétences', `<div class="skills">${data.skills.map((s) => `<p><b>${esc(s.group)} :</b> ${esc(s.items)}</p>`).join('')}</div>`)}
${section('Entraînement et certifications', `<div class="plain">${data.training.map((t) => `<p><b>${esc(t.name)} :</b> ${esc([t.big, t.text].filter(Boolean).join(' · '))}</p>`).join('')}</div>`)}
${section('Langues', `<p>${data.languages.map((l) => `${esc(l.name)} (${esc(l.level)})`).join(' · ')}</p>`)}
${section("Centres d'intérêt", `<p>${data.interests.map(esc).join(' · ')}</p>`)}
</body></html>`;
}

/* ---------- Version portfolio : thème clair lavande du site ---------- */
function portfolio(v) {
  const head = (t) => `<h2>${esc(t)}</h2>`;
  const timeline = (list) => list.map((e) => `
    <div class="item">
      <div class="row"><h3>${esc(e.title)}</h3><span class="date">${esc(e.date)}</span></div>
      <p class="sub">${esc(e.place)}</p>
      ${e.text ? `<p>${esc(e.text)}</p>` : ''}
    </div>`).join('');
  return `<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>${esc(data.name)} · CV</title>
<style>${fontFace}
:root { --bg: #ECE8F6; --card: rgb(255 255 255 / .62); --edge: rgb(255 255 255 / .9); --text: #17121F; --muted: #524B67; --accent: #6025C9; --line: #D6CFEA; }
html, body { width: 210mm; height: 296mm; overflow: hidden; }
body { position: relative; color: var(--text); background: var(--bg); font-size: 9pt; line-height: 1.42; padding: 12mm 12mm 10mm; }
.orb { position: absolute; border-radius: 50%; z-index: -1; }
.orb--a { width: 150mm; height: 150mm; left: -55mm; top: -60mm; background: radial-gradient(circle, color-mix(in srgb, var(--accent) 22%, transparent), transparent 68%); }
.orb--b { width: 140mm; height: 140mm; right: -60mm; top: 70mm; background: radial-gradient(circle, rgb(255 190 160 / .38), transparent 68%); }
.orb--c { width: 160mm; height: 160mm; left: 10mm; bottom: -90mm; background: radial-gradient(circle, rgb(150 160 235 / .32), transparent 68%); }
header { display: flex; gap: 6mm; align-items: center; }
.mono { flex: none; width: 17mm; height: 17mm; border-radius: 5.5mm; background: var(--text); color: #fff; display: grid; place-items: center; font-weight: 800; font-size: 15pt; letter-spacing: -0.04em; }
h1 { font-size: 27pt; font-weight: 800; letter-spacing: -0.04em; line-height: 1; }
.title { font-size: 13pt; font-weight: 700; letter-spacing: -0.02em; color: var(--accent); margin-top: 1.4mm; }
.goal { margin-top: 4mm; background: var(--card); border: 0.6pt solid var(--edge); border-radius: 4mm; padding: 3mm 4.2mm; display: flex; gap: 3mm; align-items: flex-start; box-shadow: 0 1mm 4mm rgb(40 20 80 / .06); }
.dot { flex: none; width: 2.4mm; height: 2.4mm; border-radius: 50%; background: #3FAF7A; margin-top: 1.4mm; box-shadow: 0 0 0 1mm rgb(63 175 122 / .18); }
.goal strong { display: block; font-size: 10pt; font-weight: 700; letter-spacing: -0.01em; }
.goal span { color: var(--muted); }
.grid { display: grid; grid-template-columns: 1fr 66mm; gap: 6mm; margin-top: 4.4mm; }
h2 { font-size: 8.4pt; font-weight: 600; color: var(--muted); margin-bottom: 2mm; display: flex; align-items: center; gap: 2mm; }
h2::after { content: ''; flex: 1; height: 0.6pt; background: var(--line); }
main section + section, aside section + section { margin-top: 4mm; }
.profile { font-size: 9.5pt; line-height: 1.48; }
.project { background: var(--card); border: 0.6pt solid var(--edge); border-radius: 3.6mm; padding: 2.3mm 3.2mm; }
.project + .project { margin-top: 1.8mm; }
.row { display: flex; justify-content: space-between; align-items: baseline; gap: 3mm; }
h3 { font-size: 9.9pt; font-weight: 700; letter-spacing: -0.01em; line-height: 1.3; }
.meta { font-size: 7.8pt; font-weight: 600; color: var(--accent); white-space: nowrap; }
.project p { margin-top: 0.8mm; }
.stack { color: var(--muted); font-size: 8pt; margin-top: 1mm !important; }
.stack a { color: var(--accent); font-weight: 600; }
.item { position: relative; padding-left: 4mm; }
.item::before { content: ''; position: absolute; left: 0; top: 1.5mm; width: 1.6mm; height: 1.6mm; border-radius: 50%; background: var(--accent); }
.item::after { content: ''; position: absolute; left: 0.7mm; top: 3.6mm; bottom: -2.4mm; width: 0.3mm; background: var(--line); }
.item:last-child::after { display: none; }
.item + .item { margin-top: 2.2mm; }
.date { font-weight: 700; color: var(--accent); font-size: 8.4pt; white-space: nowrap; }
.sub { color: var(--muted); font-size: 8.4pt; }
aside { background: var(--card); border: 0.6pt solid var(--edge); border-radius: 4.5mm; padding: 4.2mm 4mm; align-self: start; box-shadow: 0 1mm 4mm rgb(40 20 80 / .06); }
.contact li { word-break: break-word; }
.contact li + li { margin-top: 0.9mm; }
.contact li::before { content: '↗'; color: var(--accent); font-weight: 700; margin-right: 1.6mm; }
.contact li.city::before { content: '●'; font-size: 6pt; vertical-align: 1px; }
.skill + .skill { margin-top: 2.2mm; }
.skill b, .stat b { display: block; font-weight: 700; font-size: 8.6pt; }
.tags { display: flex; flex-wrap: wrap; gap: 1.1mm; margin-top: 1.1mm; }
.tags span { background: color-mix(in srgb, var(--accent) 9%, #fff); color: var(--text); border-radius: 99px; padding: 0.35mm 2mm; font-size: 7.7pt; }
.stat + .stat { margin-top: 1.8mm; }
.stat span { color: var(--muted); }
.tiles { display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 2mm; }
.tile { background: var(--card); border: 0.6pt solid var(--edge); border-radius: 3.6mm; padding: 2.4mm 3mm; display: flex; flex-direction: column; }
.tile__name { font-size: 7.6pt; font-weight: 600; color: var(--muted); }
.tile strong { font-size: 15pt; font-weight: 800; letter-spacing: -0.035em; line-height: 1.15; color: var(--accent); }
.tile strong.small { font-size: 10.5pt; letter-spacing: -0.02em; margin-top: 1mm; }
.tile__text { font-size: 7.6pt; color: var(--muted); line-height: 1.35; margin-top: 0.4mm; }
.edu .item p:not(.sub) { font-size: 8.2pt; }
.exp { display: grid; grid-template-columns: 1fr 1fr; gap: 2mm; }
.exp .date { font-size: 7.8pt; }
.exp p:last-child { margin-top: 0.6mm; }
.edu .date { display: block; font-size: 7.8pt; line-height: 1.2; }
.edu .item::before { top: 0.9mm; }
.edu .item::after { top: 3mm; }
.lang li { display: flex; justify-content: space-between; }
.lang li + li { margin-top: 0.6mm; }
.lang span { color: var(--muted); }
</style></head><body>
<div class="orb orb--a"></div><div class="orb orb--b"></div><div class="orb orb--c"></div>
<header>
  <div class="mono" aria-hidden="true">EB</div>
  <div><h1>${esc(data.name)}</h1><p class="title">${esc(v.title)} · Ynov Lyon</p></div>
</header>
<div class="goal"><i class="dot"></i><div><strong>${esc(v.goal)}</strong><span>${esc(v.detail)}</span></div></div>
<div class="grid">
<main>
  <section>${head('Profil')}<p class="profile">${esc(data.profile)}</p></section>
  <section>${head('Entraînement')}<div class="tiles">${data.training.map((t) => `
    <div class="tile"><span class="tile__name">${esc(t.name)}</span><strong${t.big.length > 10 ? ' class="small"' : ''}>${esc(t.big)}</strong>${t.text ? `<span class="tile__text">${esc(t.text)}</span>` : ''}</div>`).join('')}</div></section>
  <section>${head('Projets')}${data.projects.map((p) => `
    <div class="project">
      <div class="row"><h3>${esc(p.name)}</h3><span class="meta">${esc(p.meta)}</span></div>
      <p>${esc(p.text)}</p>
      <p class="stack">${esc(p.stack)}${p.link ? ` · <a href="https://${esc(p.link)}">${esc(p.link)}</a>` : ''}</p>
    </div>`).join('')}</section>
  <section>${head('Expérience')}<div class="exp">${data.experience.map((e) => `
    <div class="tile"><span class="date">${esc(e.date)}</span><h3>${esc(e.title)}</h3><p class="sub">${esc(e.place)}</p><p>${esc(e.text)}</p></div>`).join('')}</div></section>
</main>
<aside>
  <section>${head('Contact')}<ul class="contact">${contactItems(data.contact)
    .map((it) => `<li${it.href ? '' : ' class="city"'}>${link(it)}</li>`).join('')}</ul></section>
  <section>${head('Formation')}<div class="edu">${data.education.map((e) => `
    <div class="item"><span class="date">${esc(e.date)}</span><h3>${esc(e.title)}</h3><p class="sub">${esc(e.place)}</p>${e.text ? `<p>${esc(e.text)}</p>` : ''}</div>`).join('')}</div></section>
  <section>${head('Compétences')}${data.skills.map((s) => `
    <div class="skill"><b>${esc(s.group)}</b><div class="tags">${s.items.split(', ').map((i) => `<span>${esc(i)}</span>`).join('')}</div></div>`).join('')}</section>
  <section>${head('Langues')}<ul class="lang">${data.languages.map((l) => `<li><b>${esc(l.name)}</b><span>${esc(l.level)}</span></li>`).join('')}</ul></section>
  <section>${head("Centres d'intérêt")}${data.interests.map((i) => `<p>${esc(i)}</p>`).join('')}</section>
</aside>
</div>
</body></html>`;
}

const outputs = [
  ['ats', 'stage', 'cv/ethan-bacquier-cv-ats-stage.pdf'],
  ['ats', 'alternance', 'cv/ethan-bacquier-cv-ats-alternance.pdf'],
  ['portfolio', 'stage', 'cv/ethan-bacquier-cv-stage.pdf'],
  ['portfolio', 'alternance', 'cv/ethan-bacquier-cv-alternance.pdf'],
  ['portfolio', 'site', 'public/cv/ethan-bacquier-cv.pdf'],
];

const { chromium } = createRequire(import.meta.url)('playwright');
mkdirSync(buildDir, { recursive: true });
mkdirSync(join(root, 'cv'), { recursive: true });
mkdirSync(join(root, 'public/cv'), { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 794, height: 1123 } });
await page.emulateMedia({ media: 'print' });
for (const [style, variant, out] of outputs) {
  const html = (style === 'ats' ? ats : portfolio)(data.variants[variant]);
  const file = join(buildDir, `${style}-${variant}.html`);
  writeFileSync(file, html);
  await page.goto(pathToFileURL(file).href);
  await page.evaluate(() => document.fonts.ready);
  const overflow = await page.evaluate(() => Math.max(...[...document.querySelectorAll('body > :not(.orb)')].map((el) => el.getBoundingClientRect().bottom)) > 297 * 96 / 25.4 - 4);
  if (overflow) console.warn(`⚠ ${out} : le contenu dépasse une page A4`);
  await page.pdf({ path: join(root, out), format: 'A4', printBackground: true, preferCSSPageSize: true });
  console.log(`✓ ${out}`);
}
await browser.close();
