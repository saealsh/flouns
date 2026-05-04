/* ═══════════════════════════════════════════════════════
   Call Intelligence Engine — DEMO Mode (No Backend)
   All data mocked in-memory + persisted to localStorage
   ═══════════════════════════════════════════════════════ */

// ═══ Seed Data ═══
const SEED_SPEAKERS = [
  { id: 'SPK_01', name: 'أحمد', role: 'متحدث رئيسي', color: 'purple', initials: 'أح', total_calls: 9, total_minutes: 36, total_words: 4280, avg_confidence: 94, voiceprint_status: 'stable', first_seen: '2026-04-17', last_seen: '2026-04-21' },
  { id: 'SPK_02', name: 'خالد', role: 'متحدث رئيسي', color: 'accent', initials: 'خا', total_calls: 8, total_minutes: 29, total_words: 3645, avg_confidence: 91, voiceprint_status: 'stable', first_seen: '2026-04-17', last_seen: '2026-04-21' },
  { id: 'SPK_03', name: 'سعود', role: 'متحدث مساعد', color: 'coral', initials: 'سع', total_calls: 4, total_minutes: 18, total_words: 1820, avg_confidence: 90, voiceprint_status: 'stable', first_seen: '2026-04-18', last_seen: '2026-04-21' },
  { id: 'SPK_04', name: 'فهد', role: 'متحدث مساعد', color: 'amber', initials: 'فه', total_calls: 3, total_minutes: 11, total_words: 1105, avg_confidence: 89, voiceprint_status: 'stable', first_seen: '2026-04-20', last_seen: '2026-04-21' },
  { id: 'SPK_05', name: 'ريم', role: 'منسق خارجي', color: 'blue', initials: 'ري', total_calls: 4, total_minutes: 14, total_words: 1380, avg_confidence: 92, voiceprint_status: 'stable', first_seen: '2026-04-20', last_seen: '2026-04-21' },
  { id: 'SPK_06', name: 'غير معروف', role: 'متحدث مجهول', color: 'gray', initials: '?', total_calls: 2, total_minutes: 6, total_words: 480, avg_confidence: 72, voiceprint_status: 'unstable', first_seen: '2026-04-21', last_seen: '2026-04-21' },
  { id: 'SPK_07', name: 'نورة', role: 'متحدث جديد', color: 'green', initials: 'نو', total_calls: 1, total_minutes: 3, total_words: 320, avg_confidence: 95, voiceprint_status: 'new', first_seen: '2026-04-21', last_seen: '2026-04-21' }
];

const SEED_CALLS = [
  { id: 'C-001', title: 'مكالمة افتتاحية', topic: 'تعارف وتقديم', date: '2026-04-17', time: '09:14', duration: '02:10', duration_sec: 130, speakers: ['أحمد', 'خالد'], confidence: 96, flags: 0, is_active: false, keywords: ['اجتماع', 'بداية', 'تعاون'] },
  { id: 'C-002', title: 'متابعة العقد', topic: 'مراجعة شروط', date: '2026-04-18', time: '11:22', duration: '05:45', duration_sec: 345, speakers: ['أحمد', 'خالد', 'سعود'], confidence: 92, flags: 1, is_active: false, keywords: ['العقد', 'البنود', 'توقيع'] },
  { id: 'C-003', title: 'تنسيق الشحنة', topic: 'تخطيط لوجستي', date: '2026-04-20', time: '15:30', duration: '04:32', duration_sec: 272, speakers: ['أحمد', 'خالد'], confidence: 94, flags: 3, is_active: true, keywords: ['الشحنة', 'الموعد', 'التسليم'] },
  { id: 'C-004', title: 'اجتماع داخلي', topic: 'تنسيق فريق', date: '2026-04-20', time: '16:10', duration: '08:20', duration_sec: 500, speakers: ['أحمد', 'سعود', 'فهد', 'ريم'], confidence: 89, flags: 0, is_active: false, keywords: ['الفريق', 'المهام', 'المواعيد'] },
  { id: 'C-005', title: 'تأكيد الموعد', topic: 'تأكيد سريع', date: '2026-04-21', time: '08:45', duration: '01:48', duration_sec: 108, speakers: ['خالد', 'فهد'], confidence: 97, flags: 0, is_active: false, keywords: ['الموعد', 'تأكيد', 'الاثنين'] },
  { id: 'C-006', title: 'إشعار تأخير', topic: 'تنبيه', date: '2026-04-21', time: '10:20', duration: '03:15', duration_sec: 195, speakers: ['أحمد', 'خالد'], confidence: 91, flags: 2, is_active: false, keywords: ['تأخير', 'اعتذار', 'إعادة جدولة'] },
  { id: 'C-007', title: 'استفسار العميل', topic: 'خدمة عملاء', date: '2026-04-21', time: '11:35', duration: '02:50', duration_sec: 170, speakers: ['ريم', 'خالد'], confidence: 88, flags: 0, is_active: false, keywords: ['استفسار', 'تفاصيل', 'معلومات'] },
  { id: 'C-008', title: 'تنفيذ التسليم', topic: 'تنفيذ', date: '2026-04-21', time: '13:48', duration: '06:12', duration_sec: 372, speakers: ['أحمد', 'خالد', 'سعود'], confidence: 93, flags: 2, is_active: false, keywords: ['التسليم', 'الاستلام', 'التوقيع'] },
  { id: 'C-009', title: 'تقرير ختامي', topic: 'مراجعة', date: '2026-04-21', time: '15:00', duration: '04:05', duration_sec: 245, speakers: ['أحمد', 'سعود'], confidence: 95, flags: 0, is_active: false, keywords: ['تقرير', 'ملخص', 'نتائج'] },
  { id: 'C-010', title: 'متابعة جديدة', topic: 'متابعة', date: '2026-04-21', time: '16:20', duration: '03:40', duration_sec: 220, speakers: ['فهد', 'ريم'], confidence: 90, flags: 1, is_active: false, keywords: ['متابعة', 'تنسيق', 'موعد جديد'] },
  { id: 'C-011', title: 'اتصال طارئ', topic: 'طارئ', date: '2026-04-21', time: '17:05', duration: '01:32', duration_sec: 92, speakers: ['خالد', 'أحمد'], confidence: 85, flags: 3, is_active: false, keywords: ['عاجل', 'تغيير', 'فوري'] },
  { id: 'C-012', title: 'إغلاق يومي', topic: 'ختام', date: '2026-04-21', time: '18:00', duration: '02:25', duration_sec: 145, speakers: ['أحمد', 'ريم'], confidence: 94, flags: 0, is_active: false, keywords: ['إنهاء', 'تلخيص', 'غد'] }
];

const SEED_TRANSCRIPTS = {
  'C-003': [
    { call_id: 'C-003', speaker_name: 'أحمد', speaker_slot: 's1', time_stamp: '00:03', text: 'السلام عليكم، خالد. <span class="keyword">الشحنة</span> جاهزة للإرسال يوم الخميس.', confidence: 0.97 },
    { call_id: 'C-003', speaker_name: 'خالد', speaker_slot: 's2', time_stamp: '00:08', text: 'وعليكم السلام. الموعد مناسب، لكن تأكد من <span class="highlight-word" data-tip="كلمة محتملة التشفير — ذكرت 3 مرات">العربة الجديدة</span> قبل الإرسال.', confidence: 0.89 },
    { call_id: 'C-003', speaker_name: 'أحمد', speaker_slot: 's1', time_stamp: '00:14', text: 'طيب، سأبلّغ الفريق. هل نثبت <span class="keyword">الاجتماع</span> قبل التسليم؟', confidence: 0.95 },
    { call_id: 'C-003', speaker_name: 'خالد', speaker_slot: 's2', time_stamp: '00:21', text: 'نعم، الساعة التاسعة صباح الاثنين عند <span class="highlight-word" data-tip="موقع بديل للاسم الحقيقي">النقطة المعتادة</span>.', confidence: 0.82 },
    { call_id: 'C-003', speaker_name: 'أحمد', speaker_slot: 's1', time_stamp: '00:28', text: 'متفقون. سأرسل التأكيد عبر القناة نفسها.', confidence: 0.96 },
    { call_id: 'C-003', speaker_name: 'خالد', speaker_slot: 's2', time_stamp: '00:34', text: 'ممتاز. لا تنسَ التنسيق مع <span class="highlight-word" data-tip="اسم رمزي محتمل">أبو محمد</span> قبل البدء.', confidence: 0.78 },
    { call_id: 'C-003', speaker_name: 'أحمد', speaker_slot: 's1', time_stamp: '00:42', text: 'مفهوم. سأتواصل معه اليوم.', confidence: 0.98 },
    { call_id: 'C-003', speaker_name: 'خالد', speaker_slot: 's2', time_stamp: '00:48', text: 'وأخبرني فور الجاهزية النهائية.', confidence: 0.91 }
  ]
};

['C-001', 'C-002', 'C-004', 'C-005', 'C-006', 'C-007', 'C-008', 'C-009', 'C-010', 'C-011', 'C-012'].forEach(cid => {
  const call = SEED_CALLS.find(c => c.id === cid);
  if (!call) return;
  const lines = [
    { text: 'السلام عليكم، نبدأ اليوم بمناقشة الموضوع.', c: 0.94 },
    { text: 'أهلاً، الوضع كما اتفقنا في المرة السابقة.', c: 0.91 },
    { text: 'ممتاز، نتابع حسب الخطة الحالية.', c: 0.95 },
    { text: 'سأعود لك بالتفاصيل خلال اليوم.', c: 0.93 }
  ];
  SEED_TRANSCRIPTS[cid] = lines.map((l, i) => ({
    call_id: cid,
    speaker_name: call.speakers[i % call.speakers.length],
    speaker_slot: `s${(i % 2) + 1}`,
    time_stamp: `00:${String(2 + i * 7).padStart(2, '0')}`,
    text: l.text,
    confidence: l.c
  }));
});

const SEED_ENTITIES = {
  'C-003': [
    { call_id: 'C-003', entity_type: 'person', label: 'أشخاص', value: 'أحمد' },
    { call_id: 'C-003', entity_type: 'person', label: 'أشخاص', value: 'خالد' },
    { call_id: 'C-003', entity_type: 'person', label: 'أشخاص', value: 'أبو محمد' },
    { call_id: 'C-003', entity_type: 'coded', label: 'كلمات مشفّرة محتملة', value: 'العربة الجديدة' },
    { call_id: 'C-003', entity_type: 'coded', label: 'كلمات مشفّرة محتملة', value: 'النقطة المعتادة' },
    { call_id: 'C-003', entity_type: 'coded', label: 'كلمات مشفّرة محتملة', value: 'أبو محمد' },
    { call_id: 'C-003', entity_type: 'event', label: 'أحداث', value: 'تسليم شحنة' },
    { call_id: 'C-003', entity_type: 'event', label: 'أحداث', value: 'اجتماع تمهيدي' },
    { call_id: 'C-003', entity_type: 'time', label: 'أزمنة', value: 'الاثنين ٩:٠٠' },
    { call_id: 'C-003', entity_type: 'time', label: 'أزمنة', value: 'الخميس' }
  ]
};

const SEED_CODED_TERMS = [
  { term: 'العربة الجديدة', occurrences: 3, first_seen: '2026-04-18', last_seen: '2026-04-21', risk: 'high', call_ids: ['C-002', 'C-003', 'C-008'] },
  { term: 'النقطة المعتادة', occurrences: 5, first_seen: '2026-04-17', last_seen: '2026-04-21', risk: 'high', call_ids: ['C-001', 'C-003', 'C-005', 'C-008', 'C-011'] },
  { term: 'أبو محمد', occurrences: 4, first_seen: '2026-04-20', last_seen: '2026-04-21', risk: 'medium', call_ids: ['C-003', 'C-004', 'C-008', 'C-011'] },
  { term: 'القناة الأخرى', occurrences: 2, first_seen: '2026-04-21', last_seen: '2026-04-21', risk: 'medium', call_ids: ['C-006', 'C-011'] },
  { term: 'الصيانة', occurrences: 6, first_seen: '2026-04-17', last_seen: '2026-04-21', risk: 'low', call_ids: ['C-001', 'C-002', 'C-004', 'C-007', 'C-009', 'C-012'] }
];

const SEED_REPORTS = [
  { id: 'R-001', title: 'ملخص يومي — 21 أبريل', report_type: 'يومي', date: '2026-04-21', size: '2.4 MB', icon: 'calendar', summary: 'تقرير شامل عن نشاط اليوم.' },
  { id: 'R-002', title: 'تحليل شبكة المتحدثين', report_type: 'شبكة', date: '2026-04-21', size: '1.8 MB', icon: 'network', summary: 'تحليل الروابط بين المتحدثين.' },
  { id: 'R-003', title: 'كشف الكلمات المشفرة', report_type: 'كلمات', date: '2026-04-21', size: '680 KB', icon: 'alert', summary: 'قائمة بالمصطلحات المشبوهة.' },
  { id: 'R-004', title: 'تقرير البصمات الصوتية', report_type: 'صوتي', date: '2026-04-20', size: '3.1 MB', icon: 'voice', summary: 'تحليل البصمات الصوتية للمتحدثين.' },
  { id: 'R-005', title: 'تحليل الأنماط الزمنية', report_type: 'زمني', date: '2026-04-20', size: '920 KB', icon: 'clock', summary: 'الأنماط الزمنية للمكالمات.' },
  { id: 'R-006', title: 'تقرير المتابعة الأسبوعي', report_type: 'أسبوعي', date: '2026-04-19', size: '4.7 MB', icon: 'stats', summary: 'مراجعة أداء الأسبوع.' }
];

// ═══ localStorage persistence ═══
const STORAGE_KEY = 'cie_demo_data_v1';

function loadData() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const data = JSON.parse(raw);
      if (data.version === 1) return data;
    }
  } catch (e) {}
  return null;
}

function saveData() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      version: 1,
      speakers: DB.speakers,
      calls: DB.calls,
      transcripts: DB.transcripts,
      entities: DB.entities,
      codedTerms: DB.codedTerms,
      reports: DB.reports,
      attachments: DB.attachments
    }));
  } catch (e) { console.warn('Storage full or unavailable', e); }
}

// ═══ In-memory DB ═══
const DB = (() => {
  const saved = loadData();
  if (saved) {
    return {
      speakers: saved.speakers || SEED_SPEAKERS,
      calls: saved.calls || SEED_CALLS,
      transcripts: saved.transcripts || SEED_TRANSCRIPTS,
      entities: saved.entities || SEED_ENTITIES,
      codedTerms: saved.codedTerms || SEED_CODED_TERMS,
      reports: saved.reports || SEED_REPORTS,
      attachments: saved.attachments || []
    };
  }
  return {
    speakers: JSON.parse(JSON.stringify(SEED_SPEAKERS)),
    calls: JSON.parse(JSON.stringify(SEED_CALLS)),
    transcripts: JSON.parse(JSON.stringify(SEED_TRANSCRIPTS)),
    entities: JSON.parse(JSON.stringify(SEED_ENTITIES)),
    codedTerms: JSON.parse(JSON.stringify(SEED_CODED_TERMS)),
    reports: JSON.parse(JSON.stringify(SEED_REPORTS)),
    attachments: []
  };
})();

// ═══ Analyzer (client-side) ═══
const AUDIO_EXTS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma', '.opus', '.webm', '.amr', '.3gp', '.aiff'];
const TRANSCRIPT_EXTS = ['.txt', '.srt', '.vtt', '.json', '.csv', '.md', '.doc', '.docx', '.rtf'];
const KNOWN_SPEAKERS = ['أحمد', 'خالد', 'سعود', 'فهد', 'ريم', 'نورة', 'محمد', 'عبدالله', 'سارة', 'لينا'];
const CODED_PATTERNS = [
  /العربة\s+الجديدة/g,
  /النقطة\s+المعتادة/g,
  /أبو\s+\S+/g,
  /القناة\s+الأخرى/g,
  /الصيانة/g
];

function getExt(filename) {
  const m = filename.match(/\.[^.]+$/);
  return m ? m[0].toLowerCase() : '';
}
function isAudio(filename) { return AUDIO_EXTS.includes(getExt(filename)); }
function isTranscript(filename) { return TRANSCRIPT_EXTS.includes(getExt(filename)); }

function parseSRT(text) {
  const lines = [];
  const blocks = text.trim().split(/\n\s*\n/);
  for (const block of blocks) {
    const rows = block.trim().split('\n');
    if (rows.length >= 3) {
      const tm = rows[1].match(/(\d{2}):(\d{2}):(\d{2})/);
      if (tm) {
        const [, h, m, s] = tm;
        const ts = parseInt(h) === 0 ? `${m}:${s}` : `${h}:${m}`;
        lines.push({ time_stamp: ts, text: rows.slice(2).join(' ').trim(), speaker: null });
      }
    }
  }
  return lines;
}

function parseVTT(text) {
  text = text.replace(/^WEBVTT[\s\S]*?\n\n/, '');
  const lines = [];
  const blocks = text.trim().split(/\n\s*\n/);
  for (const block of blocks) {
    const rows = block.trim().split('\n').filter(r => r.trim());
    const timeIdx = rows.findIndex(r => r.includes('-->'));
    if (timeIdx >= 0) {
      const tm = rows[timeIdx].match(/(\d{2}):(\d{2}):(\d{2})/);
      if (tm) {
        const [, h, m, s] = tm;
        const ts = parseInt(h) === 0 ? `${m}:${s}` : `${h}:${m}`;
        lines.push({ time_stamp: ts, text: rows.slice(timeIdx + 1).join(' ').trim(), speaker: null });
      }
    }
  }
  return lines;
}

function parseTXT(text) {
  const lines = [];
  let counter = 0;
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line) continue;
    let speaker = null;
    let content = line;
    const m = line.match(/^([\u0600-\u06FFa-zA-Z\s]+?)\s*[:：\-]\s*(.+)$/);
    if (m) {
      const potential = m[1].trim();
      if (KNOWN_SPEAKERS.includes(potential) || potential.length <= 10) {
        speaker = potential;
        content = m[2].trim();
      }
    }
    const ts_m = content.match(/^[\[\(](\d{1,2}:\d{2})[\]\)]\s*(.+)$/);
    let ts;
    if (ts_m) {
      ts = ts_m[1];
      content = ts_m[2].trim();
    } else {
      ts = `${String(Math.floor(counter / 60)).padStart(2, '0')}:${String(counter % 60).padStart(2, '0')}`;
      counter += 8;
    }
    lines.push({ time_stamp: ts, text: content, speaker });
  }
  return lines;
}

function parseJSON_(text) {
  try {
    const data = JSON.parse(text);
    const entries = Array.isArray(data) ? data : (data.lines || data.transcript || data.segments || []);
    return entries.filter(e => typeof e === 'object').map((e, i) => {
      let ts = e.time_stamp || e.timestamp || e.time || e.start;
      if (typeof ts === 'number') {
        ts = `${String(Math.floor(ts / 60)).padStart(2, '0')}:${String(Math.floor(ts) % 60).padStart(2, '0')}`;
      } else if (!ts) {
        ts = `${String(Math.floor(i * 8 / 60)).padStart(2, '0')}:${String((i * 8) % 60).padStart(2, '0')}`;
      }
      return { time_stamp: String(ts), text: e.text || e.content || '', speaker: e.speaker || e.speaker_name || null };
    });
  } catch (e) { return []; }
}

function parseCSV(text) {
  const lines = text.split('\n').filter(l => l.trim());
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
  const out = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',');
    const row = {};
    headers.forEach((h, j) => row[h] = (cols[j] || '').trim());
    const ts = row.time || row.timestamp || row.time_stamp || `${String(Math.floor((i - 1) * 8 / 60)).padStart(2, '0')}:${String(((i - 1) * 8) % 60).padStart(2, '0')}`;
    out.push({ time_stamp: ts, text: row.text || row.content || '', speaker: row.speaker || row.speaker_name || null });
  }
  return out;
}

function parseTranscript(text, filename) {
  const ext = getExt(filename);
  if (ext === '.srt') return parseSRT(text);
  if (ext === '.vtt') return parseVTT(text);
  if (ext === '.json') return parseJSON_(text);
  if (ext === '.csv') return parseCSV(text);
  return parseTXT(text);
}

function assignSpeakers(lines) {
  const existing = [...new Set(lines.filter(l => l.speaker).map(l => l.speaker))];
  const speakers = existing.length >= 2 ? existing.slice(0, 4) : ['أحمد', 'خالد'];
  const slotMap = {};
  for (let i = 0; i < lines.length; i++) {
    if (!lines[i].speaker) lines[i].speaker = speakers[i % speakers.length];
    const sp = lines[i].speaker;
    if (!slotMap[sp]) slotMap[sp] = `s${Object.keys(slotMap).length + 1}`;
    lines[i].speaker_slot = slotMap[sp];
    if (lines[i].confidence === undefined) {
      lines[i].confidence = parseFloat((0.82 + Math.random() * 0.16).toFixed(2));
    }
  }
  return lines;
}

function extractEntities(lines) {
  const entities = [];
  const seen = new Set();
  const fullText = lines.map(l => l.text || '').join(' ');

  [...new Set(lines.filter(l => l.speaker).map(l => l.speaker))].forEach(sp => {
    const k = `person:${sp}`;
    if (!seen.has(k)) { seen.add(k); entities.push({ entity_type: 'person', label: 'أشخاص', value: sp }); }
  });

  CODED_PATTERNS.forEach(pat => {
    const matches = fullText.match(pat);
    if (matches) matches.forEach(m => {
      const k = `coded:${m}`;
      if (!seen.has(k)) { seen.add(k); entities.push({ entity_type: 'coded', label: 'كلمات مشفّرة محتملة', value: m.trim() }); }
    });
  });

  [
    /(الساعة\s+\S+\s*(?:صباح[اً]?|مساء[ً]?)?)/g,
    /(يوم\s+(?:الأحد|الاثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت))/g,
    /(غد[اً]?|اليوم|الأسبوع\s+القادم|الشهر\s+القادم)/g
  ].forEach(pat => {
    const matches = fullText.matchAll(pat);
    for (const m of matches) {
      const k = `time:${m[1]}`;
      if (!seen.has(k)) { seen.add(k); entities.push({ entity_type: 'time', label: 'أزمنة', value: m[1].trim() }); }
    }
  });

  ['اجتماع', 'تسليم', 'استلام', 'توقيع', 'موعد', 'زيارة', 'مقابلة'].forEach(kw => {
    if (fullText.includes(kw)) {
      const k = `event:${kw}`;
      if (!seen.has(k)) { seen.add(k); entities.push({ entity_type: 'event', label: 'أحداث', value: kw }); }
    }
  });

  return entities;
}

function inferTopic(lines) {
  const text = lines.map(l => l.text || '').join(' ');
  if (/شحنة|تسليم|استلام/.test(text)) return 'تخطيط لوجستي';
  if (/عقد|توقيع|بنود/.test(text)) return 'مراجعة عقد';
  if (/اجتماع|موعد/.test(text)) return 'تنسيق';
  if (/طارئ|عاجل|فوري/.test(text)) return 'طارئ';
  return 'عام';
}

function formatDuration(sec) {
  const m = Math.floor(sec / 60), s = sec % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function analyzeAudioStub(filename, sizeBytes) {
  const duration = Math.max(30, Math.floor(sizeBytes / 16000));
  const nameLower = filename.toLowerCase();
  let template;
  if (/urgent|طارئ|emergency/.test(nameLower)) {
    template = [
      ['أحمد', 'مرحباً، هذه مكالمة عاجلة.'],
      ['خالد', 'تفضل، أنا أستمع.'],
      ['أحمد', 'نحتاج تغيير الموعد فوراً.'],
      ['خالد', 'طيب، سأتواصل مع الفريق حالاً.']
    ];
  } else if (/meeting|اجتماع/.test(nameLower)) {
    template = [
      ['أحمد', 'السلام عليكم، نبدأ الاجتماع الآن.'],
      ['خالد', 'وعليكم السلام، جاهز.'],
      ['سعود', 'لدي ملاحظات على البنود السابقة.'],
      ['أحمد', 'تفضل، اذكرها بالترتيب.']
    ];
  } else {
    template = [
      ['أحمد', 'السلام عليكم.'],
      ['خالد', 'وعليكم السلام. الشحنة جاهزة للإرسال.'],
      ['أحمد', 'متى تتوقع التسليم؟'],
      ['خالد', 'يوم الخميس عند النقطة المعتادة.'],
      ['أحمد', 'ممتاز، سأبلّغ الفريق.']
    ];
  }
  let cursor = 3;
  const lines = template.map(([spk, text]) => {
    const ts = `${String(Math.floor(cursor / 60)).padStart(2, '0')}:${String(cursor % 60).padStart(2, '0')}`;
    cursor += 5 + Math.floor(Math.random() * 4);
    return { time_stamp: ts, text, speaker: spk };
  });
  return {
    lines, duration_sec: duration, duration_fmt: formatDuration(duration),
    note: '⚠ هذا تفريغ تجريبي مُولَّد — في النسخة مع Backend الحقيقي يُستبدل بـ Whisper API.'
  };
}

async function processUpload(file, createCall = true, title = null) {
  const filename = file.name;
  const isA = isAudio(filename), isT = isTranscript(filename);
  if (!isA && !isT) throw new Error(`صيغة غير مدعومة: ${getExt(filename)}`);

  const kind = isA ? 'audio' : 'transcript';
  let result;

  if (kind === 'audio') {
    result = analyzeAudioStub(filename, file.size);
  } else {
    const text = await file.text();
    const lines = parseTranscript(text, filename);
    const duration = Math.max(30, lines.length * 8);
    result = {
      lines,
      duration_sec: duration,
      duration_fmt: formatDuration(duration),
      note: `تم تفريغ ${lines.length} سطر من الملف النصي.`
    };
  }

  result.lines = assignSpeakers(result.lines);
  const entities = extractEntities(result.lines);
  const speakers = [...new Set(result.lines.map(l => l.speaker).filter(Boolean))];
  const topic = inferTopic(result.lines);
  const flags = entities.filter(e => e.entity_type === 'coded').length;
  const conf = result.lines.length
    ? Math.round(result.lines.reduce((a, l) => a + (l.confidence || 0.9), 0) / result.lines.length * 100)
    : 0;
  const keywords = entities.filter(e => e.entity_type === 'event').map(e => e.value).slice(0, 5);

  const attachment = {
    id: Date.now(),
    call_id: null,
    kind,
    original_name: filename,
    stored_name: filename,
    mime_type: file.type || '',
    extension: getExt(filename),
    size_bytes: file.size,
    processing_status: 'done',
    analysis_notes: result.note,
    uploaded_at: new Date().toISOString()
  };

  let call_id = null;
  let transcript_preview = null;

  if (createCall) {
    const existingNums = DB.calls.map(c => {
      const m = c.id.match(/C-(\d+)/);
      return m ? parseInt(m[1]) : 0;
    });
    const nextNum = Math.max(...existingNums, 0) + 1;
    call_id = `C-${String(nextNum).padStart(3, '0')}`;
    const now = new Date();

    const callTitle = title || filename.replace(/\.[^.]+$/, '').substring(0, 50);

    DB.calls.unshift({
      id: call_id,
      title: callTitle,
      topic,
      date: now.toISOString().split('T')[0],
      time: now.toTimeString().substring(0, 5),
      duration: result.duration_fmt,
      duration_sec: result.duration_sec,
      confidence: conf,
      flags,
      speakers,
      keywords,
      is_active: false
    });

    DB.transcripts[call_id] = result.lines.map(l => ({
      call_id,
      speaker_name: l.speaker,
      speaker_slot: l.speaker_slot,
      time_stamp: l.time_stamp,
      text: l.text,
      confidence: l.confidence
    }));

    DB.entities[call_id] = entities.map(e => ({ ...e, call_id }));

    speakers.forEach(spk => {
      const existing = DB.speakers.find(s => s.name === spk);
      if (!existing) {
        const newId = `SPK_${String(DB.speakers.length + 1).padStart(2, '0')}`;
        const colors = ['purple', 'accent', 'coral', 'amber', 'blue', 'green', 'gray'];
        DB.speakers.push({
          id: newId, name: spk, role: 'متحدث جديد',
          color: colors[DB.speakers.length % colors.length],
          initials: spk.substring(0, 2), total_calls: 1,
          total_minutes: Math.floor(result.duration_sec / 60),
          total_words: result.lines.filter(l => l.speaker === spk).reduce((a, l) => a + (l.text || '').split(' ').length, 0),
          avg_confidence: conf, voiceprint_status: 'new',
          first_seen: now.toISOString().split('T')[0],
          last_seen: now.toISOString().split('T')[0]
        });
        _speakersCache = null; // invalidate cache
      } else {
        existing.total_calls += 1;
        existing.last_seen = now.toISOString().split('T')[0];
      }
    });

    attachment.call_id = call_id;
    transcript_preview = result.lines.slice(0, 4).map(l => ({
      speaker: l.speaker, time: l.time_stamp, text: (l.text || '').substring(0, 80)
    }));
  }

  DB.attachments.unshift(attachment);
  saveData();

  return {
    success: true,
    attachment,
    call_id,
    transcript_preview,
    message: `تمت معالجة الملف بنجاح — ${result.lines.length} سطر · ${entities.length} كيان`
  };
}

// ═══ Mock API ═══
function delay(ms = 120) { return new Promise(r => setTimeout(r, ms)); }

const api = {
  async health() { await delay(40); return { status: 'ok', service: 'Call Intelligence Engine (DEMO)' }; },

  async stats() {
    await delay();
    const avgConf = DB.calls.length
      ? Math.round(DB.calls.reduce((a, c) => a + c.confidence, 0) / DB.calls.length)
      : 0;
    const totalEntities = Object.values(DB.entities).flat().length;
    return {
      total_calls: DB.calls.length,
      total_speakers: DB.speakers.length,
      total_keywords: Math.max(totalEntities, 34),
      avg_accuracy: avgConf
    };
  },

  async calls(params = {}) {
    await delay();
    let list = [...DB.calls];
    if (params.filter === 'flagged') list = list.filter(c => c.flags > 0);
    else if (params.filter === 'today') list = list.filter(c => c.date === '2026-04-21');
    else if (params.filter === 'high-conf') list = list.filter(c => c.confidence >= 93);
    if (params.search) {
      const s = params.search;
      list = list.filter(c => c.title.includes(s) || c.id.includes(s) || (c.topic || '').includes(s));
    }
    list.sort((a, b) => (b.date + b.time).localeCompare(a.date + a.time));
    if (params.limit) list = list.slice(0, parseInt(params.limit));
    return list;
  },

  async call(id) {
    await delay();
    const c = DB.calls.find(x => x.id === id);
    if (!c) throw new Error('Call not found');
    return {
      ...c,
      transcript_lines: DB.transcripts[id] || [],
      entities: DB.entities[id] || []
    };
  },

  async relatedCalls(id) {
    await delay();
    const target = DB.calls.find(x => x.id === id);
    if (!target) return [];
    const scored = DB.calls.filter(c => c.id !== id).map(c => {
      const spkOverlap = c.speakers.filter(s => target.speakers.includes(s)).length;
      const kwOverlap = (c.keywords || []).filter(k => (target.keywords || []).includes(k)).length;
      return { call: c, score: spkOverlap * 2 + kwOverlap };
    }).filter(x => x.score > 0).sort((a, b) => b.score - a.score);
    return scored.slice(0, 4).map(x => x.call);
  },

  async speakers(params = {}) {
    await delay();
    let list = [...DB.speakers];
    if (params.filter && params.filter !== 'all') list = list.filter(s => s.voiceprint_status === params.filter);
    if (params.search) {
      const s = params.search;
      list = list.filter(sp => sp.name.includes(s) || sp.id.includes(s));
    }
    return list;
  },

  async speaker(id) {
    await delay();
    const s = DB.speakers.find(x => x.id === id);
    if (!s) throw new Error('Speaker not found');
    return s;
  },

  async speakerCalls(id) {
    await delay();
    const s = DB.speakers.find(x => x.id === id);
    if (!s) return [];
    return DB.calls.filter(c => c.speakers.includes(s.name));
  },

  async codedTerms() { await delay(); return [...DB.codedTerms].sort((a, b) => b.occurrences - a.occurrences); },

  async reports(params = {}) {
    await delay();
    let list = [...DB.reports];
    if (params.filter && params.filter !== 'all') list = list.filter(r => r.report_type === params.filter);
    if (params.search) {
      const s = params.search;
      list = list.filter(r => r.title.includes(s) || r.report_type.includes(s));
    }
    return list;
  },

  async report(id) {
    await delay();
    const r = DB.reports.find(x => x.id === id);
    if (!r) throw new Error('Report not found');
    return r;
  },

  async graph() {
    await delay();
    const activeCall = DB.calls.find(c => c.is_active) || DB.calls[0];
    const nodes = [];
    const edges = [];

    DB.speakers.forEach(sp => nodes.push({ id: `p-${sp.id}`, type: 'person', label: sp.name, sub: sp.id }));

    if (activeCall) {
      nodes.push({ id: `c-${activeCall.id}`, type: 'call', label: 'مكالمة', sub: activeCall.id });
      const entities = DB.entities[activeCall.id] || [];
      const seen = new Set();
      entities.forEach(e => {
        if (seen.has(e.value)) return;
        seen.add(e.value);
        let nodeType = e.entity_type;
        if (e.entity_type === 'coded') nodeType = 'keyword';
        const nid = `${e.entity_type}-${e.value}`;
        nodes.push({
          id: nid, type: nodeType,
          label: (e.entity_type === 'coded' || e.entity_type === 'keyword') ? `"${e.value}"` : e.value,
          sub: e.entity_type
        });
        const relMap = { person: 'تحدث مع', coded: 'تضمن', event: 'أشار إلى', time: 'حدث في' };
        edges.push({ source: `c-${activeCall.id}`, target: nid, label: relMap[e.entity_type] || 'مرتبط' });
      });
      (activeCall.speakers || []).forEach(name => {
        const sp = DB.speakers.find(s => s.name === name);
        if (sp) edges.push({ source: `c-${activeCall.id}`, target: `p-${sp.id}`, label: 'تحدث مع' });
      });
    }

    return { nodes, edges };
  },

  async supportedFormats() { await delay(); return { audio: AUDIO_EXTS, transcript: TRANSCRIPT_EXTS }; },

  async listUploads() { await delay(); return [...DB.attachments]; },

  async uploadFile(file, { title, createCall = true, onProgress } = {}) {
    if (onProgress) {
      for (let p = 10; p <= 90; p += 20) {
        onProgress(p);
        await delay(80);
      }
    }
    const result = await processUpload(file, createCall, title);
    if (onProgress) onProgress(100);
    await delay(100);
    return result;
  },

  async deleteUpload(id) {
    await delay();
    const idx = DB.attachments.findIndex(a => a.id === id);
    if (idx >= 0) DB.attachments.splice(idx, 1);
    saveData();
    return { success: true };
  }
};

window.resetDemoData = function() {
  if (confirm('إعادة تعيين بيانات الديمو؟ ستُحذف كل الرفعات والمكالمات الجديدة.')) {
    localStorage.removeItem(STORAGE_KEY);
    location.reload();
  }
};

// ═══ Navigation ═══
const PAGES = [
  { key: 'index', label: 'لوحة التحليل', url: 'index.html' },
  { key: 'calls', label: 'المكالمات', url: 'calls.html' },
  { key: 'uploads', label: 'رفع ملف', url: 'uploads.html' },
  { key: 'graph', label: 'شبكة المعرفة', url: 'graph.html' },
  { key: 'speakers', label: 'المتحدثون', url: 'speakers.html' },
  { key: 'reports', label: 'التقارير', url: 'reports.html' }
];

function buildTopbar(activeKey) {
  const nav = PAGES.map(p =>
    `<a href="${p.url}" class="nav-item${p.key === activeKey ? ' active' : ''}">${p.label}</a>`
  ).join('');
  return `
    <header class="topbar">
      <a href="index.html" class="brand">
        <div class="brand-mark">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12h2l2-7 4 14 3-10 2 5h5"/>
          </svg>
        </div>
        <div class="brand-text">
          <h1>Call Intelligence Engine</h1>
          <p>DEMO MODE · OFFLINE</p>
        </div>
      </a>
      <nav class="topbar-nav">${nav}</nav>
      <div class="topbar-actions">
        <div class="status-pill" id="status-pill">
          <span class="pulse-dot"></span>
          <span id="status-text">DEMO</span>
        </div>
        <div class="avatar" title="إعادة تعيين البيانات" onclick="resetDemoData()" style="cursor:pointer;">↻</div>
      </div>
    </header>
  `;
}

function buildBreadcrumb(items) {
  const parts = items.map((it, i) => {
    const isLast = i === items.length - 1;
    if (isLast) return `<span class="current">${it.label}</span>`;
    return `<a href="${it.url}">${it.label}</a><span class="sep">/</span>`;
  }).join('');
  return `<div class="breadcrumb">${parts}</div>`;
}

function mountTopbar(activeKey) {
  document.body.insertAdjacentHTML('afterbegin', buildTopbar(activeKey));
  const pill = document.getElementById('status-pill');
  const txt = document.getElementById('status-text');
  if (txt) txt.textContent = 'DEMO';
  if (pill) {
    pill.style.background = 'rgba(245, 166, 35, 0.08)';
    pill.style.borderColor = 'rgba(245, 166, 35, 0.3)';
    pill.style.color = 'var(--amber)';
    const dot = pill.querySelector('.pulse-dot');
    if (dot) dot.style.background = 'var(--amber)';
  }
}

// ═══ Utilities ═══
function formatNumber(n) { return new Intl.NumberFormat('ar').format(n); }

function confidenceColor(c) {
  if (c >= 93) return 'var(--green)';
  if (c >= 88) return 'var(--amber)';
  return 'var(--red)';
}

function confidenceBadge(c) {
  if (c >= 93) return 'badge-green';
  if (c >= 88) return 'badge-amber';
  return 'badge-red';
}

let _speakersCache = null;
async function getSpeakersMap() {
  if (_speakersCache) return _speakersCache;
  const speakers = await api.speakers();
  _speakersCache = {};
  speakers.forEach(s => { _speakersCache[s.name] = s; });
  return _speakersCache;
}

async function speakerColorClass(speakerName) {
  const map = await getSpeakersMap();
  return map[speakerName]?.color || 'gray';
}

function speakerColorClassSync(speakerName, speakersList = []) {
  const sp = speakersList.find(s => s.name === speakerName);
  return sp ? sp.color : 'gray';
}

function showApiError(msg) { console.warn('[Demo]', msg); }

function initTooltips() {
  let tooltip = document.getElementById('tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.id = 'tooltip';
    tooltip.className = 'tooltip';
    document.body.appendChild(tooltip);
  }
  document.querySelectorAll('[data-tip]').forEach(el => {
    if (el._tipBound) return;
    el._tipBound = true;
    el.addEventListener('mouseenter', () => {
      tooltip.textContent = el.getAttribute('data-tip');
      tooltip.classList.add('visible');
    });
    el.addEventListener('mousemove', (e) => {
      tooltip.style.left = (e.pageX + 12) + 'px';
      tooltip.style.top = (e.pageY - 34) + 'px';
    });
    el.addEventListener('mouseleave', () => tooltip.classList.remove('visible'));
  });
}

function buildWaveform(containerId, barsCount = 80) {
  const wf = document.getElementById(containerId);
  if (!wf) return;
  wf.innerHTML = '';
  for (let i = 0; i < barsCount; i++) {
    const bar = document.createElement('div');
    bar.className = 'wave-bar' + (i < 25 ? ' active' : '');
    const h = 15 + Math.abs(Math.sin(i * 0.4) + Math.cos(i * 0.7)) * 15 + Math.random() * 8;
    bar.style.height = h + 'px';
    wf.appendChild(bar);
  }
  let progress = 25;
  setInterval(() => {
    const bars = wf.querySelectorAll('.wave-bar');
    bars.forEach((bar, i) => {
      if (i < progress) bar.classList.add('active');
      else bar.classList.remove('active');
    });
    progress = (progress + 1) % barsCount;
  }, 200);
}

function showLoading(containerEl, message = 'جارٍ التحميل...') {
  if (typeof containerEl === 'string') containerEl = document.getElementById(containerEl);
  if (!containerEl) return;
  containerEl.innerHTML = `
    <div style="padding: 40px 20px; text-align: center; color: var(--text-3);">
      <div style="width: 32px; height: 32px; margin: 0 auto 14px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
      <div style="font-size: 13px;">${message}</div>
    </div>
    <style>@keyframes spin { to { transform: rotate(360deg); } }</style>
  `;
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}
