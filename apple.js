// Shared motion for the portfolio demos: blocks fade up as they scroll into view
// and cards lift on hover. Selectors come from data-reveal / data-lift on the script tag.
// Does nothing for visitors who prefer reduced motion.
(() => {
  const me = document.currentScript;
  const revealSel = me?.dataset.reveal || "";
  const liftSel = me?.dataset.lift || "";
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const apply = () => {
    if (liftSel) document.querySelectorAll(liftSel).forEach((el) => el.classList.add("ap-lift"));
    if (reduced || !revealSel || !("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver((entries) => entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add("ap-in");
      io.unobserve(e.target);
    }), { threshold: 0.06, rootMargin: "0px 0px -40px 0px" });
    document.querySelectorAll(revealSel).forEach((el, i) => {
      if (el.classList.contains("ap-reveal")) return;
      const box = el.getBoundingClientRect();
      if (box.top < innerHeight) { el.style.transitionDelay = Math.min(i, 6) * 60 + "ms"; }
      el.classList.add("ap-reveal");
      io.observe(el);
    });
  };
  // Run after the page's own scripts have rendered their content.
  if (document.readyState === "complete") setTimeout(apply, 50);
  else addEventListener("load", () => setTimeout(apply, 50));
})();
