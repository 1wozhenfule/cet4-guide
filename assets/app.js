(function () {
  "use strict";

  var progress = document.getElementById("progress");
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    var v = max > 0 ? (h.scrollTop || document.body.scrollTop) / max : 0;
    if (progress) progress.style.width = (v * 100).toFixed(2) + "%";
  }
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  var body = document.body;
  var menuBtn = document.getElementById("menuBtn");
  var mask = document.getElementById("mask");
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      body.classList.toggle("nav-open");
    });
  }
  if (mask) {
    mask.addEventListener("click", function () {
      body.classList.remove("nav-open");
    });
  }

  var input = document.getElementById("searchInput");
  var panel = document.getElementById("searchPanel");
  var results = document.getElementById("searchResults");
  var closeBtn = document.getElementById("searchClose");
  var data = null;
  var loading = false;

  function load(cb) {
    if (data) return cb();
    if (window.__SEARCH_DATA__) {
      data = window.__SEARCH_DATA__;
      return cb();
    }
    if (loading) return;
    loading = true;
    var s = document.createElement("script");
    s.src = "assets/search-data.js";
    s.onload = function () {
      loading = false;
      data = window.__SEARCH_DATA__ || [];
      cb();
    };
    s.onerror = function () {
      loading = false;
      results.innerHTML = '<div class="nores">搜索索引加载失败，请检查 assets/search-data.js。</div>';
    };
    document.head.appendChild(s);
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function render(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) {
      results.innerHTML = '<div class="nores">输入关键词，例如「同义替换」「选词填空」「翻译」。</div>';
      return;
    }
    var hits = [];
    for (var i = 0; i < data.length; i++) {
      var it = data[i];
      var hay = (it.t + " " + it.x).toLowerCase();
      var ok = true;
      for (var j = 0; j < terms.length; j++) {
        if (hay.indexOf(terms[j]) === -1) { ok = false; break; }
      }
      if (ok) {
        var pos = hay.indexOf(terms[0]);
        var start = Math.max(0, pos - 30);
        hits.push({
          t: it.t, p: it.p, a: it.a,
          x: (start > 0 ? "…" : "") + it.x.slice(start, start + 110) + "…"
        });
      }
      if (hits.length >= 20) break;
    }
    if (!hits.length) {
      results.innerHTML = '<div class="nores">没有找到「' + esc(q) + '」，换个词试试。</div>';
      return;
    }
    results.innerHTML = hits.map(function (h) {
      return '<a class="res" href="' + h.p + ".html#" + h.a + '"><b>' +
        esc(h.t) + "</b><small>" + esc(h.x) + "</small></a>";
    }).join("");
  }

  function open() {
    if (!panel) return;
    panel.hidden = false;
    load(function () { render(input.value.trim()); });
    input.focus();
  }

  function close() {
    if (panel) panel.hidden = true;
  }

  if (input) {
    input.addEventListener("focus", open);
    input.addEventListener("input", function () {
      load(function () { render(input.value.trim()); });
    });
    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { close(); input.blur(); }
      if (e.key === "Enter") {
        var first = results.querySelector("a.res");
        if (first) window.location.href = first.getAttribute("href");
      }
    });
  }
  if (closeBtn) closeBtn.addEventListener("click", close);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { close(); body.classList.remove("nav-open"); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault(); open();
    }
  });
  document.addEventListener("click", function (e) {
    if (panel && !panel.hidden && !panel.contains(e.target) &&
        e.target !== input) close();
  });
})();