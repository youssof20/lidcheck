import "./fonts.css";
import "./style.css";
import text from "./i18n/en.json";
import manifest from "../public/model/manifest.json";
import {
  analyze,
  failures,
  methods,
  predict,
  type RGB,
  type Method,
  type Model,
} from "./pipeline";
import { syntheticDrift } from "./study";

const app = document.querySelector<HTMLDivElement>("#app")!;
const study = location.hash === "#study";
let population = "older",
  photo: HTMLCanvasElement | null = null,
  pixels: RGB[] = [],
  stream: MediaStream | null = null;
let output: ReturnType<typeof analyze> | null = null,
  synthetic = false,
  resultState = "";
const entries: Record<string, unknown>[] = [];
const t = (key: string): string =>
  String((text as Record<string, unknown>)[key] ?? key);
const escape = (value: string) =>
  value.replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ]!,
  );
const button = (id: string, key: string, secondary = false) =>
  `<button id="${id}" class="${secondary ? "secondary" : ""}" type="button">${t(key)}</button>`;
const eye = `<svg class="eye" viewBox="0 0 300 180" role="img" aria-label="${t("eyeAlt")}"><path d="M25 83Q145 -2 275 83Q155 157 25 83" fill="white" stroke="currentColor" stroke-width="3"/><circle cx="150" cy="65" r="31" fill="#ccd4dc"/><circle cx="150" cy="60" r="14" fill="#1b2430"/><path d="M35 101Q151 166 265 101L252 125Q150 183 48 125Z" fill="none" stroke="#8c2639" stroke-width="4"/><path d="M150 158v17m-6-7 6 7 6-7" fill="none" stroke="#526171" stroke-width="2"/></svg>`;
function shell(body: string) {
  app.innerHTML = `<header><a href="${import.meta.env.BASE_URL}" class="brand">${t("name")}</a><button id="about" class="link" type="button">${t("about")}</button></header><main>${body}</main><footer>${t("footer")}</footer>`;
  document.querySelector("#about")?.addEventListener("click", about);
}
function listen(id: string, fn: () => void) {
  document.getElementById(id)?.addEventListener("click", fn);
}
function announce(message: string) {
  const el = document.getElementById("status");
  if (el) el.textContent = message;
}
function focusHeading() {
  document.querySelector<HTMLElement>("h1")?.focus();
}
function stop() {
  stream?.getTracks().forEach((track) => track.stop());
  stream = null;
}
function reset() {
  stop();
  photo = null;
  pixels = [];
  output = null;
  synthetic = false;
  capture();
}
function banner() {
  return manifest.populations[
    population as keyof typeof manifest.populations
  ] === "validated-in-prototype"
    ? ""
    : `<aside class="demo"><strong>${t("demo")}</strong><p>${t("demoDetail")}</p></aside>`;
}
function capture() {
  shell(`<p class="privacy-line">${t("private")}</p><div class="intro"><div><h1 tabindex="-1">${t(study ? "studyTitle" : "title")}</h1><p class="lead">${t(study ? "studyIntro" : "intro")}</p></div>${eye}</div>
    ${study ? "" : `<fieldset><legend>${t("population")}</legend><label><input type="radio" name="population" value="older" ${population === "older" ? "checked" : ""}>${t("older")}</label><label><input type="radio" name="population" value="child" ${population === "child" ? "checked" : ""}>${t("child")}</label></fieldset><div id="banner">${banner()}</div>`}
    <section class="instruction"><h2>${t("guideTitle")}</h2><p>${t("guide")}</p></section>
    <div class="actions"><label class="button" for="camera-file">${t("take")}</label><input class="file" id="camera-file" type="file" accept="image/*" capture="environment"><label class="button secondary" for="upload">${t("upload")}</label><input class="file" id="upload" type="file" accept="image/*"></div>
    <div class="actions">${button("sample", "sample", true)}${button("live", "live", true)}</div><div id="camera"></div><p id="status" role="status" aria-live="polite"></p>
    <section class="privacy-note"><h2>${t("privacyTitle")}</h2><p>${t("privacy")}</p></section>`);
  document
    .querySelectorAll<HTMLInputElement>("[name=population]")
    .forEach((el) =>
      el.addEventListener("change", () => {
        population = el.value;
        document.getElementById("banner")!.innerHTML = banner();
      }),
    );
  ["camera-file", "upload"].forEach((id) =>
    document.getElementById(id)?.addEventListener("change", (event) => {
      const file = (event.target as HTMLInputElement).files?.[0];
      if (file) void load(file);
    }),
  );
  listen("sample", sample);
  listen("live", () => void live());
}
async function load(file: File) {
  announce(t("processing"));
  let bitmap: ImageBitmap | null = null;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const canvas = document.createElement("canvas"),
      scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas
      .getContext("2d")!
      .drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    process(canvas);
  } catch {
    announce(t("fileError"));
  } finally {
    bitmap?.close();
  }
}
function process(canvas: HTMLCanvasElement) {
  stop();
  photo = canvas;
  const ctx = canvas.getContext("2d")!,
    data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
  pixels = [];
  const n = manifest.image_size;
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++) {
      const i =
        (Math.floor((y * canvas.height) / n) * canvas.width +
          Math.floor((x * canvas.width) / n)) *
        4;
      pixels.push([data[i], data[i + 1], data[i + 2]]);
    }
  output = analyze(pixels, n, manifest.normalization as Method);
  review();
}
function sample() {
  synthetic = true;
  const canvas = document.createElement("canvas");
  canvas.width = 384;
  canvas.height = 288;
  const ctx = canvas.getContext("2d")!;
  ctx.fillStyle = "#9d8e85";
  ctx.fillRect(0, 0, 384, 288);
  ctx.fillStyle = "#e9e7e4";
  ctx.beginPath();
  ctx.ellipse(192, 115, 155, 78, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#46565e";
  ctx.beginPath();
  ctx.arc(192, 85, 54, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#18232c";
  ctx.beginPath();
  ctx.arc(192, 75, 25, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#ba6972";
  ctx.beginPath();
  ctx.ellipse(192, 185, 143, 31, 0, 0, Math.PI * 2);
  ctx.fill();
  for (let x = 70; x < 310; x += 9) {
    ctx.strokeStyle = "#9e5663";
    ctx.beginPath();
    ctx.moveTo(x, 185);
    ctx.lineTo(x + 6, 200);
    ctx.stroke();
  }
  process(canvas);
}
function review() {
  shell(
    `<h1 tabindex="-1">${t("review")}</h1><p>${t("reviewDetail")}</p>${synthetic ? `<p>${t("synthetic")}</p>` : ""}<div class="photo-frame"><canvas id="preview"></canvas></div><div class="actions">${button("confirm", "confirm")}${button("retake", "retake", true)}</div><p id="status" aria-live="polite"></p>`,
  );
  const canvas = document.querySelector<HTMLCanvasElement>("#preview")!;
  canvas.width = photo!.width;
  canvas.height = photo!.height;
  const ctx = canvas.getContext("2d")!;
  ctx.drawImage(photo!, 0, 0);
  const n = manifest.image_size;
  ctx.fillStyle = "rgba(140,38,57,0.65)";
  output!.mask.forEach((v, i) => {
    if (
      v &&
      (i % n === 0 ||
        i % n === n - 1 ||
        i < n ||
        i >= n * (n - 1) ||
        !output!.mask[i - 1] ||
        !output!.mask[i + 1] ||
        !output!.mask[i - n] ||
        !output!.mask[i + n])
    )
      ctx.fillRect(
        ((i % n) * canvas.width) / n,
        (Math.floor(i / n) * canvas.height) / n,
        canvas.width / n,
        canvas.height / n,
      );
  });
  listen("confirm", () => (study ? studyForm() : result()));
  listen("retake", reset);
  focusHeading();
}
function result() {
  const failed = failures(output!.quality, manifest.quality),
    f = output!.features;
  const p = f.every(Number.isFinite) ? predict(f, manifest.model) : NaN;
  const uncertain =
    !Number.isFinite(p) ||
    Math.abs(p - manifest.model.threshold) < manifest.model.band;
  resultState =
    failed.length || uncertain
      ? "inconclusive"
      : p >= manifest.model.threshold
        ? "positive"
        : "negative";
  const scores = Number.isFinite(p)
    ? manifest.ensemble.map((m) => predict(f, m as Model))
    : [];
  const lo = scores.length ? Math.min(p, ...scores) : 0,
    hi = scores.length ? Math.max(p, ...scores) : 1;
  const bars = (label: "0" | "1", y: number) => {
    const a = manifest.density_bands[label],
      max = Math.max(...a, 1);
    return a
      .map(
        (v, i) =>
          `<rect x="${20 + i * 20}" y="${y - (v / max) * 30}" width="19" height="${(v / max) * 30}" fill="${label === "0" ? "#ccd4dc" : "#8997a5"}"/>`,
      )
      .join("");
  };
  shell(`${banner()}${synthetic ? `<p>${t("synthetic")}</p>` : ""}<p>${t("result")}</p><h1 tabindex="-1" aria-live="polite">${t(resultState + "Label")}</h1><p class="lead">${t(resultState)}</p>${failed.map((k) => `<p class="reason">${t(k)}</p>`).join("")}${uncertain && !failed.length ? `<p>${t("uncertain")}</p>` : ""}
    ${Number.isFinite(p) ? `<section class="signal"><h2>${t("scale")}</h2><svg viewBox="0 0 440 125" role="img" aria-label="${t("scale")}">${bars("0", 45)}${bars("1", 85)}<line x1="20" y1="100" x2="420" y2="100" stroke="#526171"/><line x1="${20 + lo * 400}" y1="108" x2="${20 + hi * 400}" y2="108" stroke="#8c2639" stroke-width="3"/><line x1="${20 + p * 400}" y1="15" x2="${20 + p * 400}" y2="113" stroke="#8c2639" stroke-width="3"/><circle cx="${20 + p * 400}" cy="108" r="5" fill="#8c2639"/></svg><div class="scale-labels"><span>${t("scaleLow")}</span><span>${t("scaleHigh")}</span></div><p class="small">${t("nonAnemic")} / ${t("anemic")}</p><p class="small">${t("distribution")}</p></section>` : ""}
    <p>${t("screening")}</p><section id="teach"><h2>${t("teach")}</h2>${[1, 2].map((i) => `<fieldset><legend>${t("q" + i)}</legend><button class="secondary answer" data-q="${i}" data-a="yes">${t("yes")}</button><button class="secondary answer" data-q="${i}" data-a="no">${t("no")}</button><p id="answer-${i}" aria-live="polite"></p></fieldset>`).join("")}${button("skip", "skip", true)}</section>
    <section class="clinician"><h2>${t("summary")}</h2><dl><dt>${t("date")}</dt><dd>${new Date().toLocaleDateString("en-GB")}</dd><dt>${t("version")}</dt><dd>${manifest.version}</dd><dt>${t("scale")}</dt><dd>${t(resultState + "Label")}</dd></dl><h3>${t("quality")}</h3><dl>${Object.entries(
      output!.quality,
    )
      .map(
        ([k, v]) =>
          `<dt>${t(k === "blur" || k === "cohesion" || k === "glare" ? k + "Metric" : k)}</dt><dd>${v.toFixed(5)}</dd>`,
      )
      .join(
        "",
      )}</dl><p>${t("notes")}</p><div class="notes"></div></section><div class="actions">${button("print", "print")}${button("retake", "retake", true)}</div>`);
  document.querySelectorAll<HTMLButtonElement>(".answer").forEach((el) =>
    el.addEventListener("click", () => {
      document.getElementById("answer-" + el.dataset.q)!.textContent = t(
        "a" + el.dataset.q,
      );
    }),
  );
  listen("skip", () => document.getElementById("teach")!.remove());
  listen("print", () => window.print());
  listen("retake", reset);
  focusHeading();
}
function studyForm() {
  shell(
    `<h1 tabindex="-1">${t("studyTitle")}</h1><p>${t("studyIntro")}</p><form id="study-form"><label>${t("participant")}<input id="participant" required maxlength="32" pattern="[A-Za-z0-9_-]+"></label><label>${t("phone")}<input id="phone" required maxlength="80"></label><label>${t("condition")}<select id="condition">${text.conditions.map((c, i) => `<option value="${i}">${c}</option>`).join("")}</select></label><label>${t("shot")}<select id="shot"><option>1</option><option>2</option></select></label>${button("save-study", "saveStudy")}</form><p id="status" aria-live="polite"></p><p>${t("studyCount")}: <span id="count">${entries.length}</span></p><div class="actions">${button("download", "download", true)}${button("retake", "retake", true)}</div>`,
  );
  listen("save-study", () => {
    const field = (id: string) =>
      (document.getElementById(id) as HTMLInputElement).value.trim();
    const participant = field("participant"),
      phone = field("phone"),
      condition = field("condition"),
      shot = field("shot");
    if (
      !(
        document.getElementById("study-form") as HTMLFormElement
      ).reportValidity()
    ) {
      announce(t("studyMissing"));
      return;
    }
    if (
      entries.some(
        (e) =>
          e.participant === participant &&
          e.condition === condition &&
          e.shot === shot,
      )
    ) {
      announce(t("studyDuplicate"));
      return;
    }
    const measurements = Object.fromEntries(
      methods.map((method) => {
        const a = analyze(pixels, manifest.image_size, method);
        const model = (manifest.study_models as Record<string, Model>)[method];
        return [
          method,
          {
            features: a.features.map((v) => (Number.isFinite(v) ? v : null)),
            quality: a.quality,
            rejected: failures(a.quality, manifest.quality).length > 0,
            score:
              a.features.every(Number.isFinite) && model
                ? predict(a.features, model)
                : null,
            synthetic_drift: syntheticDrift(
              pixels,
              manifest.image_size,
              method,
            ),
          },
        ];
      }),
    );
    entries.push({
      participant,
      phone,
      condition,
      shot,
      synthetic,
      model_version: manifest.version,
      measurements,
    });
    announce(t("studySaved"));
    document.getElementById("count")!.textContent = String(entries.length);
  });
  listen("download", () => {
    const url = URL.createObjectURL(
      new Blob([JSON.stringify({ schema: 1, entries }, null, 2)], {
        type: "application/json",
      }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "lidcheck-study.json";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  });
  listen("retake", reset);
  focusHeading();
}
async function live() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
      audio: false,
    });
    const box = document.getElementById("camera")!;
    box.innerHTML = `<div class="live-frame"><video autoplay playsinline muted></video>${eye}</div><div class="actions">${button("snap", "snap")}${button("stop", "stop", true)}</div>`;
    const video = box.querySelector("video")!;
    video.srcObject = stream;
    await video.play();
    listen("stop", () => {
      stop();
      box.innerHTML = "";
    });
    listen("snap", () => {
      const c = document.createElement("canvas");
      const scale = Math.min(
        1,
        1600 / Math.max(video.videoWidth, video.videoHeight),
      );
      c.width = Math.round(video.videoWidth * scale);
      c.height = Math.round(video.videoHeight * scale);
      c.getContext("2d")!.drawImage(video, 0, 0, c.width, c.height);
      process(c);
    });
  } catch {
    stop();
    announce(t("cameraError"));
  }
}
function about() {
  stop();
  shell(
    `<h1 tabindex="-1">${t("about")}</h1><p>${t("aboutText")}</p><p>${t("screening")}</p><pre>${escape(JSON.stringify(manifest, null, 2))}</pre>${button("back", "back", true)}`,
  );
  listen("back", reset);
  focusHeading();
}
window.addEventListener("pagehide", stop);
capture();
