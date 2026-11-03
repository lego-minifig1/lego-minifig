/* 대문 통합 검색에서 넘어올 때: 주소 ?q=코드&n=이름&s=세트 → 그 카드의 상세 창을 바로 엶. 못 찾으면 도감 검색창에 이름을 넣어 둠 */
(function(){
  var P = new URLSearchParams(location.search), Q = (P.get("q") || "").trim(), N = (P.get("n") || "").trim(),
      S = (P.get("s") || "").split(",").map(function(x){ return x.trim(); }).filter(Boolean).slice(0, 4);
  if (!Q && !N) return;
  var CFG = window.__OPEN_CFG || {}, lc = Q.toLowerCase(), base = N.replace(/\s*[(\[].*$/, "");
  var wait = function(ms){ return new Promise(function(r){ setTimeout(r, ms); }); };
  function clean(){ hideTip(); try { var u = new URL(location.href); ["q", "n", "s", "t", "k"].forEach(function(k){ u.searchParams.delete(k); }); history.replaceState(history.state, "", u.pathname + u.search + u.hash); } catch(e){} }
  function toks(v){ return String(v).toLowerCase().split(/[^a-z0-9.\-]/).map(function(t){ return t.replace(/\.(png|jpe?g|gif|webp)$/, "").replace(/-1$/, ""); }); }
  function hasCode(e, code){
    for (var i = 0; i < e.attributes.length; i++){ var a = e.attributes[i]; if (a.value && a.value.length < 400 && toks(a.value).indexOf(code) >= 0) return true; }
    return false;
  }
  function overlay(){
    var d = document.querySelector("dialog[open]"); if (d) return d;
    var all = document.querySelectorAll(".modal.open,.modal.show,.modal-backdrop.open,[role=dialog]:not([hidden])");
    for (var i = 0; i < all.length; i++){ var c = getComputedStyle(all[i]); if (c.display !== "none" && c.visibility !== "hidden" && all[i].getClientRects().length) return all[i]; }
    return null;
  }
  /* 코드가 들어 있는 속성을 가진 요소만 브라우저가 바로 골라 줌 (화면 전체를 훑지 않음) */
  var LOW = "translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')";
  function find(code, root, sel){
    if (!code || /['"\\]/.test(code)) return null;
    var snap;
    try { snap = document.evaluate(".//*[@*[contains(" + LOW + ", '" + code + "')]]", root || document.body, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null); } catch(_){ return null; }
    for (var i = 0; i < snap.snapshotLength; i++){
      var e = snap.snapshotItem(i);
      if (!root && CFG.cand && !e.matches(CFG.cand)) continue;
      if (!root && e.closest("dialog,[role=dialog],input,textarea,select,option,summary")) continue;
      if (CFG.skip && e.closest(CFG.skip)) continue;
      if (hasCode(e, code)){ var s = sel || CFG.card; if (!s) return e; var c = e.closest(s) || e.querySelector(s); if (c) return c; }
    }
    return null;
  }
  function hit(el){
    try {
      var r = el.getBoundingClientRect(), o = { bubbles: true, cancelable: true, view: window, clientX: r.left + r.width / 2, clientY: r.top + r.height / 2 };
      if (window.PointerEvent){ el.dispatchEvent(new PointerEvent("pointerdown", o)); el.dispatchEvent(new PointerEvent("pointerup", o)); }
      el.dispatchEvent(new MouseEvent("mousedown", o)); el.dispatchEvent(new MouseEvent("mouseup", o));
    } catch(_){}
    el.click();
  }
  function reveal(e){ for (var x = e; x; x = x.parentElement) if (x.tagName === "DETAILS" && !x.open) x.open = true; }
  function press(e){
    reveal(e);
    var t = [e]; if (CFG.click){ var c = e.querySelector(CFG.click); if (c) t.unshift(c); }
    var im = e.querySelector && e.querySelector("img"); if (im) t.push(im);
    for (var i = 0; i < t.length; i++){ try { t[i].scrollIntoView({ block: "center" }); } catch(_){} hit(t[i]); if (overlay()) return true; }
    return false;
  }
  var went = false;
  function go(){
    if (went || !CFG.go) return; went = true;
    var g = document.querySelector('[data-go="' + CFG.go + '"],[data-view="' + CFG.go + '"],a[href="#' + CFG.go + '"]');
    if (g) g.click(); else location.hash = CFG.go;
  }
  function type(v){
    go();
    var inp = CFG.input ? document.querySelector(CFG.input) : null;
    if (!inp || !v) return false;
    inp.value = v;
    ["input", "keyup"].forEach(function(ev){ inp.dispatchEvent(new Event(ev, { bubbles: true })); });
    return true;
  }
  async function look(code, ms, again){
    for (var t = 0; t < ms; t += 300){
      var e = find(code); if (e && press(e)) return true;
      if (again && t && t % 1200 === 0) again();   /* 도감이 늦게 준비돼 검색창이 비워졌을 때 다시 넣음 */
      await wait(300);
    }
    return false;
  }
  async function viaSet(){
    if (!CFG.via || !S.length || !lc) return false;
    if (CFG.viaGo){ var g = document.querySelector(CFG.viaGo); if (g) g.click(); await wait(300); }
    for (var i = 0; i < S.length; i++){
      var s = S[i].toLowerCase().replace(/-1$/, "");
      type(S[i].replace(/-1$/, "")); await wait(500);
      var box = null;
      for (var t = 0; t < 1500 && !box; t += 250){
        box = [].slice.call(document.querySelectorAll("[" + CFG.via + "]")).filter(function(e){ return e.getAttribute(CFG.via).toLowerCase().replace(/-1$/, "") === s; })[0];
        if (!box) await wait(250);
      }
      if (!box) continue;
      box.click(); await wait(500);
      var d = overlay(); if (!d) continue;
      var f = find(lc, d);
      if (f){ f.click(); await wait(400); return true; }
      var x = d.querySelector("[data-close],.close,button[aria-label*='닫기']"); if (x) x.click(); else if (d.close) d.close();
      await wait(300);
    }
    return false;
  }
  /* 찾는 동안 화면 가운데 작은 창: 빙글 도는 표시 + "카드 여는 중" + 찾는 이름
     (도감마다 보안 설정이 달라 style 태그 대신 요소에 직접 꾸밈, 회전은 Web Animations로) */
  var tip = null, tipMsg = null;
  function showTip(){
    try {
      var box = document.createElement("div"); box.setAttribute("role", "status"); box.setAttribute("aria-live", "polite");
      var b = box.style; b.position = "fixed"; b.left = "50%"; b.top = "50%"; b.transform = "translate(-50%,-50%)"; b.zIndex = "2147483000";
      b.width = "min(240px, 76vw)"; b.padding = "22px 20px 18px"; b.borderRadius = "16px"; b.background = "rgba(255,255,255,.97)";
      b.boxShadow = "0 18px 50px rgba(0,0,0,.4), 0 0 0 1px rgba(0,0,0,.08)"; b.borderTop = "4px solid #c8382e"; b.textAlign = "center"; b.pointerEvents = "none";
      b.font = "500 14px/1.45 system-ui,-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif"; b.color = "#2a2118";
      b.transition = "opacity .25s"; b.opacity = "0";
      var sp = document.createElement("div"), ss = sp.style;
      ss.width = "34px"; ss.height = "34px"; ss.margin = "0 auto 12px"; ss.borderRadius = "50%";
      ss.border = "4px solid #ece4d4"; ss.borderTopColor = "#c8382e"; ss.boxSizing = "border-box";
      if (sp.animate) sp.animate([{ transform: "rotate(0deg)" }, { transform: "rotate(360deg)" }], { duration: 800, iterations: Infinity });
      tipMsg = document.createElement("div"); tipMsg.textContent = "카드 여는 중…";
      tipMsg.style.font = "700 16px/1.3 system-ui,-apple-system,'Apple SD Gothic Neo','Malgun Gothic',sans-serif";
      box.appendChild(sp); box.appendChild(tipMsg);
      if (N || Q){
        var nm = document.createElement("div"), ns = nm.style; nm.textContent = N || Q;
        ns.marginTop = "6px"; ns.color = "#7a6a58"; ns.fontSize = "13px"; ns.overflow = "hidden"; ns.textOverflow = "ellipsis"; ns.whiteSpace = "nowrap";
        box.appendChild(nm);
      }
      (document.documentElement || document.body).appendChild(box); tip = box;   /* 도감이 준비될 때까지 본문을 가려 두는 경우에도 보이게 */
      requestAnimationFrame(function(){ box.style.opacity = "1"; });
    } catch(_){}
  }
  function hideTip(msg){
    if (!tip) return;
    var t = tip; tip = null;
    var go = function(){ t.style.opacity = "0"; setTimeout(function(){ t.remove(); }, 300); };
    if (msg && tipMsg){ tipMsg.textContent = msg; var sp = t.firstChild; if (sp) sp.style.visibility = "hidden"; setTimeout(go, 1400); } else go();
  }
  async function run(){
    await wait(150);
    var T = P.get("t"); if (T && CFG.tabs){ var tb = [].slice.call(document.querySelectorAll(CFG.tabs)).filter(function(b){ return b.getAttribute("data-t") === T; })[0]; if (tb){ hit(tb); await wait(300); } }
    if (await look(lc, 900)){ clean(); return; }
    if (await viaSet()){ clean(); return; }
    if (lc && type(Q) && await look(lc, 4800, function(){ var i = CFG.input && document.querySelector(CFG.input); if (i && i.value !== Q) type(Q); })){ clean(); return; }
    if (CFG.tabs && lc){
      var tabs = document.querySelectorAll(CFG.tabs);
      for (var i = 0; i < tabs.length; i++){ var tb = document.querySelectorAll(CFG.tabs)[i]; if (!tb) break; hit(tb); await wait(300); type(Q); if (await look(lc, 1500)){ clean(); return; } }
    }
    if (P.get("k") !== "s" && base && type(base) && await look(lc, 2500)){ clean(); return; }
    type(P.get("k") === "s" ? (Q || base) : (base || Q)); hideTip("검색 결과로 보여 드릴게요"); clean();
  }
  /* 사진까지 다 받을 때(load)를 기다리지 않고, 화면 뼈대가 준비되면 바로 시작 */
  function start(){ showTip(); run(); }
  if (document.readyState === "loading") addEventListener("DOMContentLoaded", start); else start();
})();
