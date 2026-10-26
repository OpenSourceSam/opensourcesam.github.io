// Timeline line that fills as you scroll, and gentle reveals. Content is visible without JavaScript.
(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  // Still mode: reduced motion or no IntersectionObserver. Everything is visible without JavaScript.
  var still = reduce || !('IntersectionObserver' in window);
  var items = [].slice.call(document.querySelectorAll('.reveal'));
  var lines = [].slice.call(document.querySelectorAll('[data-fill]'));
  function showAll() { items.forEach(function (el) { el.classList.add('in'); }); }
  if (still) { root.classList.add('still'); showAll(); }
  else {
    root.classList.add('anim');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.05 });
    items.forEach(function (el) {
      if (el.getBoundingClientRect().top < window.innerHeight * 0.95) el.classList.add('in'); else io.observe(el);
    });
    window.addEventListener('beforeprint', showAll);
  }
  var ticking = false;
  function fill() {
    ticking = false;
    lines.forEach(function (tl) {
      var r = tl.getBoundingClientRect();
      var p = still ? 1 : (window.innerHeight * 0.6 - r.top) / r.height;
      tl.style.setProperty('--fill', Math.min(1, Math.max(0, p)).toFixed(4));
    });
  }
  fill();
  if (!still) {
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(fill); } }, { passive: true });
    window.addEventListener('resize', fill);
  }
})();
