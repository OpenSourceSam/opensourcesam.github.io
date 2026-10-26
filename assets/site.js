// Starfield behind the hero, and small accessibility helpers. No dependencies.
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Reduced motion: show a still instead of the animated clip.
  var clip = document.getElementById("clip");
  if (clip && reduce && clip.dataset.still) clip.src = clip.dataset.still;

  var canvas = document.getElementById("stars");
  if (!canvas) return;
  var ctx = canvas.getContext("2d");
  var stars = [], w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
  var mx = 0, my = 0;

  function size() {
    w = canvas.clientWidth; h = canvas.clientHeight;
    canvas.width = Math.floor(w * dpr); canvas.height = Math.floor(h * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var n = Math.floor((w * h) / 6500);
    stars = [];
    for (var i = 0; i < n; i++) {
      stars.push({ x: Math.random() * w, y: Math.random() * h, r: 0.4 + Math.random() * 1.3,
        p: Math.random() * Math.PI * 2, s: 0.4 + Math.random() * 0.8, d: 0.3 + Math.random() * 0.7,
        c: Math.random() < 0.15 ? "#cfeaff" : "#ffffff" });
    }
  }

  function draw(t) {
    ctx.clearRect(0, 0, w, h);
    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      var tw = reduce ? 0.8 : 0.55 + 0.45 * Math.sin(t * 0.001 * s.s + s.p);
      var x = s.x + mx * 12 * s.d, y = s.y + my * 12 * s.d;
      ctx.globalAlpha = tw * 0.9;
      ctx.fillStyle = s.c;
      ctx.beginPath(); ctx.arc(x, y, s.r, 0, Math.PI * 2); ctx.fill();
    }
    ctx.globalAlpha = 1;
    if (!reduce) requestAnimationFrame(draw);
  }

  window.addEventListener("resize", function () { size(); if (reduce) draw(0); });
  if (!reduce) {
    window.addEventListener("pointermove", function (e) {
      mx = (e.clientX / window.innerWidth - 0.5); my = (e.clientY / window.innerHeight - 0.5);
    }, { passive: true });
  }
  size();
  draw(0);
})();
