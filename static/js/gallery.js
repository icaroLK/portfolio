// Gallery viewer: clicking a gallery image opens it full screen in a <dialog>
// with Close, Previous and Next. Keyboard: Escape closes, arrow keys switch.
// Swiping left or right switches on touch screens.
// Without JS the links still work: each image opens on its own.
(function () {
  const gallery = document.querySelector("[data-gallery]");
  const dialog = document.querySelector("[data-lightbox]");
  if (!gallery || !dialog || typeof dialog.showModal !== "function") return;

  const items = Array.from(gallery.querySelectorAll("[data-gallery-item]"));
  const image = dialog.querySelector("[data-lightbox-img]");
  const caption = dialog.querySelector("[data-lightbox-caption]");
  const counter = dialog.querySelector("[data-lightbox-count]");
  const prevButton = dialog.querySelector("[data-lightbox-prev]");
  const nextButton = dialog.querySelector("[data-lightbox-next]");
  let current = 0;

  // With a single image there is nothing to switch to.
  if (items.length < 2) {
    prevButton.hidden = true;
    nextButton.hidden = true;
  }

  function show(index) {
    // Wraps around: Next on the last image goes to the first.
    current = (index + items.length) % items.length;
    const item = items[current];
    image.src = item.href;
    image.alt = item.dataset.alt || "";
    caption.textContent = item.dataset.caption || "";
    caption.hidden = !item.dataset.caption;
    counter.textContent = current + 1 + " / " + items.length;
  }

  function open(index) {
    show(index);
    document.documentElement.classList.add("overflow-hidden"); // stop the page scrolling behind
    dialog.showModal();
  }

  items.forEach(function (item, index) {
    item.addEventListener("click", function (event) {
      event.preventDefault();
      open(index);
    });
  });

  // Cleanup runs right here instead of on the dialog's "close" event,
  // which some browsers fire late or not at all.
  function close() {
    if (!dialog.open) return;
    dialog.close();
    document.documentElement.classList.remove("overflow-hidden");
    image.removeAttribute("src");
    items[current].focus();
  }

  prevButton.addEventListener("click", function () { show(current - 1); });
  nextButton.addEventListener("click", function () { show(current + 1); });
  dialog.querySelector("[data-lightbox-close]").addEventListener("click", close);

  // Escape: take over from <dialog> so the same cleanup runs.
  dialog.addEventListener("cancel", function (event) {
    event.preventDefault();
    close();
  });

  // Clicking the dark area around the image closes the viewer.
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog || event.target.hasAttribute("data-lightbox-stage")) {
      close();
    }
  });

  dialog.addEventListener("keydown", function (event) {
    if (items.length < 2) return;
    if (event.key === "ArrowLeft") show(current - 1);
    if (event.key === "ArrowRight") show(current + 1);
  });

  let touchStartX = null;
  dialog.addEventListener("touchstart", function (event) {
    touchStartX = event.touches[0].clientX;
  }, { passive: true });
  dialog.addEventListener("touchend", function (event) {
    if (touchStartX === null || items.length < 2) return;
    const distance = event.changedTouches[0].clientX - touchStartX;
    if (Math.abs(distance) > 50) show(current + (distance < 0 ? 1 : -1));
    touchStartX = null;
  });
})();
