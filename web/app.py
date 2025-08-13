from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv  # type: ignore

from orchestration.main_graph import build_graph
from utils.io_utils import create_output_dir
from agents.social_media_agent import generate_social
from agents.image_agent import generate_image


load_dotenv()

app = FastAPI(title="Multi-Agent Content Marketing Web")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Expose outputs dir for static file serving (images)
OUTPUT_ROOT = os.getenv("OUTPUT_ROOT", "outputs")
os.makedirs(OUTPUT_ROOT, exist_ok=True)
app.mount("/outputs-static", StaticFiles(directory=OUTPUT_ROOT), name="outputs_static")


class RunRequest(BaseModel):
    topic: str
    no_image: bool = True


def _read_file(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def _read_json(path: str) -> Optional[Dict[str, Any]]:
    import json

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return (
        """
        <!doctype html>
        <html>
        <head>
            <meta charset='utf-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1'>
            <title>Multi-Agent Content Marketing</title>
            <style>
                :root { --bg:#0b1020; --panel:#121933; --muted:#7a8bab; --txt:#e6ecff; --brand:#7c9cff; --ok:#2ecc71; --warn:#ffcc00; --err:#ff6b6b; }
                * { box-sizing: border-box; }
                body { margin:0; background: var(--bg); color: var(--txt); font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Inter, sans-serif; }
                header { display:flex; align-items:center; justify-content:space-between; padding: 16px 20px; border-bottom: 1px solid #1b2450; background: #0c1430; }
                header h1 { font-size: 18px; margin: 0; }
                .container { display:grid; grid-template-columns: 280px 1fr; min-height: calc(100vh - 58px); }
                aside { border-right: 1px solid #1b2450; background: #0d1637; padding: 14px; }
                main { padding: 16px 20px; }
                .field { margin-bottom: 10px; }
                label { display:block; font-size: 12px; color: var(--muted); margin-bottom: 6px; }
                input[type=text] { width:100%; padding:10px 12px; border-radius:8px; border:1px solid #243066; background:#0b1536; color: var(--txt); }
                .btn { padding: 10px 14px; border-radius: 8px; border:1px solid #33407a; background: #142158; color: var(--txt); cursor:pointer; }
                .btn[disabled] { opacity: 0.6; cursor:not-allowed; }
                .row { display:flex; gap:8px; align-items:center; }
                .tabs { display:flex; gap:8px; margin: 16px 0 10px; }
                .tab { padding: 8px 12px; border-radius:8px; background:#0f1a42; border:1px solid #243066; color: var(--muted); cursor:pointer; }
                .tab.active { background:#142158; color: var(--txt); border-color:#3a4aa0; }
                .panel { background: var(--panel); border:1px solid #243066; border-radius: 10px; padding: 12px; }
                .toolbar { display:flex; gap:8px; justify-content:flex-end; margin: 8px 0; }
                pre { background: #0b1536; padding: 12px; border-radius: 10px; overflow:auto; border:1px solid #1e2a5a; }
                .list { list-style:none; margin:0; padding:0; }
                .list li { padding: 8px 10px; border-radius: 8px; border:1px solid #243066; background:#0b1536; margin-bottom:8px; cursor:pointer; }
                .list li:hover { border-color:#3a4aa0; }
                .status { font-size: 12px; color: var(--muted); margin-left: 10px; }
                .stepper { display:flex; gap:10px; align-items:center; font-size:12px; color: var(--muted); }
                .dot { width:8px; height:8px; border-radius:50%; background:#3a4aa0; }
                .dot.ok { background: var(--ok); }
                .dot.run { background: var(--warn); }
                .dot.err { background: var(--err); }
            </style>
        </head>
        <body>
            <header>
                <h1>Multi-Agent Content Marketing</h1>
                <div class="stepper"><span class="dot" id="s1"></span>Research <span class="dot" id="s2"></span>Content <span class="dot" id="s3"></span>Social <span class="dot" id="s4"></span>Image</div>
            </header>
            <div class="container">
                <aside>
                    <div class="field">
                        <label for="topic">Topic</label>
                        <input id="topic" type="text" placeholder="eco friendly water bottle" />
                    </div>
                    <div class="row">
                        <button class="btn" id="run_btn" onclick="run()">Generate</button>
                        <label class="status"><input id="no_image" type="checkbox" checked /> Skip Image</label>
                    </div>
                    <div style="margin-top:16px; font-size:12px; color:var(--muted);">Recent Runs</div>
                    <ul class="list" id="history"></ul>
                </aside>
                <main>
                    <div class="tabs">
                        <div class="tab active" data-tab="blog" onclick="showTab('blog')">Blog</div>
                        <div class="tab" data-tab="seo" onclick="showTab('seo')">SEO</div>
                        <div class="tab" data-tab="social" onclick="showTab('social')">Social</div>
                        <div class="tab" data-tab="research" onclick="showTab('research')">Research</div>
                        <div class="tab" data-tab="images" onclick="showTab('images')">Images</div>
                    </div>
                    <div class="toolbar">
                        <button class="btn" onclick="copyCurrent()">Copy</button>
                        <button class="btn" onclick="downloadZip()">Download ZIP</button>
                        <button class="btn" onclick="regenerateSocial()">Regenerate Social</button>
                        <button class="btn" onclick="regenerateSocial()">Regenerate Social</button>
                        <button class="btn" onclick="regenerateImage()">Regenerate Image</button>
                        <span class="status" id="status"></span>
                    </div>
                    <div class="panel">
                        <div id="tab_blog"><pre id="blog"></pre></div>
                        <div id="tab_seo" style="display:none;"><pre id="seo"></pre></div>
                        <div id="tab_social" style="display:none;"><pre id="social"></pre></div>
                        <div id="tab_research" style="display:none;"><pre id="research"></pre></div>
                        <div id="tab_images" style="display:none;">
                            <div style="display:flex; gap:12px; align-items:flex-start; flex-wrap:wrap;">
                                <div>
                                    <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">Hero</div>
                                    <img id="hero" alt="hero" style="max-width:100%; border:1px solid #243066; border-radius:8px;" />
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
            <script>
                let currentFolder = null;
                let currentTab = 'blog';
                function setStep(id, cls) { const el = document.getElementById(id); el.classList.remove('ok','run','err'); if (cls) el.classList.add(cls); }
                function resetSteps() { ['s1','s2','s3','s4'].forEach(id => setStep(id, null)); }
                function showTab(tab){ currentTab = tab; document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active')); document.querySelector('.tab[data-tab="'+tab+'"]').classList.add('active');
                    document.querySelectorAll('[id^=tab_]').forEach(p=>p.style.display='none'); document.getElementById('tab_'+tab).style.display='block'; }
                async function loadHistory(){
                    try { const r = await fetch('/outputs/list'); const j = await r.json(); const h = document.getElementById('history'); h.innerHTML=''; (j.outputs||[]).reverse().slice(0,30).forEach(folder=>{
                        const li = document.createElement('li'); li.textContent = folder; li.onclick=()=>viewFolder(folder); h.appendChild(li);
                    }); } catch(e){}
                }
                async function viewFolder(folder){
                    try { const r = await fetch('/outputs/details?folder='+encodeURIComponent(folder)); const data = await r.json(); currentFolder = folder;
                        document.getElementById('blog').innerText = data.blog_md || '';
                        document.getElementById('seo').innerText = JSON.stringify(data.seo||{}, null, 2);
                        document.getElementById('social').innerText = JSON.stringify(data.social||{}, null, 2);
                        document.getElementById('research').innerText = JSON.stringify(data.research||{}, null, 2);
                        if (data.images && data.images.hero_url) { document.getElementById('hero').src = data.images.hero_url; }
                        document.getElementById('status').innerText = folder;
                    } catch(e) { document.getElementById('status').innerText = 'Error: '+e; }
                }
                async function run() {
                    const btn = document.getElementById('run_btn'); btn.disabled = true;
                    const topic = document.getElementById('topic').value || 'eco friendly water bottle';
                    const no_image = document.getElementById('no_image').checked;
                    document.getElementById('status').innerText = 'Running...'; resetSteps(); setStep('s1','run');
                    try {
                        const resp = await fetch('/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ topic, no_image }) });
                        setStep('s1','ok'); setStep('s2','run');
                        const data = await resp.json();
                        setStep('s2','ok'); setStep('s3','ok'); if (!no_image) setStep('s4','ok');
                        currentFolder = (data.output_dir||'').split('/').slice(-1)[0];
                        document.getElementById('status').innerText = 'Done → '+data.output_dir;
                        document.getElementById('blog').innerText = data.blog_md || '';
                        document.getElementById('seo').innerText = JSON.stringify(data.seo || {}, null, 2);
                        document.getElementById('social').innerText = JSON.stringify(data.social || {}, null, 2);
                        document.getElementById('research').innerText = JSON.stringify(data.research || {}, null, 2);
                        if (data.images && data.images.hero_url) { document.getElementById('hero').src = data.images.hero_url; }
                        loadHistory();
                    } catch (e) {
                        setStep('s1','err'); document.getElementById('status').innerText = 'Error: ' + e;
                    } finally { btn.disabled = false; }
                }
                function copyCurrent(){ let text=''; if(currentTab==='blog') text=document.getElementById('blog').innerText; if(currentTab==='seo') text=document.getElementById('seo').innerText; if(currentTab==='social') text=document.getElementById('social').innerText; if(currentTab==='research') text=document.getElementById('research').innerText; navigator.clipboard.writeText(text); }
                function downloadZip(){ if(!currentFolder){ alert('No run selected.'); return; } window.location.href = '/outputs/zip?folder='+encodeURIComponent(currentFolder); }
                async function regenerateSocial(){ if(!currentFolder){ alert('Run something first.'); return; }
                    try { const r = await fetch('/outputs/details?folder='+encodeURIComponent(currentFolder)); const d = await r.json(); const topic = (d.research && d.research.topic) || (document.getElementById('topic').value || 'topic');
                        const body = { topic, no_image:true };
                        const resp = await fetch('/run', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
                        const data = await resp.json(); document.getElementById('social').innerText = JSON.stringify(data.social||{}, null, 2); showTab('social');
                    } catch(e){ document.getElementById('status').innerText = 'Error: '+e; }
                }
                loadHistory();
                async function regenerateImage(){ if(!currentFolder){ alert('Run something first.'); return; }
                    try { const resp = await fetch('/image?folder='+encodeURIComponent(currentFolder), { method:'POST' }); const data = await resp.json(); if (data.images && data.images.hero_url) { document.getElementById('hero').src = data.images.hero_url; showTab('images'); } }
                    catch(e){ document.getElementById('status').innerText = 'Error: '+e; }
                }
            </script>
        </body>
        </html>
        """
    )


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/outputs/list")
async def list_outputs() -> Dict[str, List[str]]:
    root = os.getenv("OUTPUT_ROOT", "outputs")
    try:
        items = sorted([f for f in os.listdir(root) if os.path.isdir(os.path.join(root, f))])
        return {"outputs": items}
    except Exception:
        return {"outputs": []}


def _safe_join_output(folder: str) -> Optional[str]:
    root = os.getenv("OUTPUT_ROOT", "outputs")
    base = Path(root).resolve()
    target = (base / folder).resolve()
    if not str(target).startswith(str(base)):
        return None
    if not target.exists() or not target.is_dir():
        return None
    return str(target)


@app.get("/outputs/details")
async def output_details(folder: str) -> JSONResponse:
    safe = _safe_join_output(folder)
    if not safe:
        return JSONResponse(status_code=400, content={"error": "invalid folder"})
    blog_path = os.path.join(safe, "blog.md")
    seo_path = os.path.join(safe, "seo.json")
    social_path = os.path.join(safe, "social.json")
    research_path = os.path.join(safe, "research.json")
    data = {
        "folder": folder,
        "blog_md": _read_file(blog_path),
        "seo": _read_json(seo_path),
        "social": _read_json(social_path),
        "research": _read_json(research_path),
        "images": {
            "hero_url": f"/outputs-static/{folder}/hero.png" if os.path.exists(os.path.join(safe, "hero.png")) else None
        }
    }
    return JSONResponse(content=data)


@app.get("/outputs/zip")
async def zip_output(folder: str):
    safe = _safe_join_output(folder)
    if not safe:
        return JSONResponse(status_code=400, content={"error": "invalid folder"})
    tmp_dir = tempfile.mkdtemp()
    zip_base = os.path.join(tmp_dir, folder)
    archive = shutil.make_archive(zip_base, 'zip', root_dir=safe)
    filename = os.path.basename(archive)
    return FileResponse(archive, media_type='application/zip', filename=filename)

@app.post("/run")
async def run_pipeline(req: RunRequest) -> JSONResponse:
    include_image = not req.no_image
    output_dir = create_output_dir(req.topic)
    app_graph = build_graph(include_image=include_image)
    state = {"topic": req.topic, "output_dir": output_dir}
    final_state = app_graph.invoke(state)

    blog_path = os.path.join(output_dir, "blog.md")
    seo_path = os.path.join(output_dir, "seo.json")
    social_path = os.path.join(output_dir, "social.json")
    research_path = os.path.join(output_dir, "research.json")

    data = {
        "output_dir": output_dir,
        "blog_md": _read_file(blog_path),
        "seo": _read_json(seo_path),
        "social": _read_json(social_path),
        "research": _read_json(research_path),
        "final_state": final_state,
        "images": {
            "hero_url": f"/outputs-static/{os.path.basename(output_dir)}/hero.png" if os.path.exists(os.path.join(output_dir, "hero.png")) else None
        }
    }
    return JSONResponse(content=data)


@app.post("/image")
async def generate_image_for_folder(folder: str) -> JSONResponse:
    safe = _safe_join_output(folder)
    if not safe:
        return JSONResponse(status_code=400, content={"error": "invalid folder"})
    blog_path = os.path.join(safe, "blog.md")
    blog_md = _read_file(blog_path) or ""
    img = generate_image(blog_md, safe)
    data = {
        "images": {
            "status": img.get("status"),
            "hero_url": f"/outputs-static/{folder}/hero.png" if os.path.exists(os.path.join(safe, "hero.png")) else None
        }
    }
    return JSONResponse(content=data)


