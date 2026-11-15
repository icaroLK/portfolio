/*
  Small formatting toolbar above the long text boxes in the admin.
  It only types Markdown symbols for you (**bold**, *italic*, ## Title, · list, [link](...)),
  so the text stays plain and the public page renders it.
  Ctrl+B and Ctrl+I work too.
*/
(function () {
  "use strict";

  function changed(textarea) {
    textarea.focus();
    textarea.dispatchEvent(new Event("input", { bubbles: true }));
  }

  // Put `before` and `after` around the selection (or a placeholder) and select the inner text.
  function wrap(textarea, before, after, placeholder) {
    var start = textarea.selectionStart;
    var end = textarea.selectionEnd;
    var inner = textarea.value.slice(start, end) || placeholder;
    textarea.setRangeText(before + inner + after, start, end, "end");
    textarea.setSelectionRange(start + before.length, start + before.length + inner.length);
    changed(textarea);
  }

  // Add `prefix` to the start of every selected line, or remove it when all lines have it.
  function prefixLines(textarea, prefix, alsoMatches) {
    var value = textarea.value;
    var start = value.lastIndexOf("\n", textarea.selectionStart - 1) + 1;
    var endBreak = value.indexOf("\n", textarea.selectionEnd);
    var end = endBreak === -1 ? value.length : endBreak;
    var lines = value.slice(start, end).split("\n");
    var pattern = alsoMatches || new RegExp("^" + prefix.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
    var allHave = lines.every(function (line) { return pattern.test(line.trim()); });
    var result = lines.map(function (line) {
      var trimmed = line.trim();
      if (allHave) return trimmed.replace(pattern, "");
      return trimmed === "" ? line : prefix + trimmed;
    }).join("\n");
    textarea.setRangeText(result, start, end, "select");
    changed(textarea);
  }

  var ACTIONS = [
    { label: "B", title: "Bold (Ctrl+B)", css: "md-bold", run: function (t) { wrap(t, "**", "**", "bold text"); } },
    { label: "I", title: "Italic (Ctrl+I)", css: "md-italic", run: function (t) { wrap(t, "*", "*", "italic text"); } },
    { label: "H", title: "Small title", run: function (t) { prefixLines(t, "## ", /^#{1,6}\s+/); } },
    { label: "· List", title: "Bullet list", run: function (t) { prefixLines(t, "· ", /^[·•\-*+]\s+/); } },
    { label: "Link", title: "Link", run: function (t) { wrap(t, "[", "](https://)", "link text"); } },
  ];

  function addToolbar(textarea) {
    var bar = document.createElement("div");
    bar.className = "md-toolbar";
    bar.setAttribute("role", "toolbar");
    bar.setAttribute("aria-label", "Text formatting");
    ACTIONS.forEach(function (action) {
      var button = document.createElement("button");
      button.type = "button";
      button.textContent = action.label;
      button.title = action.title;
      button.setAttribute("aria-label", action.title);
      if (action.css) button.classList.add(action.css);
      button.addEventListener("click", function () { action.run(textarea); });
      bar.appendChild(button);
    });
    textarea.parentNode.insertBefore(bar, textarea);

    textarea.addEventListener("keydown", function (event) {
      if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
      var key = event.key.toLowerCase();
      if (key === "b") { event.preventDefault(); ACTIONS[0].run(textarea); }
      if (key === "i") { event.preventDefault(); ACTIONS[1].run(textarea); }
    });
  }

  function init() {
    document.querySelectorAll("textarea[data-markdown]").forEach(addToolbar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
