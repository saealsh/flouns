<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>فلونس — مخططك المالي</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&family=Tajawal:wght@300;400;700;800&display=swap" rel="stylesheet">
<style>
/* ═══════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════ */
:root {
  --bg:        #0d0608;
  --bg2:       #150a0d;
  --bg3:       #1e0e12;
  --surface:   rgba(255,255,255,.04);
  --surface2:  rgba(255,255,255,.07);
  --border:    rgba(199,183,163,.14);
  --border2:   rgba(199,183,163,.22);

  --gold:      #c9a96e;
  --gold2:     #e8c98a;
  --gold-dim:  rgba(201,169,110,.18);
  --crimson:   #7a2535;
  --crimson2:  #9b3044;
  --crimson-dim:rgba(122,37,53,.2);
  --sage:      #4a8c6a;
  --sage2:     #6aaa88;
  --sage-dim:  rgba(74,140,106,.18);
  --text:      #e8ddd0;
  --text2:     #b0a090;
  --text3:     #6a5a50;

  --r-sm:  10px;
  --r-md:  16px;
  --r-lg:  22px;
  --r-xl:  30px;

  --shadow: 0 8px 32px rgba(0,0,0,.5);
  --shadow-gold: 0 0 30px rgba(201,169,110,.15);

  --font-body:    'Cairo', sans-serif;
  --font-display: 'Tajawal', sans-serif;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  font-family: var(--font-body);
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  direction: rtl;
  overflow-x: hidden;
  padding-bottom: 80px;
}

/* Subtle grid texture */
body::before {
  content: '';
  position: fixed; inset: 0; z-index: 0;
  background-image:
    linear-gradient(rgba(201,169,110,.025) 1px, transparent 1px),
    linear-gradient(90deg, rgba(201,169,110,.025) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

/* ═══════════════════════════════════════════
   SCROLLBAR
═══════════════════════════════════════════ */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--crimson); border-radius: 2px; }

/* ═══════════════════════════════════════════
   HEADER
═══════════════════════════════════════════ */
.header {
  position: sticky; top: 0; z-index: 200;
  background: rgba(13,6,8,.92);
  backdrop-filter: blur(24px);
  border-bottom: 1px solid var(--border);
  padding: 0 16px;
}

.header-inner {
  max-width: 600px; margin: 0 auto;
  display: flex; align-items: center; gap: 10px;
  height: 58px;
  overflow-x: auto; overflow-y: hidden;
  scrollbar-width: none;
}
.header-inner::-webkit-scrollbar { display: none; }

.logo {
  display: flex; align-items: center; gap: 9px;
  flex-shrink: 0; cursor: pointer;
}
.logo-mark {
  width: 36px; height: 36px; border-radius: 10px;
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  border: 1px solid rgba(201,169,110,.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 18px;
  box-shadow: 0 0 16px rgba(122,37,53,.4);
}
.logo-name {
  font-family: var(--font-display);
  font-size: 22px; font-weight: 800;
  color: var(--text);
  letter-spacing: .5px;
}

.header-spacer { flex: 1; }

.nav-pill {
  display: flex; gap: 2px;
  background: rgba(255,255,255,.04);
  border: 1px solid var(--border);
  border-radius: 12px; padding: 3px;
  flex-shrink: 0;
}
.nav-btn {
  padding: 5px 12px; border-radius: 9px;
  border: none; background: none; cursor: pointer;
  font-family: var(--font-body); font-size: 12px; font-weight: 700;
  color: var(--text3);
  transition: all .2s;
  white-space: nowrap;
}
.nav-btn.active {
  background: var(--crimson);
  color: var(--text);
  box-shadow: 0 2px 10px rgba(122,37,53,.4);
}

.month-nav {
  display: flex; align-items: center; gap: 4px; flex-shrink: 0;
}
.month-arrow {
  width: 28px; height: 28px; border-radius: 8px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text2); cursor: pointer; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.month-arrow:hover { border-color: var(--gold); color: var(--gold); }
.month-label {
  font-size: 13px; font-weight: 700; color: var(--text);
  min-width: 88px; text-align: center;
}

.bell-btn {
  width: 32px; height: 32px; border-radius: 9px;
  border: 1px solid var(--border); background: var(--surface);
  color: var(--text2); cursor: pointer; font-size: 15px;
  display: flex; align-items: center; justify-content: center;
  position: relative; flex-shrink: 0; transition: all .2s;
}
.bell-btn.alert { border-color: var(--gold); color: var(--gold); }
.bell-dot {
  position: absolute; top: -3px; right: -3px;
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--crimson2); display: none;
  animation: pulse 2s infinite;
}
.bell-dot.show { display: block; }
@keyframes pulse {
  0%,100% { box-shadow: 0 0 0 0 rgba(155,48,68,.5); }
  50%      { box-shadow: 0 0 0 5px rgba(155,48,68,0); }
}

/* ═══════════════════════════════════════════
   MAIN LAYOUT
═══════════════════════════════════════════ */
.main {
  max-width: 600px; margin: 0 auto;
  padding: 14px 12px 0;
  position: relative; z-index: 1;
}

/* ═══════════════════════════════════════════
   SALARY STRIP
═══════════════════════════════════════════ */
.salary-strip {
  background: linear-gradient(135deg, var(--bg3), rgba(122,37,53,.15));
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 12px 16px;
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 12px;
  animation: fadeIn .4s ease;
}
.salary-icon { font-size: 24px; flex-shrink: 0; }
.salary-body { flex: 1; }
.salary-label { font-size: 11px; color: var(--text3); margin-bottom: 4px; }
.salary-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.salary-select {
  background: rgba(255,255,255,.06); border: 1px solid var(--border);
  border-radius: 8px; padding: 4px 8px; color: var(--text);
  font-family: var(--font-body); font-size: 13px; outline: none; cursor: pointer;
  width: 65px;
}
.salary-badge {
  font-size: 13px; font-weight: 800; color: var(--text);
  background: rgba(122,37,53,.35); border: 1px solid rgba(201,169,110,.25);
  border-radius: 8px; padding: 4px 12px; white-space: nowrap;
}
.salary-badge.today { border-color: var(--gold); color: var(--gold); box-shadow: var(--shadow-gold); }

/* ═══════════════════════════════════════════
   SUMMARY CARDS
═══════════════════════════════════════════ */
.cards-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 8px; margin-bottom: 12px;
}
.card {
  border-radius: var(--r-md); padding: 14px;
  border: 1px solid var(--border);
  position: relative; overflow: hidden;
  background: var(--bg3);
  animation: fadeIn .5s ease both;
  cursor: default;
  transition: border-color .3s, transform .2s;
}
.card:hover { transform: translateY(-2px); }
.card::before {
  content: ''; position: absolute; inset: 0;
  opacity: 0; transition: opacity .3s;
}
.card.income { animation-delay: .05s; }
.card.income:hover { border-color: rgba(106,170,136,.4); }
.card.income::before { background: radial-gradient(ellipse at 20% 0%, rgba(74,140,106,.08), transparent 60%); }
.card.expense { animation-delay: .1s; }
.card.expense:hover { border-color: rgba(155,48,68,.4); }
.card.expense::before { background: radial-gradient(ellipse at 20% 0%, rgba(122,37,53,.1), transparent 60%); }
.card.saved { animation-delay: .15s; }
.card.saved:hover { border-color: rgba(201,169,110,.3); }
.card.saved::before { background: radial-gradient(ellipse at 20% 0%, rgba(201,169,110,.07), transparent 60%); }
.card.balance { animation-delay: .2s; }

.card:hover::before { opacity: 1; }

.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.card-icon {
  width: 32px; height: 32px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px;
}
.card.income .card-icon  { background: var(--sage-dim); }
.card.expense .card-icon { background: var(--crimson-dim); }
.card.saved .card-icon   { background: var(--gold-dim); }
.card.balance .card-icon { background: var(--surface2); }

.card-badge {
  font-size: 10px; font-weight: 700; padding: 2px 7px;
  border-radius: 8px;
}
.card.income .card-badge  { background: var(--sage-dim);    color: var(--sage2); }
.card.expense .card-badge { background: var(--crimson-dim); color: #e08080; }

.card-label { font-size: 11px; color: var(--text3); margin-bottom: 3px; }
.card-value {
  font-family: var(--font-display);
  font-size: 20px; font-weight: 800; line-height: 1;
}
.card.income  .card-value { color: var(--sage2); }
.card.expense .card-value { color: #e07070; }
.card.saved   .card-value { color: var(--gold); }
.card.balance .card-value { color: var(--text); }

.card-sub { font-size: 10px; color: var(--text3); margin-top: 4px; }
.card-bar { background: rgba(255,255,255,.06); border-radius: 3px; height: 3px; margin-top: 8px; overflow: hidden; }
.card-bar-fill { height: 100%; border-radius: 3px; transition: width .8s ease; }
.card.income  .card-bar-fill { background: var(--sage2); }
.card.expense .card-bar-fill { background: var(--crimson2); }
.card.saved   .card-bar-fill { background: var(--gold); }

/* ═══════════════════════════════════════════
   BUDGET PROGRESS
═══════════════════════════════════════════ */
.progress-block {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 14px 16px;
  margin-bottom: 12px;
  animation: fadeIn .5s .25s ease both;
}
.progress-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.progress-title { font-size: 13px; font-weight: 700; color: var(--text2); }
.progress-pct {
  font-family: var(--font-display);
  font-size: 22px; font-weight: 800; color: var(--gold);
}
.progress-track {
  background: rgba(255,255,255,.06); border-radius: 20px;
  height: 8px; overflow: hidden; margin-bottom: 6px;
}
.progress-fill {
  height: 100%; border-radius: 20px;
  background: linear-gradient(90deg, var(--crimson), var(--gold));
  transition: width .9s ease;
  position: relative; overflow: hidden;
}
.progress-fill::after {
  content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.25), transparent);
  animation: shimmer 2.5s infinite;
}
@keyframes shimmer { 100% { left: 100%; } }
.progress-fill.warn { background: linear-gradient(90deg, #e07000, #ffa040); }
.progress-fill.danger { background: linear-gradient(90deg, #800000, var(--crimson2)); }
.progress-labels { display: flex; justify-content: space-between; font-size: 11px; color: var(--text3); }

/* ═══════════════════════════════════════════
   AI INSIGHT
═══════════════════════════════════════════ */
.ai-insight {
  background: linear-gradient(135deg, rgba(122,37,53,.12), rgba(21,10,13,.8));
  border: 1px solid rgba(201,169,110,.2);
  border-radius: var(--r-md); padding: 13px 15px;
  margin-bottom: 12px; display: flex; gap: 11px; align-items: flex-start;
  animation: fadeIn .5s .3s ease both;
}
.ai-orb {
  width: 34px; height: 34px; border-radius: 10px; flex-shrink: 0;
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; cursor: pointer;
  box-shadow: 0 0 14px rgba(122,37,53,.4);
  transition: transform .3s;
  animation: orbPulse 3s ease-in-out infinite;
}
@keyframes orbPulse {
  0%,100% { box-shadow: 0 0 14px rgba(122,37,53,.4); }
  50%      { box-shadow: 0 0 22px rgba(201,169,110,.35); }
}
.ai-orb:hover { transform: rotate(15deg) scale(1.08); }
.ai-label { font-size: 10px; font-weight: 700; color: var(--gold); letter-spacing: .8px; margin-bottom: 3px; }
.ai-text { font-size: 13px; color: var(--text2); line-height: 1.65; flex: 1; }

/* ═══════════════════════════════════════════
   STREAK
═══════════════════════════════════════════ */
.streak-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 16px;
  margin-bottom: 12px; position: relative; overflow: hidden;
  animation: fadeIn .5s .35s ease both;
}
.streak-card::before {
  content: '🔥';
  position: absolute; left: -10px; bottom: -15px;
  font-size: 80px; opacity: .04; pointer-events: none;
  transform: rotate(-15deg);
}
.streak-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.streak-title { font-size: 13px; font-weight: 700; color: var(--text2); }
.streak-flame { font-size: 22px; animation: flamePop 1.6s ease-in-out infinite; }
@keyframes flamePop { 0%,100%{ transform:scale(1); } 50%{ transform:scale(1.18); } }

.streak-num {
  font-family: var(--font-display);
  font-size: 56px; font-weight: 900; color: var(--text); line-height: 1;
  text-align: center; margin-bottom: 4px;
}
.streak-num.active { color: var(--gold); text-shadow: 0 0 30px rgba(201,169,110,.35); }
.streak-sub { text-align: center; font-size: 11px; color: var(--text3); margin-bottom: 14px; }

.streak-dots {
  display: flex; gap: 5px; justify-content: center; margin-bottom: 14px; flex-wrap: wrap;
}
.streak-dot {
  width: 34px; height: 34px; border-radius: 50%;
  border: 1.5px solid rgba(255,255,255,.08);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; color: var(--text3); font-weight: 700;
  position: relative; transition: all .3s;
}
.streak-dot.done {
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  border-color: rgba(201,169,110,.4); color: var(--text);
  box-shadow: 0 0 8px rgba(122,37,53,.4);
}
.streak-dot.today { border-color: var(--gold); animation: todayRing 2s infinite; }
@keyframes todayRing {
  0%,100% { box-shadow: 0 0 0 0 rgba(201,169,110,.3); }
  50%      { box-shadow: 0 0 0 5px rgba(201,169,110,0); }
}
.streak-dot.done::after {
  content: '🔥'; position: absolute; top: -7px; right: -5px; font-size: 9px;
}

.streak-checkin {
  width: 100%; padding: 12px; border-radius: 12px;
  border: 1.5px solid rgba(122,37,53,.5);
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  color: var(--text); font-family: var(--font-display); font-size: 14px; font-weight: 800;
  cursor: pointer; letter-spacing: .5px;
  transition: all .3s;
  box-shadow: 0 4px 16px rgba(122,37,53,.35);
}
.streak-checkin:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(122,37,53,.45); }
.streak-checkin.done {
  background: rgba(255,255,255,.04); border-style: dashed;
  color: var(--text3); cursor: default; transform: none;
  box-shadow: none;
}
.streak-msg { text-align: center; font-size: 12px; color: var(--gold); margin-top: 10px; min-height: 16px; }
.streak-stats { display: grid; grid-template-columns: repeat(3,1fr); gap: 7px; margin-top: 12px; }
.streak-stat {
  background: rgba(255,255,255,.04); border-radius: 9px;
  padding: 9px; text-align: center; border: 1px solid var(--border);
}
.streak-stat-num {
  font-family: var(--font-display); font-size: 18px; font-weight: 900; color: var(--gold);
}
.streak-stat-lbl { font-size: 9px; color: var(--text3); margin-top: 2px; }

/* ═══════════════════════════════════════════
   SECTION CARD
═══════════════════════════════════════════ */
.section-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 15px;
  margin-bottom: 12px;
  animation: fadeIn .5s .4s ease both;
}
.section-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.section-title { font-size: 13px; font-weight: 700; color: var(--text2); }
.section-total { font-size: 13px; font-weight: 800; color: var(--gold); }
.section-subtitle { font-size: 10px; color: var(--text3); margin-top: 2px; }

.add-trigger {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 5px 11px;
  color: var(--text2); font-family: var(--font-body); font-size: 12px;
  cursor: pointer; transition: all .2s;
}
.add-trigger:hover { border-color: var(--gold); color: var(--gold); }

/* Items */
.items-list { display: flex; flex-direction: column; gap: 5px; margin-bottom: 8px; }
.item-row {
  display: flex; align-items: center; gap: 8px;
  background: rgba(255,255,255,.03); border-radius: 9px;
  padding: 9px 11px; border: 1px solid transparent;
  transition: all .2s;
}
.item-row:hover { border-color: var(--border); background: rgba(255,255,255,.05); }
.item-row.paid { opacity: .4; }
.item-row.paid .item-name { text-decoration: line-through; }
.item-emoji {
  width: 28px; height: 28px; border-radius: 8px;
  background: var(--surface2); display: flex; align-items: center;
  justify-content: center; font-size: 14px; flex-shrink: 0;
}
.item-name { flex: 1; font-size: 13px; color: var(--text); cursor: pointer; }
.item-recurring { font-size: 9px; color: var(--text3); }
.item-amount { font-size: 13px; font-weight: 700; white-space: nowrap; }
.item-amount.income  { color: var(--sage2); }
.item-amount.expense { color: #e07070; }
.item-del {
  background: none; border: none; color: var(--text3);
  cursor: pointer; font-size: 12px; padding: 3px;
  transition: color .2s; line-height: 1;
}
.item-del:hover { color: var(--crimson2); }

.empty-state {
  text-align: center; padding: 16px;
  color: var(--text3); font-size: 12px;
  display: flex; flex-direction: column; align-items: center; gap: 5px;
}
.empty-state-icon { font-size: 26px; opacity: .3; }

/* Add Form */
.add-form {
  background: rgba(255,255,255,.03); border-radius: 11px;
  padding: 11px; border: 1px solid var(--border);
  display: none; margin-top: 6px;
}
.add-form.open { display: block; animation: slideDown .25s ease; }
@keyframes slideDown { from { opacity:0; transform:translateY(-6px); } to { opacity:1; transform:translateY(0); } }

.cat-chips { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 8px; }
.cat-chip {
  background: rgba(255,255,255,.05); border: 1px solid var(--border);
  border-radius: 18px; padding: 4px 10px; font-size: 11px;
  cursor: pointer; color: var(--text3); transition: all .2s;
}
.cat-chip:hover, .cat-chip.sel {
  background: var(--crimson-dim); border-color: rgba(201,169,110,.35);
  color: var(--text);
}

.form-row { display: flex; gap: 6px; flex-wrap: wrap; }
.form-input {
  flex: 1; min-width: 80px;
  background: rgba(255,255,255,.05); border: 1px solid var(--border);
  border-radius: 9px; padding: 8px 11px; color: var(--text);
  font-family: var(--font-body); font-size: 13px; outline: none;
  transition: border-color .2s;
}
.form-input:focus { border-color: rgba(201,169,110,.5); }
.form-input::placeholder { color: var(--text3); }

.form-select {
  flex: 1; min-width: 80px;
  background: rgba(255,255,255,.05); border: 1px solid var(--border);
  border-radius: 9px; padding: 8px 10px; color: var(--text);
  font-family: var(--font-body); font-size: 13px; outline: none; cursor: pointer;
}
.form-select option { background: #1e0e12; }

.form-btn {
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  color: var(--text); border: none; border-radius: 9px;
  padding: 8px 16px; font-size: 13px; font-weight: 700;
  cursor: pointer; font-family: var(--font-body);
  transition: all .2s; white-space: nowrap;
}
.form-btn:hover { opacity: .88; transform: translateY(-1px); }

.amt-shortcuts { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 6px; }
.amt-sh {
  background: rgba(255,255,255,.04); border: 1px solid var(--border);
  border-radius: 7px; padding: 3px 9px; font-size: 11px;
  cursor: pointer; color: var(--text3); transition: all .2s;
  font-family: var(--font-body);
}
.amt-sh:hover { background: var(--gold-dim); color: var(--gold); border-color: rgba(201,169,110,.3); }

.form-check {
  display: flex; align-items: center; gap: 6px;
  margin-top: 7px; font-size: 12px; color: var(--text3); cursor: pointer;
}
.form-check input { accent-color: var(--gold); }

/* ═══════════════════════════════════════════
   BUDGET CATEGORIES
═══════════════════════════════════════════ */
.budget-alert {
  background: linear-gradient(135deg, rgba(150,30,30,.25), rgba(13,6,8,.8));
  border: 1px solid rgba(220,60,60,.35); border-radius: 11px;
  padding: 11px 14px; margin-bottom: 11px;
  display: none; flex-direction: column; gap: 7px;
}
.budget-alert.show { display: flex; }
.budget-alert-row { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #ffcdd2; }
.budget-alert-icon { font-size: 16px; flex-shrink: 0; }
.budget-alert-txt { flex: 1; line-height: 1.5; }
.budget-alert-txt b { color: #ff8080; display: block; }

.budget-item {
  background: rgba(255,255,255,.03); border-radius: 11px;
  padding: 11px 13px; border: 1px solid var(--border);
  margin-bottom: 7px; transition: border-color .2s;
}
.budget-item:hover { border-color: var(--border2); }
.budget-item-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.budget-cat { font-size: 13px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 6px; }
.budget-nums { display: flex; align-items: center; gap: 5px; }
.budget-spent { font-size: 12px; font-weight: 700; color: var(--gold); }
.budget-limit { font-size: 11px; color: var(--text3); }
.budget-track-bg {
  background: rgba(255,255,255,.06); border-radius: 20px;
  height: 7px; overflow: hidden; margin-bottom: 5px;
}
.budget-track-fill {
  height: 100%; border-radius: 20px;
  background: linear-gradient(90deg, var(--crimson), var(--gold));
  transition: width .8s ease;
}
.budget-track-fill.warn   { background: linear-gradient(90deg, #7a3000, #ff9800); }
.budget-track-fill.danger { background: linear-gradient(90deg, #7a0000, #f44336); }
.budget-foot { display: flex; justify-content: space-between; font-size: 10px; color: var(--text3); }
.budget-remain.over { color: #f44336; }

/* ═══════════════════════════════════════════
   GOALS
═══════════════════════════════════════════ */
.goal-item {
  background: rgba(255,255,255,.03); border-radius: 11px;
  padding: 12px; border: 1px solid var(--border);
  margin-bottom: 7px; transition: border-color .2s;
}
.goal-item:hover { border-color: var(--border2); }
.goal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.goal-name { font-size: 14px; font-weight: 700; color: var(--text); }
.goal-amounts { font-size: 11px; color: var(--text3); }
.goal-track-bg { background: rgba(255,255,255,.06); border-radius: 10px; height: 7px; overflow: hidden; margin-bottom: 4px; }
.goal-track-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, var(--sage), var(--gold)); transition: width .8s ease; }
.goal-pct { font-size: 11px; color: var(--text3); }

/* ═══════════════════════════════════════════
   CHARTS
═══════════════════════════════════════════ */
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.chart-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 14px;
}
.chart-title { font-size: 12px; font-weight: 700; color: var(--text2); margin-bottom: 12px; }
.pie-wrap { display: flex; gap: 10px; align-items: center; }
.pie-legend { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.pie-item { display: flex; align-items: center; gap: 6px; font-size: 11px; }
.pie-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.pie-lbl { flex: 1; color: var(--text3); }
.pie-pct { color: var(--text); font-weight: 700; }
.cmp-row { display: flex; gap: 6px; align-items: center; margin-bottom: 7px; font-size: 11px; }
.cmp-lbl { width: 65px; color: var(--text3); }
.cmp-bar-bg { flex: 1; background: rgba(255,255,255,.06); border-radius: 5px; height: 8px; overflow: hidden; }
.cmp-bar-fill { height: 100%; border-radius: 5px; transition: width .8s ease; }
.cmp-val { width: 55px; text-align: left; font-weight: 700; color: var(--text2); }

/* ═══════════════════════════════════════════
   TIP
═══════════════════════════════════════════ */
.tip-bar {
  background: rgba(201,169,110,.06); border: 1px solid rgba(201,169,110,.15);
  border-radius: var(--r-sm); padding: 11px 13px;
  display: flex; gap: 9px; align-items: center; margin-bottom: 12px;
  animation: fadeIn .5s .5s ease both;
}
.tip-text { flex: 1; font-size: 12px; color: var(--text2); line-height: 1.6; }
.tip-next-btn {
  background: rgba(201,169,110,.12); border: 1px solid var(--border);
  color: var(--gold); padding: 4px 10px; border-radius: 7px;
  cursor: pointer; font-size: 11px; font-family: var(--font-body);
  transition: all .2s; white-space: nowrap;
}
.tip-next-btn:hover { background: rgba(201,169,110,.2); }

/* ═══════════════════════════════════════════
   ACHIEVEMENTS
═══════════════════════════════════════════ */
.ach-grid { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 11px; }
.ach-badge {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 9px 8px; background: rgba(255,255,255,.03); border-radius: 11px;
  border: 1px solid var(--border); min-width: 58px; transition: all .25s;
}
.ach-badge:hover { transform: scale(1.06); }
.ach-badge.on { border-color: rgba(201,169,110,.3); background: var(--gold-dim); }
.ach-badge.off { opacity: .28; filter: grayscale(1); }
.ach-icon { font-size: 22px; }
.ach-name { font-size: 9px; text-align: center; color: var(--text3); line-height: 1.3; }
.ach-pts { font-size: 9px; font-weight: 700; color: var(--text3); }
.ach-badge.on .ach-pts { color: var(--gold); }

/* ═══════════════════════════════════════════
   POINTS BAR
═══════════════════════════════════════════ */
.pts-bar {
  background: linear-gradient(135deg, rgba(201,169,110,.06), rgba(21,10,13,.7));
  border: 1px solid rgba(201,169,110,.15);
  border-radius: var(--r-sm); padding: 10px 14px;
  display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
  animation: fadeIn .5s .45s ease both;
}
.pts-icon { font-size: 18px; }
.pts-val {
  font-family: var(--font-display); font-size: 20px; font-weight: 900; color: var(--gold);
}
.pts-lbl { font-size: 11px; color: var(--text3); }
.pts-level {
  margin-right: auto; font-size: 12px; font-weight: 700;
  background: var(--gold-dim); border: 1px solid rgba(201,169,110,.2);
  color: var(--gold2); padding: 3px 10px; border-radius: 9px;
}

/* ═══════════════════════════════════════════
   QUICK ADD BAR (BOTTOM)
═══════════════════════════════════════════ */
.quick-bar {
  position: fixed; bottom: 0; left: 0; right: 0; z-index: 300;
  background: rgba(13,6,8,.97); border-top: 1px solid var(--border);
  padding: 8px 12px 14px;
  display: flex; gap: 7px; align-items: center;
  backdrop-filter: blur(20px);
}
.qa-types { display: flex; gap: 4px; flex-shrink: 0; }
.qa-type-btn {
  width: 34px; height: 34px; border-radius: 9px;
  border: 1.5px solid var(--border); background: transparent;
  cursor: pointer; font-size: 14px;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s; color: var(--text3);
}
.qa-type-btn.expense.active  { background: var(--crimson-dim); border-color: rgba(155,48,68,.6); color: var(--text); }
.qa-type-btn.income.active   { background: var(--sage-dim); border-color: rgba(74,140,106,.5); color: var(--text); }

.qa-field {
  flex: 1; display: flex; gap: 5px; align-items: center;
  background: rgba(255,255,255,.05); border: 1.5px solid var(--border);
  border-radius: 11px; padding: 7px 11px;
  transition: border-color .2s;
}
.qa-field:focus-within { border-color: rgba(201,169,110,.4); }
.qa-input {
  flex: 1; background: none; border: none; outline: none;
  color: var(--text); font-family: var(--font-body); font-size: 13px; direction: rtl;
}
.qa-input::placeholder { color: var(--text3); }
.qa-sep { width: 1px; height: 16px; background: var(--border); flex-shrink: 0; }
.qa-amount {
  width: 65px; background: none; border: none; outline: none;
  color: var(--text); font-family: var(--font-body); font-size: 13px; text-align: left;
}
.qa-submit {
  width: 38px; height: 38px; border-radius: 11px; border: none;
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  color: white; font-size: 16px; cursor: pointer; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s; box-shadow: 0 3px 12px rgba(122,37,53,.4);
}
.qa-submit:hover { transform: scale(1.06); }

/* ═══════════════════════════════════════════
   SAVE BAR
═══════════════════════════════════════════ */
.save-wrap {
  position: fixed; bottom: 66px; left: 50%; transform: translateX(-50%);
  z-index: 290; opacity: 0; pointer-events: none;
  transition: opacity .35s;
}
.save-wrap.dirty { opacity: 1; pointer-events: all; }
.save-btn-main {
  background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  color: var(--text); border: none; border-radius: 22px;
  padding: 9px 20px; font-size: 13px; font-weight: 800;
  cursor: pointer; font-family: var(--font-display);
  box-shadow: 0 4px 18px rgba(122,37,53,.5);
  display: flex; align-items: center; gap: 6px;
  transition: all .2s; white-space: nowrap;
}
.save-btn-main:hover { transform: scale(1.04); }
.save-btn-main.saved { background: rgba(74,140,106,.4); color: var(--sage2); }

/* ═══════════════════════════════════════════
   TOAST
═══════════════════════════════════════════ */
#toastWrap {
  position: fixed; top: 68px; left: 50%; transform: translateX(-50%);
  z-index: 9999; display: flex; flex-direction: column; gap: 6px;
  pointer-events: none; align-items: center;
}
.toast {
  background: rgba(21,10,13,.97); border: 1px solid var(--border);
  border-radius: 12px; padding: 10px 18px;
  font-size: 13px; font-weight: 600; color: var(--text2);
  box-shadow: var(--shadow); animation: toastIn .3s ease;
  white-space: nowrap;
}
.toast.success { border-color: rgba(74,140,106,.4); color: var(--sage2); }
.toast.warn    { border-color: rgba(201,169,110,.4); color: var(--gold); }
.toast.danger  { border-color: rgba(122,37,53,.5); color: #ff8080; }
@keyframes toastIn { from { opacity:0; transform:translateY(-8px); } to { opacity:1; transform:translateY(0); } }

/* ═══════════════════════════════════════════
   YEARLY VIEW
═══════════════════════════════════════════ */
.ycards { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; margin-bottom: 12px; }
.ycard {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 14px; text-align: center;
  transition: all .25s;
}
.ycard:hover { border-color: var(--border2); transform: translateY(-2px); }
.ycard-icon { font-size: 24px; margin-bottom: 5px; }
.ycard-val {
  font-family: var(--font-display); font-size: 18px; font-weight: 900; color: var(--gold);
}
.ycard-lbl { font-size: 11px; color: var(--text3); margin-top: 3px; }

.year-bars-card {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-md); padding: 15px; margin-bottom: 12px;
}
.year-bars { display: flex; gap: 3px; align-items: flex-end; height: 90px; margin-bottom: 6px; }
.year-bar-wrap { flex: 1; display: flex; gap: 2px; align-items: flex-end; justify-content: center; height: 100%; }
.year-bar {
  flex: 1; border-radius: 3px 3px 0 0; min-height: 2px;
  transition: height .6s ease;
}
.year-bar.income  { background: var(--sage2); opacity: .8; }
.year-bar.expense { background: var(--crimson2); opacity: .8; }
.year-lbrs { display: flex; gap: 3px; }
.year-lbl { flex: 1; text-align: center; font-size: 8px; color: var(--text3); }
.year-legend { display: flex; gap: 12px; margin-top: 8px; }
.year-leg-item { display: flex; align-items: center; gap: 5px; font-size: 9px; color: var(--text3); }
.year-leg-dot { width: 7px; height: 7px; border-radius: 2px; }

/* ═══════════════════════════════════════════
   NOTIFICATIONS PANEL
═══════════════════════════════════════════ */
.notif-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.6); z-index: 400;
  opacity: 0; pointer-events: none; transition: opacity .3s;
}
.notif-overlay.open { opacity: 1; pointer-events: all; }

.notif-panel {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: min(380px, 100vw);
  background: linear-gradient(160deg, #120608, #0a0406);
  border-left: 1px solid var(--border); z-index: 401;
  transform: translateX(100%); transition: transform .35s cubic-bezier(.4,0,.2,1);
  display: flex; flex-direction: column; overflow: hidden;
}
.notif-panel.open { transform: translateX(0); }
.notif-panel-head {
  padding: 16px 14px 12px;
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
  flex-shrink: 0;
}
.notif-panel-title { font-size: 16px; font-weight: 800; color: var(--text); }
.notif-panel-close {
  background: none; border: none; color: var(--text3);
  cursor: pointer; font-size: 18px; padding: 4px;
  transition: color .2s;
}
.notif-panel-close:hover { color: var(--text); }
.notif-panel-body { flex: 1; overflow-y: auto; padding: 11px 13px; display: flex; flex-direction: column; gap: 7px; }
.notif-panel-footer { padding: 11px 13px; border-top: 1px solid var(--border); flex-shrink: 0; max-height: 55vh; overflow-y: auto; }
.notif-item {
  background: rgba(255,255,255,.04); border-radius: 11px;
  padding: 12px; border: 1px solid var(--border);
  display: flex; gap: 10px; align-items: flex-start; transition: border-color .2s;
}
.notif-item.urgent  { border-color: rgba(220,60,60,.3); background: rgba(100,15,15,.15); }
.notif-item.warning { border-color: rgba(200,140,20,.25); background: rgba(80,50,5,.12); }
.notif-item.done    { opacity: .35; border-style: dashed; }
.notif-icon { font-size: 22px; flex-shrink: 0; }
.notif-body { flex: 1; min-width: 0; }
.notif-name { font-size: 13px; font-weight: 700; color: var(--text); margin-bottom: 2px; }
.notif-amt {
  font-family: var(--font-display); font-size: 17px; font-weight: 900;
  color: var(--gold); margin-bottom: 3px;
}
.notif-meta { font-size: 10px; color: var(--text3); display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.notif-sbadge { font-size: 10px; font-weight: 700; padding: 2px 7px; border-radius: 8px; }
.notif-sbadge.overdue  { background: rgba(200,40,40,.2); color: #ff8080; }
.notif-sbadge.soon     { background: rgba(200,140,20,.15); color: #ffc060; }
.notif-sbadge.upcoming { background: rgba(201,169,110,.08); color: var(--gold); }
.notif-sbadge.paid     { background: rgba(74,140,106,.12); color: var(--sage2); }
.notif-actions { display: flex; flex-direction: column; gap: 4px; align-items: center; }
.notif-check {
  width: 28px; height: 28px; border-radius: 8px;
  border: 1.5px solid var(--border); background: transparent;
  cursor: pointer; font-size: 12px; color: var(--text3);
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.notif-check:hover { border-color: var(--gold); color: var(--gold); }
.notif-check.checked { background: rgba(74,140,106,.18); border-color: var(--sage2); color: var(--sage2); }
.notif-del-btn { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 11px; padding: 2px; }
.notif-del-btn:hover { color: var(--crimson2); }

.notif-add-form {
  background: rgba(255,255,255,.03); border-radius: 12px;
  padding: 12px; border: 1px solid var(--border);
}
.notif-add-title { font-size: 11px; font-weight: 700; color: var(--gold); margin-bottom: 9px; }
.notif-fi {
  flex: 1; min-width: 80px;
  background: rgba(255,255,255,.05); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; color: var(--text);
  font-family: var(--font-body); font-size: 12px; outline: none; direction: rtl;
}
.notif-fi:focus { border-color: rgba(201,169,110,.4); }
.notif-fi::placeholder { color: var(--text3); }
.notif-fi-sel {
  flex: 1; background: rgba(255,255,255,.05); border: 1px solid var(--border);
  border-radius: 8px; padding: 8px 10px; color: var(--text);
  font-family: var(--font-body); font-size: 12px; outline: none; cursor: pointer;
}
.notif-fi-sel option { background: #1e0e12; }
.notif-add-btn {
  width: 100%; background: linear-gradient(135deg, var(--crimson), var(--crimson2));
  color: var(--text); border: none; padding: 9px; border-radius: 9px;
  font-size: 12px; font-weight: 800; cursor: pointer; font-family: var(--font-body);
  transition: all .2s; margin-top: 3px;
}
.notif-add-btn:hover { opacity: .88; }
.day-chips { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 6px; }
.day-chip {
  background: rgba(255,255,255,.04); border: 1px solid var(--border);
  border-radius: 7px; padding: 3px 8px; font-size: 10px;
  cursor: pointer; color: var(--text3); transition: all .2s;
  font-family: var(--font-body);
}
.day-chip:hover, .day-chip.sel {
  background: var(--crimson-dim); border-color: rgba(201,169,110,.3); color: var(--text);
}
.notif-section-lbl { font-size: 10px; font-weight: 700; color: var(--text3); letter-spacing: .8px; padding: 2px 0; }
.notif-empty { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; padding: 30px; text-align: center; }
.notif-empty-icon { font-size: 40px; opacity: .25; }
.notif-empty-text { color: var(--text3); font-size: 12px; line-height: 1.6; }

/* ═══════════════════════════════════════════
   SEARCH
═══════════════════════════════════════════ */
.search-bar {
  background: var(--bg3); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 9px 12px;
  display: flex; gap: 8px; align-items: center; margin-bottom: 10px;
}
.search-input {
  flex: 1; background: none; border: none; outline: none;
  color: var(--text); font-family: var(--font-body); font-size: 13px; direction: rtl;
}
.search-input::placeholder { color: var(--text3); }
.search-clear {
  background: none; border: none; color: var(--text3);
  cursor: pointer; font-size: 12px; transition: color .2s;
}
.search-clear:hover { color: var(--text); }
.search-results { display: flex; flex-direction: column; gap: 4px; margin-top: 7px; max-height: 150px; overflow-y: auto; }

/* ═══════════════════════════════════════════
   YEAR SELECTOR
═══════════════════════════════════════════ */
.year-selector {
  background: rgba(255,255,255,.03); border: 1px solid var(--border);
  border-radius: var(--r-sm); padding: 10px 13px;
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 12px;
}
.year-lbl { font-size: 12px; color: var(--text3); font-weight: 700; }
.year-btns { display: flex; gap: 5px; flex-wrap: wrap; }
.year-btn {
  background: rgba(255,255,255,.04); border: 1px solid var(--border);
  color: var(--text3); padding: 3px 11px; border-radius: 8px;
  cursor: pointer; font-size: 12px; font-family: var(--font-body); transition: all .2s;
}
.year-btn:hover { border-color: var(--gold); color: var(--gold); }
.year-btn.active { background: var(--gold); color: var(--bg); font-weight: 700; border-color: var(--gold); }
.year-input {
  background: rgba(255,255,255,.04); border: 1px solid var(--border);
  color: var(--text); padding: 3px 9px; border-radius: 8px;
  font-size: 12px; font-family: var(--font-body); width: 80px; outline: none;
}
.year-go {
  background: var(--crimson); border: none; color: var(--text);
  padding: 3px 10px; border-radius: 8px; font-size: 12px; cursor: pointer;
  font-family: var(--font-body);
}

/* ═══════════════════════════════════════════
   MISC UTILITIES
═══════════════════════════════════════════ */
@keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }

.footer {
  text-align: center; padding: 40px 16px 12px;
  color: var(--text3); font-size: 11px;
  border-top: 1px solid rgba(255,255,255,.04);
  position: relative; z-index: 1;
}

@media (max-width:480px) {
  .charts-grid { grid-template-columns: 1fr; }
  .ycards { grid-template-columns: 1fr 1fr; }
}
</style>
</head>
<body>

<!-- ═══════════════ NOTIFICATION PANEL ═══════════════ -->
<div class="notif-overlay" id="notifOverlay" onclick="closeNotifPanel()"></div>
<div class="notif-panel" id="notifPanel">
  <div class="notif-panel-head">
    <div class="notif-panel-title">🔔 المستحقات والتنبيهات</div>
    <button class="notif-panel-close" onclick="closeNotifPanel()">✕</button>
  </div>
  <div class="notif-panel-body" id="notifPanelBody"></div>
  <div class="notif-panel-footer">
    <div class="notif-add-form">
      <div class="notif-add-title">➕ أضف تنبيهاً جديداً</div>
      <div class="day-chips" id="notifCatChips">
        <span class="day-chip" onclick="notifSetCat('🏠','إيجار')">🏠 إيجار</span>
        <span class="day-chip" onclick="notifSetCat('🚗','قسط سيارة')">🚗 قسط</span>
        <span class="day-chip" onclick="notifSetCat('📱','جوال/نت')">📱 جوال</span>
        <span class="day-chip" onclick="notifSetCat('📺','اشتراكات')">📺 اشتراكات</span>
        <span class="day-chip" onclick="notifSetCat('💡','فواتير')">💡 فواتير</span>
        <span class="day-chip" onclick="notifSetCat('🏦','قسط بنكي')">🏦 بنك</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:6px">
        <input class="notif-fi" id="nfName" type="text" placeholder="اسم المستحق">
        <input class="notif-fi" id="nfIcon" type="text" value="🏠" style="max-width:55px;text-align:center">
      </div>
      <div style="display:flex;gap:6px;margin-bottom:6px">
        <input class="notif-fi" id="nfAmt" type="number" placeholder="المبلغ ﷼" style="max-width:110px">
        <select class="notif-fi-sel" id="nfAlert">
          <option value="3">قبل ٣ أيام</option>
          <option value="5" selected>قبل ٥ أيام</option>
          <option value="7">قبل ٧ أيام</option>
          <option value="10">قبل ١٠ أيام</option>
        </select>
      </div>
      <div style="font-size:10px;color:var(--text3);margin-bottom:5px">📅 يوم الاستحقاق:</div>
      <div class="day-chips" id="dayChips">
        <span class="day-chip" onclick="notifSetDay(1)">١</span>
        <span class="day-chip" onclick="notifSetDay(5)">٥</span>
        <span class="day-chip" onclick="notifSetDay(10)">١٠</span>
        <span class="day-chip" onclick="notifSetDay(15)">١٥</span>
        <span class="day-chip" onclick="notifSetDay(20)">٢٠</span>
        <span class="day-chip" onclick="notifSetDay(25)">٢٥</span>
        <span class="day-chip" onclick="notifSetDay(28)">٢٨</span>
      </div>
      <div style="display:flex;gap:6px;margin-bottom:7px">
        <input class="notif-fi" id="nfDay" type="number" placeholder="يوم (١-٣١)" min="1" max="31">
      </div>
      <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text3);cursor:pointer;margin-bottom:8px">
        <input type="checkbox" id="nfRecurring" checked style="accent-color:var(--gold)"> يتكرر شهرياً 🔄
      </label>
      <button class="notif-add-btn" onclick="addNotif()">✅ أضف التنبيه</button>
    </div>
  </div>
</div>

<!-- ═══════════════ HEADER ═══════════════ -->
<header class="header">
  <div class="header-inner">
    <div class="logo" onclick="showTab('monthly')">
      <div class="logo-mark">💰</div>
      <div class="logo-name">فلونس</div>
    </div>
    <div class="header-spacer"></div>
    <div class="month-nav" id="monthNav">
      <button class="month-arrow" onclick="changeMonth(-1)">‹</button>
      <div class="month-label" id="monthLbl">—</div>
      <button class="month-arrow" onclick="changeMonth(1)">›</button>
    </div>
    <button class="bell-btn" id="bellBtn" onclick="openNotifPanel()">
      🔔<div class="bell-dot" id="bellDot"></div>
    </button>
    <div class="nav-pill">
      <button class="nav-btn active" id="tabM" onclick="showTab('monthly')">الشهر</button>
      <button class="nav-btn" id="tabY" onclick="showTab('yearly')">السنة</button>
    </div>
  </div>
</header>

<!-- ═══════════════ TOAST ═══════════════ -->
<div id="toastWrap"></div>

<!-- ═══════════════ SAVE BAR ═══════════════ -->
<div class="save-wrap" id="saveWrap">
  <button class="save-btn-main" id="saveBtn" onclick="saveAll()">💾 احفظ التغييرات</button>
</div>

<!-- ═══════════════ QUICK ADD ═══════════════ -->
<div class="quick-bar">
  <div class="qa-types">
    <button class="qa-type-btn expense active" id="qaBtnOut" onclick="qaSetType('out')" title="مصروف">💸</button>
    <button class="qa-type-btn income" id="qaBtnIn"  onclick="qaSetType('in')"  title="دخل">💵</button>
  </div>
  <div class="qa-field">
    <input class="qa-input" id="qaName" placeholder="وش صرفت على؟" onkeydown="if(event.key==='Enter')qaSubmit()">
    <div class="qa-sep"></div>
    <input class="qa-amount" id="qaAmt" type="number" placeholder="ريال" onkeydown="if(event.key==='Enter')qaSubmit()">
  </div>
  <button class="qa-submit" onclick="qaSubmit()">✓</button>
</div>

<!-- ═══════════════ MAIN ═══════════════ -->
<main class="main">

<!-- MONTHLY VIEW -->
<div id="viewMonthly">

  <div class="year-selector">
    <div class="year-lbl">📅 السنة:</div>
    <div class="year-btns" id="yearBtns"></div>
    <input class="year-input" id="yearCustom" type="number" placeholder="أخرى">
    <button class="year-go" onclick="goYear()">انتقل</button>
  </div>

  <!-- Salary Strip -->
  <div class="salary-strip">
    <div class="salary-icon">💰</div>
    <div class="salary-body">
      <div class="salary-label">يوم نزول الراتب</div>
      <div class="salary-row">
        <span style="font-size:12px;color:var(--text3)">كل شهر يوم:</span>
        <select class="salary-select" id="salarySelect" onchange="setSalaryDay(this.value)"></select>
        <div class="salary-badge" id="salaryCd">اختر يوم</div>
      </div>
    </div>
  </div>

  <!-- Streak -->
  <div class="streak-card">
    <div class="streak-head">
      <div>
        <div class="streak-title">سلسلة المتابعة اليومية</div>
        <div style="font-size:10px;color:var(--text3);margin-top:2px">سجّل حضورك كل يوم وابني سلسلتك 🔥</div>
      </div>
      <div class="streak-flame">🔥</div>
    </div>
    <div class="streak-num" id="streakNum">0</div>
    <div class="streak-sub">يوم متتالي</div>
    <div class="streak-dots" id="streakDots"></div>
    <button class="streak-checkin" id="streakBtn" onclick="doCheckin()">🔥 سجّل حضورك اليوم</button>
    <div class="streak-msg" id="streakMsg"></div>
    <div class="streak-stats">
      <div class="streak-stat"><div class="streak-stat-num" id="sCur">0</div><div class="streak-stat-lbl">الحالية</div></div>
      <div class="streak-stat"><div class="streak-stat-num" id="sMax">0</div><div class="streak-stat-lbl">الأطول</div></div>
      <div class="streak-stat"><div class="streak-stat-num" id="sTot">0</div><div class="streak-stat-lbl">إجمالي</div></div>
    </div>
  </div>

  <!-- AI Insight -->
  <div class="ai-insight">
    <div class="ai-orb" onclick="refreshAI()">🧠</div>
    <div>
      <div class="ai-label">🤖 تحليل ذكي</div>
      <div class="ai-text" id="aiText">أضف بياناتك أول عشان أحللها لك ✨</div>
    </div>
  </div>

  <!-- Points -->
  <div class="pts-bar">
    <div class="pts-icon">⭐</div>
    <div>
      <div class="pts-val" id="ptsVal">0</div>
      <div class="pts-lbl">نقطة</div>
    </div>
    <div class="pts-level" id="ptsLevel">مبتدئ 🌱</div>
  </div>

  <!-- Cards -->
  <div class="cards-grid">
    <div class="card income">
      <div class="card-head">
        <div class="card-icon">💵</div>
        <div class="card-badge" id="incBadge">—</div>
      </div>
      <div class="card-label">الدخل</div>
      <div class="card-value" id="tInc">٠ ﷼</div>
      <div class="card-bar"><div class="card-bar-fill" id="incBar" style="width:0%"></div></div>
    </div>
    <div class="card expense">
      <div class="card-head">
        <div class="card-icon">💸</div>
        <div class="card-badge" id="expBadge">—</div>
      </div>
      <div class="card-label">المصاريف</div>
      <div class="card-value" id="tExp">٠ ﷼</div>
      <div class="card-bar"><div class="card-bar-fill" id="expBar" style="width:0%"></div></div>
    </div>
    <div class="card saved">
      <div class="card-head">
        <div class="card-icon">🏦</div>
        <div class="card-badge" id="savBadge">—</div>
      </div>
      <div class="card-label">التوفير</div>
      <div class="card-value" id="tSav">٠ ﷼</div>
    </div>
    <div class="card balance">
      <div class="card-head">
        <div class="card-icon">⚖️</div>
      </div>
      <div class="card-label">الباقي</div>
      <div class="card-value" id="tBal">٠ ﷼</div>
      <div class="card-sub" id="balSub"></div>
    </div>
  </div>

  <!-- Progress -->
  <div class="progress-block">
    <div class="progress-head">
      <div>
        <div class="progress-title">📊 نسبة الإنفاق من الدخل</div>
      </div>
      <div class="progress-pct" id="progPct">٠٪</div>
    </div>
    <div class="progress-track">
      <div class="progress-fill" id="progFill" style="width:0%"></div>
    </div>
    <div class="progress-labels">
      <span id="spentLbl">صرفت: ٠ ﷼</span>
      <span id="incomeLbl">دخلك: ٠ ﷼</span>
    </div>
  </div>

  <!-- Tip -->
  <div class="tip-bar">
    <span style="font-size:16px">💡</span>
    <div class="tip-text" id="tipText"></div>
    <button class="tip-next-btn" onclick="nextTip()">نصيحة ثانية ›</button>
  </div>

  <!-- Search -->
  <div class="search-bar">
    <span style="font-size:13px;color:var(--text3)">🔍</span>
    <input class="search-input" id="searchInput" placeholder="ابحث في المعاملات..." oninput="doSearch(this.value)">
    <button class="search-clear" onclick="clearSearch()">✕</button>
    <div class="search-results" id="searchResults" style="display:none"></div>
  </div>

  <!-- Income Section -->
  <div class="section-card">
    <div class="section-head">
      <div>
        <div class="section-title">💵 مصادر الدخل</div>
        <div class="section-subtitle">راتب، شغل حر، تجارة...</div>
      </div>
      <div style="display:flex;gap:7px;align-items:center">
        <span class="section-total" id="incTotal">٠ ﷼</span>
        <button class="add-trigger" onclick="toggleForm('formIncome')">+ أضف</button>
      </div>
    </div>
    <div class="items-list" id="incList"></div>
    <div class="add-form" id="formIncome">
      <div class="cat-chips">
        <span class="cat-chip" onclick="qSetCat('incCat','💼','incName','راتب')">💼 راتب</span>
        <span class="cat-chip" onclick="qSetCat('incCat','💻','incName','فريلانس')">💻 فريلانس</span>
        <span class="cat-chip" onclick="qSetCat('incCat','🏪','incName','تجارة')">🏪 تجارة</span>
        <span class="cat-chip" onclick="qSetCat('incCat','📦','incName','استثمار')">📦 استثمار</span>
      </div>
      <div class="form-row">
        <input class="form-input" id="incName" type="text" placeholder="مثل: راتب، فريلانس...">
        <input class="form-input" id="incAmt"  type="number" placeholder="المبلغ ﷼" style="max-width:110px">
        <select class="form-select" id="incCat" style="max-width:110px">
          <option value="💼">💼 راتب</option>
          <option value="💻">💻 فريلانس</option>
          <option value="🏪">🏪 تجارة</option>
          <option value="📦">📦 استثمار</option>
          <option value="🎁">🎁 هدية</option>
          <option value="➕">➕ غير ذلك</option>
        </select>
        <button class="form-btn" onclick="addItem('income')">سجّل</button>
      </div>
      <div class="amt-shortcuts">
        <span class="amt-sh" onclick="setAmt('incAmt',1000)">١٠٠٠</span>
        <span class="amt-sh" onclick="setAmt('incAmt',3000)">٣٠٠٠</span>
        <span class="amt-sh" onclick="setAmt('incAmt',5000)">٥٠٠٠</span>
        <span class="amt-sh" onclick="setAmt('incAmt',10000)">١٠٠٠٠</span>
        <span class="amt-sh" onclick="setAmt('incAmt',15000)">١٥٠٠٠</span>
      </div>
      <label class="form-check"><input type="checkbox" id="incRec"> كرره كل شهر 🔄</label>
    </div>
  </div>

  <!-- Fixed Expenses -->
  <div class="section-card">
    <div class="section-head">
      <div>
        <div class="section-title">🏠 المصاريف الثابتة</div>
        <div class="section-subtitle">إيجار، قسط، اشتراكات...</div>
      </div>
      <div style="display:flex;gap:7px;align-items:center">
        <span class="section-total" id="fixTotal">٠ ﷼</span>
        <button class="add-trigger" onclick="toggleForm('formFixed')">+ أضف</button>
      </div>
    </div>
    <div class="items-list" id="fixList"></div>
    <div class="add-form" id="formFixed">
      <div class="form-row">
        <input class="form-input" id="fixName" type="text" placeholder="مثل: إيجار، نت...">
        <input class="form-input" id="fixAmt"  type="number" placeholder="المبلغ ﷼" style="max-width:110px">
        <select class="form-select" id="fixCat" style="max-width:110px">
          <option value="🏠">🏠 إيجار</option>
          <option value="💡">💡 كهرباء/ماء</option>
          <option value="📱">📱 جوال/نت</option>
          <option value="🚗">🚗 سيارة</option>
          <option value="🏦">🏦 قسط</option>
          <option value="📺">📺 اشتراكات</option>
          <option value="➕">➕ غير ذلك</option>
        </select>
        <button class="form-btn" onclick="addItem('fixed')">سجّل</button>
      </div>
      <label class="form-check"><input type="checkbox" id="fixRec" checked> كرره كل شهر 🔄</label>
    </div>
  </div>

  <!-- Variable Expenses -->
  <div class="section-card">
    <div class="section-head">
      <div>
        <div class="section-title">📝 المشتريات اليومية</div>
        <div class="section-subtitle">سجّل كل ما تصرف يومياً</div>
      </div>
      <div style="display:flex;gap:7px;align-items:center">
        <span class="section-total" id="varTotal">٠ ﷼</span>
        <button class="add-trigger" onclick="toggleForm('formVar')">+ أضف</button>
      </div>
    </div>
    <div class="items-list" id="varList"></div>
    <div class="add-form" id="formVar">
      <div class="cat-chips">
        <span class="cat-chip" onclick="qSetCat('varCat','🛒','varName','بقالة')">🛒 بقالة</span>
        <span class="cat-chip" onclick="qSetCat('varCat','🍽️','varName','مطعم')">🍽️ مطعم</span>
        <span class="cat-chip" onclick="qSetCat('varCat','🎮','varName','ترفيه')">🎮 ترفيه</span>
        <span class="cat-chip" onclick="qSetCat('varCat','💄','varName','عناية')">💄 عناية</span>
        <span class="cat-chip" onclick="qSetCat('varCat','✈️','varName','سفر')">✈️ سفر</span>
        <span class="cat-chip" onclick="qSetCat('varCat','🏥','varName','صحة')">🏥 صحة</span>
      </div>
      <div class="form-row">
        <input class="form-input" id="varName" type="text" placeholder="مثل: غداء، قهوة...">
        <input class="form-input" id="varAmt"  type="number" placeholder="المبلغ ﷼" style="max-width:110px">
        <select class="form-select" id="varCat" style="max-width:110px">
          <option value="🛒">🛒 بقالة</option>
          <option value="🍽️">🍽️ مطاعم</option>
          <option value="👗">👗 ملابس</option>
          <option value="💄">💄 عناية</option>
          <option value="🎮">🎮 ترفيه</option>
          <option value="✈️">✈️ سفر</option>
          <option value="🏥">🏥 صحة</option>
          <option value="🎁">🎁 هدايا</option>
          <option value="➕">➕ غير ذلك</option>
        </select>
        <button class="form-btn" onclick="addItem('variable')">سجّل</button>
      </div>
      <div class="amt-shortcuts">
        <span class="amt-sh" onclick="setAmt('varAmt',20)">٢٠</span>
        <span class="amt-sh" onclick="setAmt('varAmt',50)">٥٠</span>
        <span class="amt-sh" onclick="setAmt('varAmt',100)">١٠٠</span>
        <span class="amt-sh" onclick="setAmt('varAmt',200)">٢٠٠</span>
        <span class="amt-sh" onclick="setAmt('varAmt',500)">٥٠٠</span>
      </div>
    </div>
  </div>

  <!-- Goals -->
  <div class="section-card">
    <div class="section-head">
      <div>
        <div class="section-title">🎯 الأهداف المالية</div>
        <div class="section-subtitle">سفر، سيارة، زواج...</div>
      </div>
      <button class="add-trigger" onclick="toggleForm('formGoal')">+ هدف</button>
    </div>
    <div id="goalList"></div>
    <div class="add-form" id="formGoal">
      <div class="form-row">
        <input class="form-input" id="goalName"   type="text"   placeholder="اسم الهدف">
        <input class="form-input" id="goalTarget" type="number" placeholder="المبلغ المستهدف">
        <input class="form-input" id="goalSaved"  type="number" placeholder="وفّرت لحد الآن">
        <select class="form-select" id="goalIcon" style="max-width:90px">
          <option value="✈️">✈️ سفر</option>
          <option value="🚗">🚗 سيارة</option>
          <option value="🏠">🏠 بيت</option>
          <option value="💍">💍 زواج</option>
          <option value="📱">📱 جهاز</option>
          <option value="🎓">🎓 دراسة</option>
          <option value="🆘">🆘 طوارئ</option>
          <option value="⭐">⭐ أخرى</option>
        </select>
        <button class="form-btn" onclick="addGoal()">سجّل</button>
      </div>
    </div>
  </div>

  <!-- Budget Categories -->
  <div class="section-card">
    <div class="section-head">
      <div>
        <div class="section-title">🎯 ميزانية الفئات</div>
        <div class="section-subtitle">حدد سقفاً لكل نوع إنفاق</div>
      </div>
      <button class="add-trigger" onclick="toggleForm('formBudget')">+ فئة</button>
    </div>
    <div class="budget-alert" id="budgetAlert"></div>
    <div id="budgetItems"></div>
    <div class="add-form" id="formBudget">
      <div class="form-row">
        <select class="form-select" id="bcCat">
          <option value="🍽️ مطاعم">🍽️ مطاعم</option>
          <option value="🎮 ترفيه">🎮 ترفيه</option>
          <option value="🛒 بقالة">🛒 بقالة</option>
          <option value="👗 ملابس">👗 ملابس</option>
          <option value="✈️ سفر">✈️ سفر</option>
          <option value="🏥 صحة">🏥 صحة</option>
          <option value="💄 عناية">💄 عناية</option>
          <option value="⛽ بنزين">⛽ بنزين</option>
        </select>
        <input class="form-input" id="bcName"  type="text"   placeholder="أو اكتب اسم فئة">
        <input class="form-input" id="bcLimit" type="number" placeholder="الحد ﷼" style="max-width:100px">
        <button class="form-btn" onclick="addBudgetCat()">سجّل</button>
      </div>
    </div>
  </div>

  <!-- Achievements -->
  <div class="section-card">
    <div class="section-head">
      <div class="section-title">🏆 الإنجازات</div>
    </div>
    <div class="ach-grid" id="achGrid"></div>
  </div>

  <!-- Charts -->
  <div class="charts-grid">
    <div class="chart-card">
      <div class="chart-title">🥧 توزيع المصاريف</div>
      <div class="pie-wrap">
        <svg width="80" height="80" viewBox="0 0 100 100" id="pieChart" style="flex-shrink:0"></svg>
        <div class="pie-legend" id="pieLegend"></div>
      </div>
    </div>
    <div class="chart-card">
      <div class="chart-title">📊 مقارنة الشهرين</div>
      <div id="cmpChart"></div>
    </div>
  </div>

</div><!-- /viewMonthly -->

<!-- YEARLY VIEW -->
<div id="viewYearly" style="display:none">
  <div class="ycards">
    <div class="ycard"><div class="ycard-icon">💵</div><div class="ycard-val" id="yInc">٠</div><div class="ycard-lbl">إجمالي الدخل</div></div>
    <div class="ycard"><div class="ycard-icon">💸</div><div class="ycard-val" id="yExp">٠</div><div class="ycard-lbl">إجمالي المصاريف</div></div>
    <div class="ycard"><div class="ycard-icon">🏦</div><div class="ycard-val" id="ySav">٠</div><div class="ycard-lbl">إجمالي التوفير</div></div>
  </div>
  <div class="year-bars-card">
    <div class="chart-title">📈 الدخل والمصاريف شهرياً</div>
    <div class="year-bars" id="yearBars"></div>
    <div class="year-lbrs" id="yearLbls"></div>
    <div class="year-legend">
      <div class="year-leg-item"><div class="year-leg-dot" style="background:var(--sage2)"></div>دخل</div>
      <div class="year-leg-item"><div class="year-leg-dot" style="background:var(--crimson2)"></div>مصروف</div>
    </div>
  </div>
  <div class="section-card">
    <div class="section-head"><div class="section-title">🏆 الإنجازات السنوية</div></div>
    <div id="yearAch" style="display:flex;gap:7px;flex-wrap:wrap;margin-top:8px"></div>
  </div>
</div>

</main>

<div class="footer">فلونس — مخططك المالي الذكي 🤖 | بياناتك محلية ومؤمّنة 🔒</div>

<!-- ═══════════════ JAVASCRIPT ═══════════════ -->
<script>
'use strict';

// ── Constants ──────────────────────────────────────────────────
const MONTHS = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
const DAYS_IN_MONTH = [31,28,31,30,31,30,31,31,30,31,30,31];
const DAY_NAMES = ['أح','إث','ثل','أر','خم','جم','سب'];
const PIE_COLORS = ['#c9a96e','#7a2535','#4a8c6a','#6a7a9a','#8a6a4a','#5a4a8a','#7a6a4a','#4a7a7a'];
const TIPS = [
  'قاعدة الذهبية: ٥٠٪ احتياجات، ٣٠٪ رغبات، ٢٠٪ توفير 💡',
  'وفّر ١٠٠٠ ﷼ أولاً كصندوق طوارئ — قبل أي شيء 🆘',
  'راجع اشتراكاتك وألغِ ما لا تستخدمه 📺',
  'اكتب قائمة قبل ما تروح الجمعية — توفر ٢٠٪ 🛒',
  'أول ما يدخل الراتب، حوّل للتوفير فوراً 🏦',
  'قبل أي شراء: احتاجه فعلاً ولا بس خاطري؟ 🤔',
  'استثمر في نفسك — كورس أو كتاب يعادل مليون 📚',
  'وفّر أولاً ثم أنفق — مو العكس 💰',
];
const ACHIEVEMENTS = [
  {id:'first_save',icon:'🌱',name:'أول توفير',pts:50},
  {id:'no_exceed',icon:'🛡️',name:'ما تجاوزت',pts:100},
  {id:'save_20',icon:'💎',name:'وفّرت ٢٠٪',pts:200},
  {id:'daily_log',icon:'📅',name:'تسجيل يومي',pts:75},
  {id:'goal_done',icon:'🏆',name:'حققت هدف',pts:300},
  {id:'three_months',icon:'🔥',name:'٣ شهور',pts:500},
];
const LEVELS = [
  {min:0,name:'مبتدئ 🌱'},{min:100,name:'ذكي 💡'},{min:300,name:'محترف 💼'},
  {min:700,name:'خبير 🏆'},{min:1500,name:'ماهر 💎'},{min:3000,name:'أسطورة ⭐'},
];

// ── State ──────────────────────────────────────────────────────
const now = new Date();
let state = {
  year:  now.getFullYear(),
  month: now.getMonth(),
  tab:   'monthly',
  tipIdx: 0,
  qaType: 'out',
  dirty:  false,
  pts:    0,
  salaryDay: 0,
  data:   {},
  streak: {days:[],current:0,max:0,total:0},
  notifs: [],
};

// ── Storage ────────────────────────────────────────────────────
const Storage = {
  save(key, val) {
    try { localStorage.setItem('fl_'+key, JSON.stringify(val)); return true; }
    catch(e) { console.warn('Storage error:', e); return false; }
  },
  load(key, fallback) {
    try {
      const raw = localStorage.getItem('fl_'+key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch(e) { return fallback; }
  },
};

// ── Init ───────────────────────────────────────────────────────
function init() {
  state.data      = Storage.load('data', {});
  state.pts       = Storage.load('pts', 0);
  state.salaryDay = Storage.load('salary', 0);
  state.streak    = Storage.load('streak', {days:[],current:0,max:0,total:0});
  state.notifs    = Storage.load('notifs', []);

  // Migrate old keys
  migrateData();

  buildSalarySelect();
  buildYearBtns();
  renderAll();
  initStreakRender();
  updateBellBadge();
  checkNotifAlerts();

  document.addEventListener('visibilitychange', () => { if(document.hidden) saveAll(); });
  document.addEventListener('keydown', e => {
    if(e.ctrlKey && e.key==='s') { e.preventDefault(); saveAll(); }
    if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
      e.preventDefault(); document.getElementById('qaName')?.focus();
    }
  });

  document.getElementById('tipText').textContent = TIPS[0];
}

function migrateData() {
  Object.keys(state.data).forEach(key => {
    const m = state.data[key];
    if(!m.income)   m.income = [];
    if(!m.fixed)    m.fixed = [];
    if(!m.variable) m.variable = [];
    if(!m.goals)    m.goals = [];
    if(!m.daily)    m.daily = {};
    if(!m.budgets)  m.budgets = [];
  });
}

// ── Selectors ──────────────────────────────────────────────────
const makeKey = (y, m) => `${y}_m${m}`;

function getMonthData(y, m) {
  const key = makeKey(y, m);
  if(!state.data[key]) {
    state.data[key] = { income:[], fixed:[], variable:[], goals:[], daily:{}, budgets:[] };
  }
  return state.data[key];
}

function getTotals(y, m) {
  const d = getMonthData(y, m);
  const sum = arr => arr.reduce((s,x) => s + (Number(x.amt)||0), 0);

  let dailyIn = 0, dailyOut = 0;
  Object.values(d.daily).forEach(arr => {
    arr.forEach(e => { if(e.type==='out') dailyOut+=e.amt; else dailyIn+=e.amt; });
  });

  const income  = sum(d.income) + dailyIn;
  const expense = sum(d.fixed) + sum(d.variable) + dailyOut;
  const save    = income - expense;
  const spendPct = income > 0 ? Math.min(100, Math.round((expense/income)*100)) : 0;
  const savePct  = income > 0 ? Math.round((Math.max(0,save)/income)*100) : 0;
  return { income, expense, save, spendPct, savePct };
}

function getCategorySpending(y, m) {
  const d = getMonthData(y, m);
  const cats = {};
  [...d.variable, ...d.fixed].forEach(({cat,amt}) => { cats[cat] = (cats[cat]||0) + (Number(amt)||0); });
  Object.values(d.daily).forEach(arr => {
    arr.forEach(e => { if(e.type==='out') cats[e.cat] = (cats[e.cat]||0)+e.amt; });
  });
  return cats;
}

// ── Formatters ─────────────────────────────────────────────────
const fmt = n => {
  const v = Math.abs(Math.round(n||0));
  return (n<0?'-':'') + v.toLocaleString('ar-SA');
};

// ── Month Navigation ───────────────────────────────────────────
function changeMonth(d) {
  const date = new Date(state.year, state.month + d, 1);
  state.year  = date.getFullYear();
  state.month = date.getMonth();
  buildYearBtns();
  renderAll();
}

// ── Year Selector ──────────────────────────────────────────────
function buildYearBtns() {
  const cur = new Date().getFullYear();
  const years = [cur-2, cur-1, cur, cur+1];
  document.getElementById('yearBtns').innerHTML = years.map(y =>
    `<button class="year-btn${y===state.year?' active':''}" onclick="setYear(${y})">${y}</button>`
  ).join('');
}
function setYear(y) { state.year=y; buildYearBtns(); renderAll(); }
function goYear() {
  const y = parseInt(document.getElementById('yearCustom').value);
  if(y>=1990&&y<=2100) { setYear(y); document.getElementById('yearCustom').value=''; }
  else toast('سنة غير صحيحة','warn');
}

// ── Render All ─────────────────────────────────────────────────
function renderAll() {
  updateMonthLabel();
  if(state.tab==='monthly') {
    renderSummary();
    renderLists();
    renderCharts();
    renderBudgets();
    renderGoals();
    renderAI();
    renderPts();
    renderAch();
    updateSalaryCountdown();
  } else {
    renderYearly();
  }
}

function updateMonthLabel() {
  document.getElementById('monthLbl').textContent = MONTHS[state.month]+' '+state.year;
}

// ── Summary ────────────────────────────────────────────────────
function renderSummary() {
  const t = getTotals(state.year, state.month);
  const p = getTotals(state.year, state.month > 0 ? state.month-1 : 11);

  setText('tInc', fmt(t.income)+' ﷼');
  setText('tExp', fmt(t.expense)+' ﷼');
  setText('tSav', fmt(Math.max(0,t.save))+' ﷼');
  setText('tBal', fmt(t.income-t.expense)+' ﷼');
  setText('balSub', t.save>=0 ? '✅ ماشي زين' : '⚠️ تجاوزت');

  if(p.income>0) setText('incBadge', (t.income-p.income>=0?'+':'')+fmt(t.income-p.income)+' ﷼');
  setText('savBadge', t.savePct+'٪');
  setText('expBadge', t.spendPct+'٪');

  const maxV = Math.max(t.income, t.expense, 1);
  setStyle('incBar','width', Math.round((t.income/maxV)*100)+'%');
  setStyle('expBar','width', Math.round((t.expense/maxV)*100)+'%');

  const fill = document.getElementById('progFill');
  if(fill) {
    fill.style.width = t.spendPct+'%';
    fill.className = 'progress-fill' + (t.spendPct>90?' danger':t.spendPct>70?' warn':'');
  }
  setText('progPct', t.spendPct+'٪');
  setText('spentLbl', 'صرفت: '+fmt(t.expense)+' ﷼');
  setText('incomeLbl', 'دخلك: '+fmt(t.income)+' ﷼');

  if(t.income>0 && t.spendPct>=90 && !sessionStorage.getItem('alerted_'+makeKey(state.year,state.month))) {
    sessionStorage.setItem('alerted_'+makeKey(state.year,state.month), '1');
    toast('انتبه! صرفت '+t.spendPct+'٪ من ميزانيتك 😬','danger');
  }
}

// ── AI Message ─────────────────────────────────────────────────
function renderAI() {
  const t = getTotals(state.year, state.month);
  let msg = '';
  if(!t.income) msg='أضف دخلك أول عشان أحللها لك ✨';
  else if(t.expense > t.income) msg='⚠️ مصاريفك تتجاوز دخلك — لازم تراجع!';
  else if(t.savePct >= 20) msg=`ماشاء الله! توفيرك ${t.savePct}٪ — أنت تمشي صح 🌟`;
  else msg=`توفيرك ${t.savePct}٪ — حاول توصل ٢٠٪ 📊`;
  setText('aiText', msg);
}
function refreshAI() { renderAI(); toast('تم تحديث التحليل ✨','warn'); }

// ── Points ─────────────────────────────────────────────────────
function addPts(n) {
  state.pts += n;
  renderPts();
}
function renderPts() {
  setText('ptsVal', fmt(state.pts));
  const lv = LEVELS.reduce((a,l)=> state.pts>=l.min?l:a, LEVELS[0]);
  setText('ptsLevel', lv.name);
}

// ── Lists ──────────────────────────────────────────────────────
function renderLists() {
  const m = getMonthData(state.year, state.month);
  renderItemList(m.income,   'income',   'incList',  'incTotal',  'income');
  renderItemList(m.fixed,    'fixed',    'fixList',  'fixTotal',  'expense');
  renderItemList(m.variable, 'variable', 'varList',  'varTotal',  'expense');
}

function renderItemList(arr, type, listId, totalId, colorCls) {
  const total = arr.reduce((s,x)=>s+(Number(x.amt)||0), 0);
  setText(totalId, fmt(total)+' ﷼');
  const el = document.getElementById(listId);
  if(!el) return;
  if(!arr.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">${colorCls==='income'?'💵':'💸'}</div><div>ما في شيء — أضف!</div></div>`;
    return;
  }
  el.innerHTML = arr.map(item =>
    `<div class="item-row${item.paid?' paid':''}">
      <div class="item-emoji">${item.cat}</div>
      <div class="item-name" onclick="togglePaid('${type}',${item.id})">${item.name}
        ${item.recurring?'<span class="item-recurring">🔄</span>':''}
      </div>
      <div class="item-amount ${colorCls}">${fmt(item.amt)} ﷼</div>
      <button class="item-del" onclick="delItem('${type}',${item.id})">✕</button>
    </div>`
  ).join('');
}

// ── Items CRUD ─────────────────────────────────────────────────
function addItem(type) {
  const fields = {
    income:   {name:'incName', amt:'incAmt', cat:'incCat', rec:'incRec'},
    fixed:    {name:'fixName', amt:'fixAmt', cat:'fixCat', rec:'fixRec'},
    variable: {name:'varName', amt:'varAmt', cat:'varCat', rec:null},
  };
  const f = fields[type];
  const name = document.getElementById(f.name)?.value.trim();
  const amt  = parseFloat(document.getElementById(f.amt)?.value)||0;
  const cat  = document.getElementById(f.cat)?.value || '➕';
  const rec  = f.rec ? document.getElementById(f.rec)?.checked : false;

  if(!name) { toast('اكتب الاسم أولاً ⚠️','warn'); return; }
  if(!amt)  { toast('اكتب المبلغ أولاً ⚠️','warn'); return; }

  const m = getMonthData(state.year, state.month);
  const arr = type==='income' ? m.income : type==='fixed' ? m.fixed : m.variable;
  arr.push({ id:Date.now(), name, amt, cat, paid:false, recurring:rec, createdAt:new Date().toISOString() });

  document.getElementById(f.name).value = '';
  document.getElementById(f.amt).value  = '';
  addPts(15); markDirty(); checkAch(); renderAll();
  toast('تمت الإضافة ✅','success');
}

function delItem(type, id) {
  const m = getMonthData(state.year, state.month);
  const arr = type==='income'?m.income:type==='fixed'?m.fixed:m.variable;
  const idx = arr.findIndex(x=>x.id===id);
  if(idx>=0) arr.splice(idx,1);
  markDirty(); renderAll();
}

function togglePaid(type, id) {
  const m = getMonthData(state.year, state.month);
  const arr = type==='income'?m.income:type==='fixed'?m.fixed:m.variable;
  const item = arr.find(x=>x.id===id);
  if(!item) return;
  item.paid = !item.paid;
  if(item.paid) { addPts(5); toast('تم ✅','success'); }
  markDirty(); renderAll();
}

// ── Goals ──────────────────────────────────────────────────────
function addGoal() {
  const name   = document.getElementById('goalName')?.value.trim();
  const target = parseFloat(document.getElementById('goalTarget')?.value)||0;
  const saved  = parseFloat(document.getElementById('goalSaved')?.value)||0;
  const icon   = document.getElementById('goalIcon')?.value||'⭐';
  if(!name||!target) { toast('اكتب اسم الهدف والمبلغ ⚠️','warn'); return; }

  const m = getMonthData(state.year, state.month);
  m.goals.push({ id:Date.now(), name, target, saved, icon });
  ['goalName','goalTarget','goalSaved'].forEach(id => { const e=document.getElementById(id);if(e)e.value=''; });
  addPts(50); markDirty(); checkAch(); renderGoals();
  toast('تم إضافة الهدف 🎯','success');
}

function delGoal(id) {
  const m = getMonthData(state.year, state.month);
  m.goals = m.goals.filter(g=>g.id!==id);
  markDirty(); renderGoals();
}

function renderGoals() {
  const m = getMonthData(state.year, state.month);
  const el = document.getElementById('goalList');
  if(!el) return;
  if(!m.goals.length) {
    el.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎯</div><div>ما عندك أهداف بعد</div></div>';
    return;
  }
  el.innerHTML = m.goals.map(g => {
    const pct = g.target ? Math.min(100, Math.round((g.saved/g.target)*100)) : 0;
    return `<div class="goal-item">
      <div class="goal-head">
        <div class="goal-name">${g.icon} ${g.name}</div>
        <div style="display:flex;gap:7px;align-items:center">
          <div class="goal-amounts">${fmt(g.saved)} / ${fmt(g.target)} ﷼</div>
          <button class="item-del" onclick="delGoal(${g.id})">✕</button>
        </div>
      </div>
      <div class="goal-track-bg"><div class="goal-track-fill" style="width:${pct}%"></div></div>
      <div class="goal-pct">${pct}٪ مكتمل ${pct>=100?'🎉':''}</div>
    </div>`;
  }).join('');
}

// ── Budget Categories ───────────────────────────────────────────
function addBudgetCat() {
  const sel   = document.getElementById('bcCat')?.value||'';
  const name  = (document.getElementById('bcName')?.value.trim()) || sel;
  const limit = parseFloat(document.getElementById('bcLimit')?.value)||0;
  if(!name||!limit) { toast('اكتب الفئة والمبلغ ⚠️','warn'); return; }

  const m = getMonthData(state.year, state.month);
  if(m.budgets.some(b=>b.name===name)) { toast('الفئة موجودة بالفعل','warn'); return; }
  m.budgets.push({ id:Date.now(), name, limit });
  document.getElementById('bcName').value  = '';
  document.getElementById('bcLimit').value = '';
  document.getElementById('formBudget').classList.remove('open');
  addPts(10); markDirty(); renderBudgets();
  toast('تمت إضافة الفئة ✅','success');
}

function delBudgetCat(id) {
  const m = getMonthData(state.year, state.month);
  m.budgets = m.budgets.filter(b=>b.id!==id);
  markDirty(); renderBudgets();
}

function renderBudgets() {
  const m  = getMonthData(state.year, state.month);
  const el = document.getElementById('budgetItems');
  const alertEl = document.getElementById('budgetAlert');
  if(!el) return;
  if(!m.budgets.length) { el.innerHTML='<div class="empty-state"><div class="empty-state-icon">🎯</div><div>ما عندك فئات — أضف فئة!</div></div>'; if(alertEl)alertEl.className='budget-alert'; return; }

  const catSpend = getCategorySpending(state.year, state.month);
  const alerts = [];

  el.innerHTML = m.budgets.map(b => {
    let spent = 0;
    const key = b.name.replace(/^[^\u0600-\u06FF\w]*/, '').trim();
    Object.entries(catSpend).forEach(([cat,amt]) => {
      if(b.name.includes(cat)||cat.includes(key)) spent+=amt;
    });
    const pct = b.limit ? Math.min(100, Math.round((spent/b.limit)*100)) : 0;
    const remain = b.limit - spent;
    const cls = pct>=100?'danger':pct>=80?'warn':'';
    const emoji = pct>=100?'🚨':pct>=80?'⚠️':'✅';
    if(pct>=80) alerts.push({over:pct>=100, name:b.name, pct, remain});
    return `<div class="budget-item">
      <div class="budget-item-head">
        <div class="budget-cat">${emoji} ${b.name}</div>
        <div style="display:flex;align-items:center;gap:7px">
          <div class="budget-nums"><span class="budget-spent">${fmt(spent)}</span><span class="budget-limit"> / ${fmt(b.limit)} ﷼</span></div>
          <button class="item-del" onclick="delBudgetCat(${b.id})">✕</button>
        </div>
      </div>
      <div class="budget-track-bg"><div class="budget-track-fill ${cls}" style="width:${pct}%"></div></div>
      <div class="budget-foot">
        <span>${pct}٪</span>
        <span class="budget-remain${remain<0?' over':''}">
          ${remain>=0?'باقي: '+fmt(remain)+' ﷼':'تجاوزت بـ '+fmt(Math.abs(remain))+' ﷼'}
        </span>
      </div>
    </div>`;
  }).join('');

  if(alertEl) {
    if(alerts.length) {
      alertEl.innerHTML = alerts.map(a=>
        `<div class="budget-alert-row"><div class="budget-alert-icon">${a.over?'🚨':'⚠️'}</div><div class="budget-alert-txt"><b>${a.name} — ${a.pct}٪</b>${a.remain<0?'تجاوزت الحد!':'قرّبت من الحد'}</div></div>`
      ).join('');
      alertEl.className = 'budget-alert show';
    } else { alertEl.className = 'budget-alert'; }
  }
}

// ── Charts ─────────────────────────────────────────────────────
function renderCharts() {
  renderPieChart();
  renderCmpChart();
}

function renderPieChart() {
  const m = getMonthData(state.year, state.month);
  const cats = {};
  [...m.fixed,...m.variable].forEach(({cat,amt})=>{ cats[cat]=(cats[cat]||0)+(Number(amt)||0); });
  const entries = Object.entries(cats).sort((a,b)=>b[1]-a[1]);
  const total = entries.reduce((s,[,v])=>s+v, 0);
  const svg = document.getElementById('pieChart');
  const leg = document.getElementById('pieLegend');
  if(!svg||!leg) return;

  if(!total) { svg.innerHTML='<text x="50" y="55" text-anchor="middle" fill="#5a4a50" font-size="9">لا بيانات</text>'; leg.innerHTML=''; return; }

  let paths='', legendHTML='', startAngle=0;
  entries.forEach(([cat,val],i) => {
    const pct = val/total, angle=pct*360, large=angle>180?1:0, col=PIE_COLORS[i%PIE_COLORS.length];
    const r=40,cx=50,cy=50;
    const x1=cx+r*Math.cos(startAngle*Math.PI/180), y1=cy+r*Math.sin(startAngle*Math.PI/180);
    const x2=cx+r*Math.cos((startAngle+angle)*Math.PI/180), y2=cy+r*Math.sin((startAngle+angle)*Math.PI/180);
    if(entries.length===1) paths+=`<circle cx="${cx}" cy="${cy}" r="${r}" fill="${col}"/>`;
    else paths+=`<path d="M${cx},${cy} L${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 ${large},1 ${x2.toFixed(2)},${y2.toFixed(2)} Z" fill="${col}"/>`;
    legendHTML+=`<div class="pie-item"><div class="pie-dot" style="background:${col}"></div><div class="pie-lbl">${cat}</div><div class="pie-pct">${Math.round(pct*100)}٪</div></div>`;
    startAngle+=angle;
  });
  svg.innerHTML = paths;
  leg.innerHTML = legendHTML;
}

function renderCmpChart() {
  const t=getTotals(state.year,state.month), p=getTotals(state.year,state.month>0?state.month-1:11);
  const mx=Math.max(t.income,t.expense,p.income,p.expense,1);
  document.getElementById('cmpChart').innerHTML=`
    <div class="cmp-row"><div class="cmp-lbl">دخل الشهر</div><div class="cmp-bar-bg"><div class="cmp-bar-fill" style="width:${Math.round((t.income/mx)*100)}%;background:var(--sage2)"></div></div><div class="cmp-val">${fmt(t.income)} ﷼</div></div>
    <div class="cmp-row"><div class="cmp-lbl">دخل السابق</div><div class="cmp-bar-bg"><div class="cmp-bar-fill" style="width:${Math.round((p.income/mx)*100)}%;background:rgba(106,170,136,.4)"></div></div><div class="cmp-val">${fmt(p.income)} ﷼</div></div>
    <div class="cmp-row"><div class="cmp-lbl">مصروف الشهر</div><div class="cmp-bar-bg"><div class="cmp-bar-fill" style="width:${Math.round((t.expense/mx)*100)}%;background:var(--crimson2)"></div></div><div class="cmp-val">${fmt(t.expense)} ﷼</div></div>
    <div class="cmp-row"><div class="cmp-lbl">مصروف السابق</div><div class="cmp-bar-bg"><div class="cmp-bar-fill" style="width:${Math.round((p.expense/mx)*100)}%;background:rgba(122,37,53,.4)"></div></div><div class="cmp-val">${fmt(p.expense)} ﷼</div></div>
  `;
}

// ── Yearly View ────────────────────────────────────────────────
function renderYearly() {
  let yI=0,yE=0,iA=[],eA=[];
  for(let m=0;m<12;m++){const t=getTotals(state.year,m);yI+=t.income;yE+=t.expense;iA.push(t.income);eA.push(t.expense);}
  setText('yInc',fmt(yI)+' ﷼'); setText('yExp',fmt(yE)+' ﷼'); setText('ySav',fmt(Math.max(0,yI-yE))+' ﷼');
  const mx=Math.max(...iA,...eA,1);
  const bars=document.getElementById('yearBars'), lbls=document.getElementById('yearLbls');
  if(bars) bars.innerHTML=iA.map((v,i)=>`<div class="year-bar-wrap"><div class="year-bar income" style="height:${Math.round((v/mx)*88)}px"></div><div class="year-bar expense" style="height:${Math.round((eA[i]/mx)*88)}px"></div></div>`).join('');
  if(lbls) lbls.innerHTML=MONTHS.map(m=>`<div class="year-lbl">${m.slice(0,3)}</div>`).join('');
  const ul=ACHIEVEMENTS.filter(a=>localStorage.getItem('ach_'+a.id));
  const el=document.getElementById('yearAch');
  if(el) el.innerHTML=ul.length?ul.map(a=>`<div style="display:flex;align-items:center;gap:7px;background:rgba(255,255,255,.04);padding:7px 11px;border-radius:10px;border:1px solid var(--border)"><span style="font-size:17px">${a.icon}</span><div><div style="font-size:11px;font-weight:700">${a.name}</div><div style="font-size:9px;color:var(--text3)">${a.pts} ⭐</div></div></div>`).join(''):
    '<div style="color:var(--text3);font-size:12px;text-align:center;padding:12px">ما حققت شي بعد — ابدأ الحين! 🚀</div>';
}

// ── Achievements ───────────────────────────────────────────────
function checkAch() {
  const t=getTotals(state.year,state.month), m=getMonthData(state.year,state.month);
  const conds={
    first_save: Object.values(state.data).some(d=>d.goals&&d.goals.length>0),
    no_exceed:  t.income>0&&t.expense<=t.income,
    save_20:    t.income>0&&t.savePct>=20,
    daily_log:  Object.keys(m.daily||{}).length>=7,
    goal_done:  Object.values(state.data).some(d=>d.goals&&d.goals.some(g=>g.target>0&&g.saved>=g.target)),
    three_months:(()=>{let c=0;for(let i=0;i<12;i++){const d=state.data[makeKey(state.year,i)];if(d&&(d.income.length||d.variable.length)){c++;if(c>=3)return true;}else c=0;}return false;})(),
  };
  ACHIEVEMENTS.forEach(a=>{
    if(!localStorage.getItem('ach_'+a.id)&&conds[a.id]){
      localStorage.setItem('ach_'+a.id,'1');
      addPts(a.pts);
      toast(`🏆 إنجاز: ${a.name} (+${a.pts} نقطة)`,'warn');
    }
  });
  renderAch();
}

function renderAch() {
  const el=document.getElementById('achGrid'); if(!el)return;
  el.innerHTML=ACHIEVEMENTS.map(a=>{
    const on=!!localStorage.getItem('ach_'+a.id);
    return `<div class="ach-badge ${on?'on':'off'}"><div class="ach-icon">${a.icon}</div><div class="ach-name">${a.name}</div><div class="ach-pts">${a.pts} ⭐</div></div>`;
  }).join('');
}

// ── Streak ─────────────────────────────────────────────────────
function getTodayStr() {
  const d=new Date(); return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`;
}
function initStreakRender() { calcStreak(); renderStreak(); }

function calcStreak() {
  const s=state.streak;
  if(!s.days||!s.days.length){s.current=0;return;}
  const sorted=[...s.days].sort().reverse();
  const today=getTodayStr();
  const d=new Date(); d.setDate(d.getDate()-1);
  const yesterday=`${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`;
  if(sorted[0]!==today&&sorted[0]!==yesterday){s.current=0;return;}
  let cnt=0, check=sorted[0]===today?today:yesterday;
  for(let i=0;i<sorted.length;i++){
    if(sorted[i]===check){cnt++;const dt=new Date(check);dt.setDate(dt.getDate()-1);check=`${dt.getFullYear()}-${dt.getMonth()+1}-${dt.getDate()}`;}
    else break;
  }
  s.current=cnt; s.max=Math.max(s.max||0,cnt); s.total=s.days.length;
}

function doCheckin() {
  const today=getTodayStr();
  if(state.streak.days.includes(today)){toast('سجّلت حضورك اليوم بالفعل 🔥','warn');return;}
  state.streak.days.push(today);
  calcStreak();
  Storage.save('streak',state.streak);
  addPts(20);
  if(state.streak.current===7)  { addPts(50);  toast('🏆 أسبوع كامل! +٥٠ نقطة إضافية','warn'); }
  if(state.streak.current===30) { addPts(200); toast('🌟 شهر كامل! +٢٠٠ نقطة إضافية','warn'); }
  renderStreak();
  toast('تم تسجيل حضورك 🔥 +٢٠ نقطة','success');
}

function renderStreak() {
  calcStreak();
  const s=state.streak, today=getTodayStr();
  const checked=s.days.includes(today);
  const cur=s.current||0;

  const numEl=document.getElementById('streakNum');
  if(numEl){numEl.textContent=cur;numEl.className='streak-num'+(cur>0?' active':'');}

  const dotsEl=document.getElementById('streakDots');
  if(dotsEl){
    let h='';
    for(let i=6;i>=0;i--){
      const dt=new Date();dt.setDate(dt.getDate()-i);
      const ds=`${dt.getFullYear()}-${dt.getMonth()+1}-${dt.getDate()}`;
      const done=s.days.includes(ds),isToday=(i===0);
      const name=DAY_NAMES[dt.getDay()];
      h+=`<div style="display:flex;flex-direction:column;align-items:center;gap:3px">
        <div class="streak-dot${done?' done':''}${isToday&&!done?' today':''}">${done?'✓':name}</div>
        <div style="font-size:8px;color:var(--text3)">${dt.getDate()}</div>
      </div>`;
    }
    dotsEl.innerHTML=h;
  }

  const btn=document.getElementById('streakBtn');
  if(btn){btn.textContent=checked?'✅ سجّلت حضورك اليوم 🔥':'🔥 سجّل حضورك اليوم';btn.className='streak-checkin'+(checked?' done':'');}

  const msgs=['','ابدأ سلسلتك اليوم 💪','✅ بداية موفقة! تعال غداً 😊'];
  let msg='';
  if(!checked)msg='سجّل حضورك عشان ما تكسر السلسلة! ⚡';
  else if(cur>=30)msg='🌟 شهر كامل ماشاء الله! استمر';
  else if(cur>=14)msg='💎 أسبوعين متتاليين! رهيب';
  else if(cur>=7) msg='🏆 أسبوع كامل! ما شاء الله';
  else if(cur>=3) msg=`🔥 ${cur} أيام — استمر!`;
  else if(cur===1)msg='✅ بداية موفقة! تعال غداً 😊';
  else msg='ابدأ سلسلتك اليوم 💪';
  setText('streakMsg',msg);
  setText('sCur',s.current||0); setText('sMax',s.max||0); setText('sTot',s.total||0);
}

// ── Salary ─────────────────────────────────────────────────────
function buildSalarySelect() {
  const sel=document.getElementById('salarySelect'); if(!sel)return;
  sel.innerHTML='<option value="">—</option>';
  for(let d=1;d<=31;d++){
    const opt=document.createElement('option');
    opt.value=d; opt.textContent=d;
    if(d===state.salaryDay) opt.selected=true;
    sel.appendChild(opt);
  }
}
function setSalaryDay(v) {
  state.salaryDay=parseInt(v)||0;
  Storage.save('salary',state.salaryDay);
  updateSalaryCountdown();
}
function updateSalaryCountdown() {
  const el=document.getElementById('salaryCd'); if(!el)return;
  if(!state.salaryDay){el.textContent='اختر يوم';el.className='salary-badge';return;}
  const today=new Date(),td=today.getDate();
  let next=new Date(today.getFullYear(),today.getMonth(),state.salaryDay);
  if(next.getDate()!==state.salaryDay||next<today){
    next=new Date(today.getFullYear(),today.getMonth()+1,state.salaryDay);
    if(next.getDate()!==state.salaryDay) next=new Date(today.getFullYear(),today.getMonth()+2,0);
  }
  const diff=Math.ceil((next-today)/(86400000));
  if(diff<=0||td===state.salaryDay){el.textContent='اليوم نزول الراتب 🎉';el.className='salary-badge today';}
  else if(diff===1){el.textContent='غداً ينزل الراتب ⏰';el.className='salary-badge today';}
  else{el.textContent=`باقي ${diff} يوم 📅`;el.className='salary-badge';}
}

// ── Notifications ───────────────────────────────────────────────
function openNotifPanel() {
  document.getElementById('notifOverlay').classList.add('open');
  document.getElementById('notifPanel').classList.add('open');
  renderNotifPanel();
}
function closeNotifPanel() {
  document.getElementById('notifOverlay').classList.remove('open');
  document.getElementById('notifPanel').classList.remove('open');
}
function notifSetCat(icon,name) {
  const ic=document.getElementById('nfIcon'),nm=document.getElementById('nfName');
  if(ic) ic.value=icon; if(nm&&!nm.value) nm.value=name; if(nm) nm.focus();
  document.querySelectorAll('#notifCatChips .day-chip').forEach(c=>c.classList.remove('sel'));
  if(event?.target) event.target.classList.add('sel');
}
function notifSetDay(d) {
  const el=document.getElementById('nfDay'); if(el) el.value=d;
  document.querySelectorAll('#dayChips .day-chip').forEach(c=>c.classList.remove('sel'));
  if(event?.target) event.target.classList.add('sel');
}
function addNotif() {
  const name=document.getElementById('nfName')?.value.trim();
  const amt=parseFloat(document.getElementById('nfAmt')?.value)||0;
  const icon=document.getElementById('nfIcon')?.value.trim()||'🔔';
  const day=parseInt(document.getElementById('nfDay')?.value)||0;
  const alertD=parseInt(document.getElementById('nfAlert')?.value)||5;
  const rec=document.getElementById('nfRecurring')?.checked;
  if(!name){toast('اكتب اسم المستحق ⚠️','warn');return;}
  if(!day||day<1||day>31){toast('حدد يوم الاستحقاق ⚠️','warn');return;}
  state.notifs.push({id:Date.now(),name,amt,icon,day,alertDays:alertD,recurring:rec,paidMonths:{}});
  Storage.save('notifs',state.notifs);
  ['nfName','nfAmt','nfDay'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});
  document.getElementById('nfIcon').value='🏠';
  document.querySelectorAll('#notifCatChips .day-chip,#dayChips .day-chip').forEach(c=>c.classList.remove('sel'));
  updateBellBadge(); renderNotifPanel();
  toast('✅ تم إضافة التنبيه','success');
}
function toggleNotifPaid(id) {
  const key=`${state.year}-${state.month}`;
  const n=state.notifs.find(x=>x.id===id); if(!n)return;
  if(!n.paidMonths) n.paidMonths={};
  if(n.paidMonths[key]){delete n.paidMonths[key];toast('إلغاء التأكيد','warn');}
  else{n.paidMonths[key]=true;toast('✅ تم — '+n.name,'success');addPts(20);}
  Storage.save('notifs',state.notifs); updateBellBadge(); renderNotifPanel();
}
function deleteNotif(id) {
  state.notifs=state.notifs.filter(n=>n.id!==id);
  Storage.save('notifs',state.notifs); updateBellBadge(); renderNotifPanel();
}
function getNotifStatus(item) {
  const today=new Date().getDate(),key=`${state.year}-${state.month}`;
  if(item.paidMonths?.[key]) return 'paid';
  const d=item.day-today;
  if(d<0) return 'overdue'; if(d===0) return 'urgent'; if(d<=item.alertDays) return 'soon'; return 'upcoming';
}
function updateBellBadge() {
  const cnt=state.notifs.filter(n=>{const s=getNotifStatus(n);return s==='overdue'||s==='urgent'||s==='soon';}).length;
  const dot=document.getElementById('bellDot');
  if(dot) dot.className='bell-dot'+(cnt>0?' show':'');
  const btn=document.getElementById('bellBtn');
  if(btn) btn.className='bell-btn'+(cnt>0?' alert':'');
}
function checkNotifAlerts() {
  const urgent=state.notifs.filter(n=>getNotifStatus(n)==='urgent');
  const overdue=state.notifs.filter(n=>getNotifStatus(n)==='overdue');
  if(urgent.length) setTimeout(()=>toast('🔴 اليوم موعد: '+urgent.map(n=>n.name).join('، '),'danger'),1500);
  else if(overdue.length) setTimeout(()=>toast('⚠️ تجاوزت موعد: '+overdue[0].name,'danger'),1500);
}
function renderNotifPanel() {
  const body=document.getElementById('notifPanelBody'); if(!body)return;
  if(!state.notifs.length){
    body.innerHTML='<div class="notif-empty"><div class="notif-empty-icon">🔔</div><div class="notif-empty-text">ما عندك تنبيهات<br>أضف مستحقاتك من الأسفل</div></div>';return;
  }
  const labels={paid:{cls:'paid',txt:'✅ تم'},overdue:{cls:'overdue',txt:'⚠️ متأخر'},urgent:{cls:'overdue',txt:'🔴 اليوم!'},soon:{cls:'soon',txt:'⏰ قريب'},upcoming:{cls:'upcoming',txt:'📅 قادم'}};
  const groups={urgent:[],soon:[],upcoming:[],paid:[]};
  state.notifs.forEach(n=>{const s=getNotifStatus(n);if(s==='overdue'||s==='urgent')groups.urgent.push([n,s]);else if(s==='soon')groups.soon.push([n,s]);else if(s==='paid')groups.paid.push([n,s]);else groups.upcoming.push([n,s]);});
  let h='';
  const renderGroup=(title,items)=>{
    if(!items.length) return;
    h+=`<div class="notif-section-lbl">${title}</div>`;
    items.forEach(([n,s])=>{
      const lbl=labels[s]||labels.upcoming;
      const paid=s==='paid';
      h+=`<div class="notif-item${s==='overdue'||s==='urgent'?' urgent':s==='soon'?' warning':paid?' done':''}">
        <div class="notif-icon">${n.icon}</div>
        <div class="notif-body">
          <div class="notif-name">${n.name}${n.recurring?' 🔄':''}</div>
          ${n.amt?`<div class="notif-amt">${fmt(n.amt)} ﷼</div>`:''}
          <div class="notif-meta"><span class="notif-sbadge ${lbl.cls}">${lbl.txt}</span><span>يوم ${n.day}</span></div>
        </div>
        <div class="notif-actions">
          <button class="notif-check${paid?' checked':''}" onclick="toggleNotifPaid(${n.id})">${paid?'✓':'○'}</button>
          <button class="notif-del-btn" onclick="deleteNotif(${n.id})">🗑</button>
        </div>
      </div>`;
    });
  };
  renderGroup('🔴 يحتاج انتباهك',groups.urgent);
  renderGroup('⏰ قريب',groups.soon);
  renderGroup('📅 قادم',groups.upcoming);
  renderGroup('✅ تم',groups.paid);
  body.innerHTML=h;
}

// ── Quick Add ──────────────────────────────────────────────────
function qaSetType(t) {
  state.qaType=t;
  document.getElementById('qaBtnOut').className='qa-type-btn expense'+(t==='out'?' active':'');
  document.getElementById('qaBtnIn').className='qa-type-btn income'+(t==='in'?' active':'');
  document.getElementById('qaName').placeholder=t==='out'?'وش صرفت على؟':'مصدر الدخل؟';
}
function qaSubmit() {
  const name=(document.getElementById('qaName')?.value||'').trim();
  const amt=parseFloat(document.getElementById('qaAmt')?.value)||0;
  if(!name&&!amt){if(state.qaType==='out')toggleForm('formVar');else toggleForm('formIncome');return;}
  if(!name){toast('اكتب الوصف ⚠️','warn');return;}
  if(!amt){toast('اكتب المبلغ ⚠️','warn');return;}
  const m=getMonthData(state.year,state.month),td=new Date().getDate();
  if(state.qaType==='out'){
    if(!m.daily[td]) m.daily[td]=[];
    m.daily[td].push({id:Date.now(),name,amt,type:'out',cat:'➕'});
  } else {
    m.income.push({id:Date.now(),name,amt,cat:'💵',paid:false,recurring:false});
  }
  document.getElementById('qaName').value='';
  document.getElementById('qaAmt').value='';
  addPts(10); markDirty(); renderAll();
  toast((state.qaType==='out'?'💸 ':'💵 ')+name+' — '+fmt(amt)+' ﷼','success');
}

// ── Search ─────────────────────────────────────────────────────
function doSearch(q) {
  const r=document.getElementById('searchResults'); if(!r)return;
  if(!q.trim()){r.style.display='none';r.innerHTML='';return;}
  const m=getMonthData(state.year,state.month);
  const all=[
    ...m.income.map(x=>({...x,typeLabel:'دخل',color:'var(--sage2)'})),
    ...m.fixed.map(x=>({...x,typeLabel:'ثابت',color:'#e07070'})),
    ...m.variable.map(x=>({...x,typeLabel:'متغير',color:'#e07070'})),
  ].filter(x=>x.name.includes(q));
  if(!all.length){r.innerHTML='<div style="font-size:12px;color:var(--text3);padding:6px">ما لقينا شيئاً</div>';r.style.display='flex';return;}
  r.innerHTML=all.map(x=>`<div class="item-row"><div class="item-emoji">${x.cat}</div><div class="item-name">${x.name} <span style="font-size:9px;color:var(--text3)">(${x.typeLabel})</span></div><div class="item-amount" style="color:${x.color}">${fmt(x.amt)} ﷼</div></div>`).join('');
  r.style.display='flex';
}
function clearSearch(){document.getElementById('searchInput').value='';doSearch('');}

// ── Tips ───────────────────────────────────────────────────────
function nextTip() { state.tipIdx=(state.tipIdx+1)%TIPS.length; setText('tipText',TIPS[state.tipIdx]); }

// ── Tabs ───────────────────────────────────────────────────────
function showTab(t) {
  state.tab=t;
  document.getElementById('tabM').className='nav-btn'+(t==='monthly'?' active':'');
  document.getElementById('tabY').className='nav-btn'+(t==='yearly'?' active':'');
  document.getElementById('viewMonthly').style.display=t==='monthly'?'block':'none';
  document.getElementById('viewYearly').style.display=t==='yearly'?'block':'none';
  document.getElementById('monthNav').style.display=t==='monthly'?'flex':'none';
  if(t==='yearly') renderYearly();
}

// ── Forms ──────────────────────────────────────────────────────
function toggleForm(id) {
  const el=document.getElementById(id); if(!el)return;
  el.classList.toggle('open');
}
function qSetCat(selId,val,inpId,name) {
  const sel=document.getElementById(selId),inp=document.getElementById(inpId);
  if(sel) sel.value=val; if(inp&&!inp.value) inp.value=name; if(inp) inp.focus();
  if(event?.target){const p=event.target.closest('.cat-chips');if(p){p.querySelectorAll('.cat-chip').forEach(c=>c.classList.remove('sel'));event.target.classList.add('sel');}}
}
function setAmt(id,v){const el=document.getElementById(id);if(el){el.value=v;el.focus();}}

// ── Save ───────────────────────────────────────────────────────
function markDirty() {
  state.dirty=true;
  document.getElementById('saveWrap').classList.add('dirty');
}
function saveAll() {
  Storage.save('data',state.data);
  Storage.save('pts',state.pts);
  state.dirty=false;
  document.getElementById('saveWrap').classList.remove('dirty');
  const btn=document.getElementById('saveBtn');
  if(btn){btn.textContent='✅ تم الحفظ!';btn.classList.add('saved');}
  toast('تم الحفظ ✅','success');
  setTimeout(()=>{if(btn){btn.textContent='💾 احفظ التغييرات';btn.classList.remove('saved');}},2000);
}

// ── Toast ──────────────────────────────────────────────────────
function toast(msg,type='success') {
  const w=document.getElementById('toastWrap'),el=document.createElement('div');
  el.className='toast '+type; el.textContent=msg; w.appendChild(el);
  setTimeout(()=>{el.style.opacity='0';el.style.transition='.3s';setTimeout(()=>el.remove(),300);},3000);
}

// ── DOM Helpers ────────────────────────────────────────────────
function setText(id,txt){const el=document.getElementById(id);if(el&&el.textContent!==txt)el.textContent=txt;}
function setStyle(id,prop,val){const el=document.getElementById(id);if(el)el.style[prop]=val;}

// ── Boot ───────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
</script>
</body>
</html>
