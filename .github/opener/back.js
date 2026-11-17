/* 휴대폰 뒤로 가기: 상세 창이 열려 있으면 도감에서 나가지 않고 그 창만 닫음 */
(function(){
  if (window.__dlgBack) return; window.__dlgBack = 1;
  var K = "dlgBack", SEL = "dialog[open],#modal.show", depth = 0, skip = 0, keep = null;
  function opened(){ return [].filter.call(document.querySelectorAll(SEL), function(e){ return e.getClientRects().length; }); }
  function shut(e){
    var b = e.querySelector("[data-close],.close,.x,.dclose,.mclose,button[aria-label*='닫기'],button[title*='닫기']");
    if (!b){ var bs = e.querySelectorAll("button"); for (var i = 0; i < bs.length; i++) if (/^[\s×✕✖xX]+$/.test(bs[i].textContent)){ b = bs[i]; break; } }
    if (b) b.click();
    if (e.matches(SEL)){ if (e.close) e.close(); else e.classList.remove("show"); }
  }
  function sync(){
    if (skip) return;
    var n = opened().length;
    while (depth < n){
      var s = {}; s[K] = depth + 1;
      try { history.pushState(s, "", location.href); } catch(_){ return; }
      depth++;
    }
    if (depth > n){ var d = depth - n; depth = n; skip++; keep = location.href; history.go(-d); }
  }
  addEventListener("popstate", function(){
    if (skip){
      skip--;
      if (keep && keep !== location.href){ try { history.replaceState(history.state, "", keep); } catch(_){} }
      keep = null; setTimeout(sync, 0); return;
    }
    if (!depth){
      /* 앞으로 가기로 빈 기록에 들어온 경우 한 칸 되돌림 */
      if (history.state && history.state[K] && !opened().length){ skip++; keep = location.href; history.back(); }
      return;
    }
    depth--;
    var o = opened(); if (o.length > depth) shut(o[o.length - 1]);
    setTimeout(sync, 0);
  });
  var mo = new MutationObserver(sync), seen = null, tries = 0;
  function watch(){
    mo.observe(document.documentElement, { subtree: true, attributes: true, attributeFilter: ["open"] });
    var t = setInterval(function(){
      var m = document.getElementById("modal");
      if (m && m !== seen){ seen = m; mo.observe(m, { attributes: true, attributeFilter: ["class"] }); sync(); }
      if (++tries > 60) clearInterval(t);
    }, 500);
    /* 창을 연 채 새로 고침했을 때 남은 빈 기록을 치움 */
    if (history.state && history.state[K]) setTimeout(function(){ if (!opened().length && !depth && history.state && history.state[K]){ skip++; keep = location.href; history.back(); } }, 1500);
    sync();
  }
  if (document.readyState === "loading") addEventListener("DOMContentLoaded", watch); else watch();
})();
