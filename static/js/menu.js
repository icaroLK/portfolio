// Mobile menu: the button opens and closes the panel; Escape closes it.
(function () {
  const button = document.querySelector("[data-menu-button]");
  const panel = document.querySelector("[data-menu-panel]");
  if (!button || !panel) return;

  const openIcon = button.querySelector('[data-menu-icon="open"]');
  const closeIcon = button.querySelector('[data-menu-icon="close"]');

  function setOpen(open) {
    panel.hidden = !open;
    button.setAttribute("aria-expanded", String(open));
    button.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    openIcon.classList.toggle("hidden", open);
    closeIcon.classList.toggle("hidden", !open);
  }

  button.addEventListener("click", function () {
    setOpen(panel.hidden);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !panel.hidden) {
      setOpen(false);
      button.focus(); // keep keyboard users where they were
    }
  });

  // Links like /about/#contact may not reload the page, so close the panel on click.
  panel.addEventListener("click", function (event) {
    if (event.target.closest("a")) setOpen(false);
  });
})();
