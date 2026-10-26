// The island from Circe's Garden as a small 3D model. three.js only.
// The top of the slab is the game's real map render; Circe, Hermes and the pig are the game's own sprites.
import * as THREE from "three";

const PLAY_URL = "#game";
const host = document.getElementById("diorama");
const box = document.getElementById("dio");
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, powerPreference: "low-power" });
} catch (err) {
  box.classList.add("no-webgl");
  throw err;
}
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
host.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
camera.position.set(0, 7.4, 9.2);
camera.lookAt(0, -0.3, 0);

const group = new THREE.Group();
scene.add(group);

const loader = new THREE.TextureLoader();
function pixelTexture(url) {
  const t = loader.load(url, () => render());
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.LinearFilter;
  t.generateMipmaps = false;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// The map crop is 544 x 704 px; one unit here is 100 px.
const W = 5.44, D = 7.04, H = 0.42;
const top = new THREE.MeshBasicMaterial({ map: pixelTexture("assets/island_top.png") });
const side = new THREE.MeshBasicMaterial({ color: 0x2b1d14 });
const bottom = new THREE.MeshBasicMaterial({ color: 0x14100c });
const slab = new THREE.Mesh(new THREE.BoxGeometry(W, H, D), [side, side, top, bottom, side, side]);
group.add(slab);

// A thin lighter rim so the edge reads as a cliff.
const rim = new THREE.Mesh(new THREE.BoxGeometry(W + 0.02, 0.06, D + 0.02), new THREE.MeshBasicMaterial({ color: 0x4a6b4a }));
rim.position.y = H / 2 - 0.03;
group.add(rim);

// Soft glow under the island.
function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(128, 128, 10, 128, 128, 128);
  grad.addColorStop(0, "rgba(65,224,255,0.55)");
  grad.addColorStop(0.5, "rgba(65,224,255,0.14)");
  grad.addColorStop(1, "rgba(65,224,255,0)");
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
const glow = new THREE.Mesh(
  new THREE.PlaneGeometry(W * 2.4, D * 1.9),
  new THREE.MeshBasicMaterial({ map: glowTexture(), transparent: true, depthWrite: false })
);
glow.rotation.x = -Math.PI / 2;
glow.position.y = -H / 2 - 0.35;
group.add(glow);

// Characters as billboards standing on the map. px, py are pixels on the map crop.
const sprites = [];
function stand(url, px, py, name, size = 1.0) {
  const m = new THREE.SpriteMaterial({ map: pixelTexture(url), transparent: true, alphaTest: 0.05 });
  const s = new THREE.Sprite(m);
  s.scale.set(size, size, 1);
  s.position.set(px / 100 - W / 2, H / 2 + size * 0.46, py / 100 - D / 2);
  s.name = name;
  s.userData.baseY = s.position.y;
  s.userData.phase = Math.random() * Math.PI * 2;
  group.add(s);
  sprites.push(s);
  return s;
}
const circe = stand("assets/circe.png", 300, 340, "circe", 1.05);
stand("assets/hermes.png", 395, 300, "hermes", 1.05);
stand("assets/pig.png", 150, 430, "pig", 0.9);

// Interaction: drag to turn, click Circe to play.
let yaw = -0.35, yawVel = 0, dragging = false, lastX = 0, downX = 0, downY = 0;
let targetTiltX = 0, targetTiltZ = 0;
host.addEventListener("pointerdown", (e) => {
  dragging = true; lastX = e.clientX; downX = e.clientX; downY = e.clientY;
  host.classList.add("grabbing"); host.setPointerCapture(e.pointerId);
});
host.addEventListener("pointermove", (e) => {
  if (dragging) { const dx = e.clientX - lastX; lastX = e.clientX; yawVel = dx * 0.004; yaw += yawVel; render(); }
  else if (!reduce) {
    const r = host.getBoundingClientRect();
    targetTiltX = ((e.clientY - r.top) / r.height - 0.5) * 0.12;
    targetTiltZ = ((e.clientX - r.left) / r.width - 0.5) * -0.08;
  }
});
function endDrag(e) {
  if (!dragging) return;
  dragging = false; host.classList.remove("grabbing");
  const moved = Math.hypot(e.clientX - downX, e.clientY - downY);
  if (moved < 6) click(e);
}
host.addEventListener("pointerup", endDrag);
host.addEventListener("pointercancel", endDrag);
host.addEventListener("pointerleave", () => { targetTiltX = 0; targetTiltZ = 0; });

const ray = new THREE.Raycaster();
const ndc = new THREE.Vector2();
function click(e) {
  const r = host.getBoundingClientRect();
  ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObject(circe, false);
  if (hit.length) window.location.href = PLAY_URL;
}
host.addEventListener("keydown", (e) => {
  if (e.key === "ArrowLeft") { yaw -= 0.15; render(); }
  if (e.key === "ArrowRight") { yaw += 0.15; render(); }
  if (e.key === "Enter") window.location.href = PLAY_URL;
});
host.tabIndex = 0;

function resize() {
  const w = host.clientWidth, h = host.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  const k = Math.max(1, 1.25 / camera.aspect);
  camera.position.set(0, 7.4 * k * 0.95, 9.2 * k);
  camera.lookAt(0, -0.3, 0);
  render();
}
window.addEventListener("resize", resize);

let tiltX = 0, tiltZ = 0, last = performance.now();
function render() { renderer.render(scene, camera); }
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (!dragging) { yaw += 0.1 * dt + yawVel; yawVel *= 0.92; }
  tiltX += (targetTiltX - tiltX) * 0.06;
  tiltZ += (targetTiltZ - tiltZ) * 0.06;
  group.rotation.set(tiltX, yaw, tiltZ);
  group.position.y = Math.sin(now * 0.0007) * 0.06;
  for (const s of sprites) s.position.y = s.userData.baseY + Math.max(0, Math.sin(now * 0.003 + s.userData.phase)) * 0.025;
  render();
  requestAnimationFrame(frame);
}
resize();
if (reduce) {
  group.rotation.set(0, yaw, 0);
  render();
} else {
  requestAnimationFrame(frame);
}
