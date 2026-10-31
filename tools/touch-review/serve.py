#!/usr/bin/env python3
"""Local touch-review annotator: open inbox screenshots, mark ROI/click, export cards."""

from __future__ import annotations

import json
import re
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw

from common import ROOT, load_config

INDEX_MD = "INDEX.md"


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "unnamed"


def load_brief(image: Path) -> dict | None:
    bp = image.with_suffix(".brief.json")
    if not bp.is_file():
        return None
    try:
        return json.loads(bp.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"title": "说明文件损坏", "goal": f"请检查 {bp.name}", "steps": []}


def save_brief(image: Path, brief: dict) -> None:
    bp = image.with_suffix(".brief.json")
    bp.write_text(json.dumps(brief, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def list_cards(cfg: dict) -> list[dict]:
    cards = []
    for p in sorted(cfg["cards_dir"].glob("*/card.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        data = json.loads(p.read_text(encoding="utf-8"))
        data["_dir"] = p.parent.name
        cards.append(data)
    return cards


def exported_source_map(cfg: dict) -> dict[str, str]:
    """Map inbox png basename -> latest card id that was exported from it."""
    mapping: dict[str, str] = {}
    for c in list_cards(cfg):
        src = str(c.get("source_image") or "")
        name = Path(src).name
        if name and name not in mapping:
            mapping[name] = str(c.get("id") or "")
    return mapping


def mark_brief_exported(source: Path, card_id: str) -> None:
    brief = load_brief(source) or {
        "image": source.name,
        "title": source.stem,
        "goal": "已导出审查卡",
        "steps": [],
    }
    brief["exported"] = True
    brief["exported_card_id"] = card_id
    brief["exported_at"] = datetime.now(timezone.utc).isoformat()
    save_brief(source, brief)


def list_inbox(cfg: dict) -> list[dict]:
    exported = exported_source_map(cfg)
    files = sorted(cfg["inbox_dir"].glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    items = []
    for p in files:
        if p.name.startswith("_"):
            continue
        with Image.open(p) as im:
            w, h = im.size
        brief = load_brief(p)
        card_id = exported.get(p.name) or (brief or {}).get("exported_card_id") or ""
        is_exported = bool(card_id) or bool((brief or {}).get("exported"))
        # Backfill brief flags for older exports so UI stays consistent after refresh.
        if is_exported and brief is not None and not brief.get("exported"):
            mark_brief_exported(p, str(card_id))
            brief = load_brief(p)
        title_l = str((brief or {}).get("title") or "")
        goal_l = str((brief or {}).get("goal") or "")
        is_skip = bool((brief or {}).get("skip")) or ("不用标注" in title_l) or ("不用标注" in goal_l)
        needs_annotation = brief is not None and not is_exported and not is_skip
        items.append(
            {
                "name": p.name,
                "url": f"/inbox/{p.name}",
                "width": w,
                "height": h,
                "brief": brief,
                "title": (brief or {}).get("title") or p.name,
                "has_brief": brief is not None,
                "exported": is_exported,
                "exported_card_id": card_id or None,
                "skip": is_skip,
                "needs_annotation": needs_annotation,
            }
        )
    # pending tasks first, then unexported plain shots, then already exported
    items.sort(
        key=lambda it: (
            0 if it["needs_annotation"] else 1 if not it["exported"] else 2,
            -Path(cfg["inbox_dir"], it["name"]).stat().st_mtime,
        )
    )
    return items


def rebuild_index(cfg: dict) -> None:
    cards = list_cards(cfg)
    lines = [
        "# Touch Review Cards",
        "",
        f"Updated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "| id | label | click | roi | expected_next | note |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in cards:
        click = c.get("click")
        roi = c.get("roi")
        lines.append(
            "| `{id}` | {label} | `{click}` | `{roi}` | {expected} | {note} |".format(
                id=c.get("id", ""),
                label=c.get("label", ""),
                click=click,
                roi=roi,
                expected=(c.get("expected_next") or "").replace("|", "/"),
                note=(c.get("note") or "").replace("|", "/"),
            )
        )
    (cfg["cards_dir"] / INDEX_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_card(cfg: dict, payload: dict) -> dict:
    label = str(payload.get("label") or "").strip()
    if not label:
        raise ValueError("label is required")
    source_name = str(payload.get("source_image") or "").strip()
    source = cfg["inbox_dir"] / Path(source_name).name
    if not source.is_file():
        raise ValueError(f"source image not found: {source_name}")

    tw, th = cfg["target_size"]
    click = payload.get("click")
    roi = payload.get("roi")
    if click is not None:
        if not (isinstance(click, list) and len(click) == 2):
            raise ValueError("click must be [x, y]")
        click = [int(click[0]), int(click[1])]
    if roi is not None:
        if not (isinstance(roi, list) and len(roi) == 4):
            raise ValueError("roi must be [x, y, w, h]")
        roi = [int(v) for v in roi]
        if roi[2] <= 0 or roi[3] <= 0:
            raise ValueError("roi width/height must be > 0")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    card_id = f"{stamp}-{slugify(label)}"
    card_dir = cfg["cards_dir"] / card_id
    card_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(source) as im:
        im = im.convert("RGB")
        if im.size != (tw, th):
            im = im.resize((tw, th), Image.Resampling.LANCZOS)
        preview = im.copy()
        draw = ImageDraw.Draw(preview)
        if roi:
            x, y, w, h = roi
            draw.rectangle([x, y, x + w, y + h], outline=(0, 200, 80), width=3)
            crop = im.crop((x, y, x + w, y + h))
            crop.save(card_dir / "template.png", format="PNG")
        if click:
            cx, cy = click
            r = 10
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 64, 64), width=3)
            draw.line([cx - 16, cy, cx + 16, cy], fill=(255, 64, 64), width=2)
            draw.line([cx, cy - 16, cx, cy + 16], fill=(255, 64, 64), width=2)
        preview.save(card_dir / "preview.png", format="PNG")
        # keep a normalized copy of the source for the agent
        im.save(card_dir / "screen.png", format="PNG")

    card = {
        "id": card_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "note": str(payload.get("note") or "").strip(),
        "expected_next": str(payload.get("expected_next") or "").strip(),
        "source_image": str(source.relative_to(ROOT)).replace("\\", "/"),
        "image_size": [tw, th],
        "click": click,
        "roi": roi,
        "files": {
            "screen": f"review/cards/{card_id}/screen.png",
            "preview": f"review/cards/{card_id}/preview.png",
            "template": f"review/cards/{card_id}/template.png" if roi else None,
            "card": f"review/cards/{card_id}/card.json",
        },
        "pipeline_hint": {
            "recognition": "TemplateMatch" if roi else "DirectHit",
            "action": "Click",
            "template": f"image/{label}.png" if roi else None,
            "roi": roi,
            "target": click,
        },
    }
    (card_dir / "card.json").write_text(json.dumps(card, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")
    md = [
        f"# {card_id}",
        "",
        f"- label: `{label}`",
        f"- click: `{click}`",
        f"- roi: `{roi}`",
        f"- expected_next: {card['expected_next'] or '(none)'}",
        f"- note: {card['note'] or '(none)'}",
        "",
        "## Preview",
        "",
        f"![preview](preview.png)",
        "",
    ]
    if roi:
        md.extend(["## Template crop", "", "![template](template.png)", ""])
    (card_dir / "CARD.md").write_text("\n".join(md), encoding="utf-8")
    rebuild_index(cfg)
    mark_brief_exported(source, card_id)
    return card


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>MaaWW Touch Review</title>
  <style>
    :root { color-scheme: dark; --bg:#0f1419; --panel:#1a2332; --line:#2b3a4f; --text:#e7eef8; --muted:#9db0c7; --acc:#3d8bfd; --ok:#3dd68c; --bad:#ff6b6b; --warn:#f0c674; }
    * { box-sizing: border-box; }
    body { margin:0; font:14px/1.45 system-ui,Segoe UI,sans-serif; background:var(--bg); color:var(--text); }
    header { padding:12px 16px; border-bottom:1px solid var(--line); display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
    header h1 { font-size:16px; margin:0; font-weight:650; }
    header .hint { color:var(--muted); }
    main { display:grid; grid-template-columns: 300px 1fr 340px; min-height: calc(100vh - 54px); }
    aside, section { border-right:1px solid var(--line); padding:12px; }
    section { border-right:none; }
    h2 { margin:0 0 8px; font-size:13px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
    .list { display:flex; flex-direction:column; gap:6px; max-height:42vh; overflow:auto; }
    .item { padding:8px 10px; border:1px solid var(--line); border-radius:8px; background:var(--panel); cursor:pointer; }
    .item.active { border-color:var(--acc); }
    .item.todo { border-color:#7a6230; }
    .item.done { border-color:#2a5a40; opacity:.85; }
    .item small { display:block; color:var(--muted); }
    .badge { display:inline-block; margin-top:4px; padding:1px 6px; border-radius:999px; font-size:11px; background:#3a2d12; color:var(--warn); }
    .badge.ok { background:#163528; color:var(--ok); }
    .brief {
      margin-bottom:12px; padding:12px; border:1px solid #6b5424; border-radius:10px;
      background:linear-gradient(180deg,#2a2414,#1b1a14); color:#f6e7c2;
    }
    .brief h3 { margin:0 0 6px; font-size:15px; color:#ffe39a; }
    .brief .goal { margin:0 0 8px; font-size:14px; }
    .brief ol { margin:0; padding-left:18px; }
    .brief li { margin:4px 0; }
    .brief .avoid { margin-top:8px; color:#ffb4b4; }
    .brief.empty { border-color:var(--line); background:var(--panel); color:var(--muted); }
    .stage-wrap { overflow:auto; background:#070b10; border:1px solid var(--line); border-radius:10px; }
    canvas { display:block; cursor:crosshair; max-width:100%; height:auto; }
    label { display:block; margin:10px 0 4px; color:var(--muted); }
    input, textarea, select, button { width:100%; border-radius:8px; border:1px solid var(--line); background:var(--panel); color:var(--text); padding:8px 10px; }
    textarea { min-height:72px; resize:vertical; }
    .row { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    .btns { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
    button { cursor:pointer; }
    button.primary { background:var(--acc); border-color:transparent; color:#041018; font-weight:650; }
    button.ghost { background:transparent; }
    .mode { display:flex; gap:8px; margin:8px 0 12px; flex-wrap:wrap; }
    .mode button { width:auto; }
    .mode button.on { border-color:var(--ok); color:var(--ok); }
    .status { margin-top:10px; color:var(--muted); white-space:pre-wrap; }
    .status.ok { color:var(--ok); }
    .status.err { color:var(--bad); }
    @media (max-width: 1100px) { main { grid-template-columns: 1fr; } aside, section { border-right:none; border-bottom:1px solid var(--line); } }
  </style>
</head>
<body>
<header>
  <h1>MaaWW Touch Review</h1>
  <div class="hint">先读黄色「本次任务」→ 再框 ROI / 点点击点 → 导出审查卡</div>
  <button class="ghost" style="width:auto" id="btnRefresh">刷新列表</button>
</header>
<main>
  <aside>
    <h2>Inbox 截图</h2>
    <div class="list" id="inbox"></div>
    <h2 style="margin-top:16px">已导出 Cards</h2>
    <div class="list" id="cards"></div>
  </aside>
  <aside>
    <div id="briefBox" class="brief empty">
      <h3>请选择左侧截图</h3>
      <p class="goal">我会在截图旁写好「你要做什么」。有黄色任务条的优先处理。</p>
    </div>
    <h2>画面</h2>
    <div class="mode">
      <button id="modeRoi" class="on">1. ROI 框</button>
      <button id="modeClick">2. 点击点</button>
      <button id="clearMarks" class="ghost">清除标记</button>
    </div>
    <div class="stage-wrap"><canvas id="cv" width="1280" height="720"></canvas></div>
  </aside>
  <section>
    <h2>审查卡字段</h2>
    <p style="margin:0 0 8px;color:var(--muted)">通常会被任务说明自动填好，你只需核对后导出。</p>
    <label>label（节点/按钮名）</label>
    <input id="label" placeholder="TitleClickConnect" />
    <label>expected_next（点完后应出现）</label>
    <input id="expected" placeholder="登录界面 / 公告弹窗 / 进入游戏" />
    <label>note（给我的说明）</label>
    <textarea id="note" placeholder="补充你看到的细节"></textarea>
    <div class="row">
      <div>
        <label>click [x,y]</label>
        <input id="click" readonly placeholder="尚未点选" />
      </div>
      <div>
        <label>roi [x,y,w,h]</label>
        <input id="roi" readonly placeholder="尚未框选" />
      </div>
    </div>
    <div class="btns">
      <button class="primary" id="btnSave">导出审查卡</button>
      <button class="ghost" id="btnOpenIndex">打开 INDEX</button>
    </div>
    <div class="status" id="status"></div>
  </section>
</main>
<script>
const state = {
  mode: 'roi',
  image: null,
  source: null,
  brief: null,
  click: null,
  roi: null,
  drag: null,
  inbox: [],
};
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');

function setStatus(msg, kind='') {
  const el = document.getElementById('status');
  el.className = 'status ' + kind;
  el.textContent = msg;
}

function renderBrief(brief, name, exported) {
  const box = document.getElementById('briefBox');
  if (!brief) {
    box.className = 'brief empty';
    box.innerHTML = `<h3>${name || '无任务说明'}</h3><p class="goal">这张图还没有我写的任务说明。先处理带黄色「待标注」标记的截图；或等我补说明。</p>`;
    return;
  }
  if (exported || brief.exported) {
    const cid = brief.exported_card_id ? `（${brief.exported_card_id}）` : '';
    box.className = 'brief empty';
    box.innerHTML = `<h3>${brief.title || name || '已导出'}</h3>
      <p class="goal">这张截图已导出审查卡${cid}，无需再标。请处理其它黄色「待标注」项，或等我补新截图任务。</p>`;
    return;
  }
  const steps = (brief.steps || []).map(s => `<li>${s}</li>`).join('');
  const avoid = (brief.do_not || []).length
    ? `<div class="avoid"><strong>不要做：</strong>${brief.do_not.join('；')}</div>`
    : '';
  box.className = 'brief';
  box.innerHTML = `
    <h3>${brief.title || '本次任务'}</h3>
    <p class="goal"><strong>目标：</strong>${brief.goal || ''}</p>
    <ol>${steps}</ol>
    ${avoid}
  `;
}

function applyBriefDefaults(brief) {
  if (!brief) return;
  if (brief.suggested_label) document.getElementById('label').value = brief.suggested_label;
  if (brief.suggested_expected_next) document.getElementById('expected').value = brief.suggested_expected_next;
  if (brief.suggested_note) document.getElementById('note').value = brief.suggested_note;
}

function draw() {
  ctx.fillStyle = '#070b10';
  ctx.fillRect(0,0,cv.width,cv.height);
  if (state.image) ctx.drawImage(state.image, 0, 0, cv.width, cv.height);
  if (state.roi) {
    const [x,y,w,h] = state.roi;
    ctx.strokeStyle = '#3dd68c';
    ctx.lineWidth = 3;
    ctx.strokeRect(x,y,w,h);
  }
  if (state.drag) {
    const {x0,y0,x1,y1} = state.drag;
    ctx.strokeStyle = '#3dd68c';
    ctx.lineWidth = 2;
    ctx.setLineDash([6,4]);
    ctx.strokeRect(Math.min(x0,x1), Math.min(y0,y1), Math.abs(x1-x0), Math.abs(y1-y0));
    ctx.setLineDash([]);
  }
  if (state.click) {
    const [x,y] = state.click;
    ctx.strokeStyle = '#ff6b6b';
    ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(x,y,10,0,Math.PI*2); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x-16,y); ctx.lineTo(x+16,y); ctx.moveTo(x,y-16); ctx.lineTo(x,y+16); ctx.stroke();
  }
}

function canvasPos(ev) {
  const rect = cv.getBoundingClientRect();
  const x = Math.round((ev.clientX - rect.left) * (cv.width / rect.width));
  const y = Math.round((ev.clientY - rect.top) * (cv.height / rect.height));
  return [Math.max(0, Math.min(cv.width-1, x)), Math.max(0, Math.min(cv.height-1, y))];
}

async function refresh(autoSelect=false) {
  const data = await fetch('/api/list').then(r => r.json());
  state.inbox = data.inbox || [];
  const inbox = document.getElementById('inbox');
  inbox.innerHTML = '';
  state.inbox.forEach(it => {
    const div = document.createElement('div');
    div.className = 'item'
      + (state.source === it.name ? ' active' : '')
      + (it.needs_annotation ? ' todo' : '')
      + (it.exported ? ' done' : '');
    let badge = '';
    if (it.needs_annotation) badge = '<span class="badge">待标注</span>';
    else if (it.exported) badge = '<span class="badge ok">已导出</span>';
    else if (it.skip) badge = '<span class="badge ok">无需标注</span>';
    div.innerHTML = `<strong>${it.title || it.name}</strong>
      <small>${it.name}<br>${it.width}×${it.height}</small>
      ${badge}`;
    div.onclick = () => loadImage(it);
    inbox.appendChild(div);
  });
  const cards = document.getElementById('cards');
  cards.innerHTML = '';
  data.cards.forEach(c => {
    const div = document.createElement('div');
    div.className = 'item';
    div.innerHTML = `<strong>${c.label}</strong><small>${c.id}<br>click ${JSON.stringify(c.click)} · roi ${JSON.stringify(c.roi)}</small>`;
    cards.appendChild(div);
  });
  if (autoSelect && !state.source) {
    const first = state.inbox.find(it => it.needs_annotation) || state.inbox[0];
    if (first) loadImage(first);
  }
}

function loadImage(it) {
  const name = typeof it === 'string' ? it : it.name;
  const meta = typeof it === 'string' ? state.inbox.find(x => x.name === name) : it;
  const url = (meta && meta.url) || ('/inbox/' + name);
  const img = new Image();
  img.onload = () => {
    state.image = img;
    state.source = name;
    state.brief = meta ? meta.brief : null;
    state.click = null;
    state.roi = null;
    state.drag = null;
    document.getElementById('click').value = '';
    document.getElementById('roi').value = '';
    document.getElementById('label').value = '';
    document.getElementById('expected').value = '';
    document.getElementById('note').value = '';
    applyBriefDefaults(state.brief);
    renderBrief(state.brief, name, meta && meta.exported);
    draw();
    refresh(false);
    if (meta && meta.exported) {
      setStatus('此截图已导出，可忽略。请选黄色「待标注」项。', 'ok');
      return;
    }
    setStatus(state.brief
      ? '已加载任务：「' + (state.brief.title || name) + '」。先框绿色 ROI，再点红色点击点。'
      : '已加载 ' + name + '（无任务说明）');
  };
  img.src = url + '?t=' + Date.now();
}

cv.addEventListener('mousedown', ev => {
  if (!state.image) return;
  const [x,y] = canvasPos(ev);
  if (state.mode === 'click') {
    state.click = [x,y];
    document.getElementById('click').value = JSON.stringify(state.click);
    draw();
  } else {
    state.drag = {x0:x,y0:y,x1:x,y1:y};
  }
});
cv.addEventListener('mousemove', ev => {
  if (!state.drag) return;
  const [x,y] = canvasPos(ev);
  state.drag.x1 = x; state.drag.y1 = y;
  draw();
});
function endDrag(ev) {
  if (!state.drag) return;
  const [x,y] = canvasPos(ev);
  const {x0,y0} = state.drag;
  const rx = Math.min(x0,x), ry = Math.min(y0,y);
  const rw = Math.abs(x-x0), rh = Math.abs(y-y0);
  state.drag = null;
  if (rw >= 4 && rh >= 4) {
    state.roi = [rx, ry, rw, rh];
    document.getElementById('roi').value = JSON.stringify(state.roi);
  }
  draw();
}
cv.addEventListener('mouseup', endDrag);
cv.addEventListener('mouseleave', endDrag);

document.getElementById('modeClick').onclick = () => {
  state.mode = 'click';
  document.getElementById('modeClick').classList.add('on');
  document.getElementById('modeRoi').classList.remove('on');
};
document.getElementById('modeRoi').onclick = () => {
  state.mode = 'roi';
  document.getElementById('modeRoi').classList.add('on');
  document.getElementById('modeClick').classList.remove('on');
};
document.getElementById('clearMarks').onclick = () => {
  state.click = null; state.roi = null; state.drag = null;
  document.getElementById('click').value = '';
  document.getElementById('roi').value = '';
  draw();
};
document.getElementById('btnRefresh').onclick = () => refresh(false);
document.getElementById('btnOpenIndex').onclick = () => window.open('/cards/INDEX.md', '_blank');
document.getElementById('btnSave').onclick = async () => {
  if (!state.source) { setStatus('请先选择截图', 'err'); return; }
  if (!state.roi) { setStatus('请先用「ROI 框」圈住目标按钮/文字', 'err'); return; }
  if (!state.click) { setStatus('请再用「点击点」点一下要点的位置', 'err'); return; }
  const body = {
    source_image: state.source,
    label: document.getElementById('label').value,
    expected_next: document.getElementById('expected').value,
    note: document.getElementById('note').value,
    click: state.click,
    roi: state.roi,
  };
  const res = await fetch('/api/save', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) { setStatus(data.error || '保存失败', 'err'); return; }
  setStatus('已导出 review/cards/' + data.id + '\n把这个 id 发给我，或直接说「已导出」。', 'ok');
  refresh(false);
};
refresh(true);
draw();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    cfg: dict

    def log_message(self, fmt: str, *args) -> None:  # quieter
        sys_stderr = __import__("sys").stderr
        sys_stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, raw, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ("/", "/index.html"):
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/list":
            self._json(200, {"inbox": list_inbox(self.cfg), "cards": list_cards(self.cfg)})
            return
        if path.startswith("/inbox/"):
            name = Path(path[len("/inbox/") :]).name
            fp = self.cfg["inbox_dir"] / name
            if not fp.is_file():
                self._send(404, b"not found", "text/plain")
                return
            self._send(200, fp.read_bytes(), "image/png")
            return
        if path.startswith("/cards/"):
            rel = path[len("/cards/") :]
            fp = (self.cfg["cards_dir"] / rel).resolve()
            if not str(fp).startswith(str(self.cfg["cards_dir"])) or not fp.is_file():
                self._send(404, b"not found", "text/plain")
                return
            ctype = "image/png" if fp.suffix.lower() == ".png" else "text/markdown; charset=utf-8"
            if fp.suffix.lower() == ".json":
                ctype = "application/json; charset=utf-8"
            self._send(200, fp.read_bytes(), ctype)
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/save":
            self._json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8"))
            card = save_card(self.cfg, payload)
            self._json(200, card)
        except Exception as exc:  # noqa: BLE001
            self._json(400, {"error": str(exc)})


def main() -> int:
    cfg = load_config()
    Handler.cfg = cfg
    host = cfg.get("host", "127.0.0.1")
    port = int(cfg.get("port", 8765))
    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}/"
    print(f"touch-review UI: {url}")
    print(f"inbox: {cfg['inbox_dir']}")
    print(f"cards: {cfg['cards_dir']}")
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001
        pass
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
