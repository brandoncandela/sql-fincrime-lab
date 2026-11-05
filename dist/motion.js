// Entrance motion: sections rise in as they scroll into view, and card groups
// cascade once on first load. Does nothing when the visitor prefers reduced motion.
(() => {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches || !("IntersectionObserver" in window)) return;
  const groups = document.querySelectorAll(".kpis, .cards, .metrics, .metric-strip, .workflow");
  groups.forEach((group) => {
    [...group.children].forEach((child, i) => child.style.setProperty("--i", i));
    group.classList.add("mo-stagger");
    // Stop the cascade after the first run so live updates don't replay it.
    setTimeout(() => group.classList.remove("mo-stagger"), 1500);
  });
  const sections = [...document.querySelectorAll("main section, body > section")].filter((s) => !s.parentElement.closest("section"));
  const io = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    entry.target.classList.add("mo-in");
    io.unobserve(entry.target);
  }), { threshold: 0.08 });
  sections.forEach((section) => { section.classList.add("mo"); io.observe(section); });
})();
