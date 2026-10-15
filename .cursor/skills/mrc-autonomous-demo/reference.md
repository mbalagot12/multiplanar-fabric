# MRC Autonomous Demo — Reference Blocks

Copy these into standalone MRC HTML pages. Adjust EV/plane indices to match the target topology.

## CSS (append to `<style>`)

```css
button.btn-pulse{background:#7F77DD;color:#fff;border-color:#7F77DD;
  box-shadow:0 0 0 3px rgba(127,119,221,.35)}
#ctl.demo-lock button:not(#b-demo){pointer-events:none;opacity:.55}
#ctl.demo-lock label{pointer-events:none;opacity:.55}
#demo-bar{height:3px;background:var(--t-bd);border-radius:2px;margin-top:10px;overflow:hidden;display:none}
#demo-bar i{display:block;height:100%;width:0;background:#7F77DD;transition:width .25s linear}
#demo-cap{font-size:12px;color:var(--t-text);margin-top:8px;min-height:40px;line-height:1.55;
  padding:8px 10px;background:var(--t-surf);border:0.5px solid var(--t-bd);border-radius:8px;display:none}
#demo-cap em{font-style:normal;color:var(--t-text2);font-size:11px;display:block;margin-top:3px}
```

If the page uses MkDocs Material vars (`--color-*`) instead of `--t-*`, map accordingly.

## HTML (before `#ctl`)

```html
<div id="demo-bar"><i id="demo-prog"></i></div>
<div id="demo-cap"></div>

<div id="ctl">
  <button id="b-demo">Run demo</button>
  <!-- existing controls -->
</div>
```

## State variables

```javascript
let demoOn = false, demoScene = 0, demoLeft = 0, demoSceneDur = 0, demoSavedRate = 3;
let lastTs = 0;
```

## Control setters

```javascript
function setRate(v){
  rate = v;
  document.getElementById('r-sl').value = v;
  document.getElementById('r-v').textContent = v;
}
function setCongest(on){
  const e = evs[6];
  e.cong = on;
  if (on) e.load = 0.8; else e.fails = 0;
  document.getElementById('b-cong').textContent = on ? 'Clear EV 6' : 'Congest EV 6';
  bgd();
}
function setBroken(on){
  const e = evs[9];
  e.broken = on;
  if (!on) e.fails = 0;
  document.getElementById('b-break').textContent = on ? 'Repair EV 9' : 'Break EV 9';
  bgd();
}
function setPlaneFail(on){
  planes[3].f = on ? 1 : 0;
  document.getElementById('b-fail').textContent = on ? 'Restore plane 3 port' : 'Fail plane 3 port';
  bgd();
}
function setTrim(on){
  trimOn = on;
  document.getElementById('b-trim').textContent = 'Trim: ' + (on ? 'on' : 'off');
}
function clearAllFaults(){
  setCongest(false); setBroken(false); setPlaneFail(false); setTrim(true);
}
```

## Demo engine (button-click with pauses)

Each step fires a real button click, then pauses so the fault can be observed before the next one.

```javascript
const DEMO_SCRIPT = [
  {pause:5, btn:null, title:'Baseline', cap:'...', em:'Pausing before first fault…'},
  {pause:8, btn:'b-cong', title:'Congest EV 6', cap:'...', em:'Pausing before next fault…'},
  {pause:5, btn:'b-cong', title:'Clear EV 6', cap:'...', em:'Pausing before next fault…'},
  {pause:10, btn:'b-break', title:'Break EV 9', cap:'...', em:'Pausing before next fault…'},
  {pause:7, btn:'b-break', title:'Repair EV 9', cap:'...', em:'Pausing before next fault…'},
  {pause:7, btn:'b-fail', title:'Fail plane 3 port', cap:'...', em:'Pausing before next fault…'},
  {pause:4, btn:'b-fail', title:'Restore plane 3 port', cap:'...', em:'Pausing before next fault…'},
  {pause:6, btn:'b-trim', title:'Trim off', cap:'...', em:'Pausing before next fault…'},
  {pause:4, btn:'b-trim', title:'Trim on', cap:'...', em:'Demo complete.'}
];

let demoFiring = false;

function pulseBtn(id){
  const el = document.getElementById(id);
  el.classList.add('btn-pulse');
  setTimeout(function(){ el.classList.remove('btn-pulse'); }, 700);
}
function fireBtn(id){
  demoFiring = true;
  pulseBtn(id);
  document.getElementById(id).click();
  demoFiring = false;
}
function demoUi(on){
  document.getElementById('demo-bar').style.display = on ? 'block' : 'none';
  document.getElementById('demo-cap').style.display = on ? 'block' : 'none';
  document.getElementById('b-demo').textContent = on ? 'Stop demo' : 'Run demo';
  document.getElementById('b-demo').className = on ? 'demo-on' : '';
  document.getElementById('ctl').classList.toggle('demo-lock', on);
}
function showDemoStep(i){
  const s = DEMO_SCRIPT[i];
  demoSceneDur = s.pause; demoLeft = s.pause;
  document.getElementById('demo-cap').innerHTML =
    '<strong>'+(i+1)+' / '+DEMO_SCRIPT.length+' — '+s.title+'</strong> '+s.cap+
    (s.em ? '<em>'+s.em+'</em>' : '');
  document.getElementById('msg').textContent = '';
  document.getElementById('demo-prog').style.width = '0%';
  if (s.btn) fireBtn(s.btn);
  hud();
}
```

Use `#ctl.demo-lock button:not(#b-demo){pointer-events:none}` — **not** `disabled`, so programmatic `.click()` still works.

Guard reset: `if (demoOn && !demoFiring) stopDemo();` on the reset handler.

## Animation loop hook

Replace `function step()` with timestamp-aware version:

```javascript
function step(ts){
  if (demoOn && lastTs) demoTick(Math.min(0.1, (ts - lastTs) / 1000));
  lastTs = ts;
  /* existing step body */
  requestAnimationFrame(step);
}
```

## Event wiring

```javascript
document.getElementById('b-demo').onclick = function(){ demoOn ? stopDemo() : startDemo(); };
document.getElementById('b-reset').onclick = function(){
  if (demoOn) stopDemo();
  reset(); clearAllFaults(); bgd();
};
```

## hud() guard

At the top of the live-status message block in `hud()`:

```javascript
if (demoOn) return;
```
