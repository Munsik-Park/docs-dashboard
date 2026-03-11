"""Docs Dashboard — generic FastAPI server for browsing any project's documentation."""

import json
import os
from pathlib import Path
from datetime import datetime

import markdown
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

DOCS_DIR = Path(os.environ.get("DOCS_DIR", "/app/docs"))
PROJECT_NAME = os.environ.get("PROJECT_NAME", "")
HTML_LANG = os.environ.get("HTML_LANG", "en")
CUSTOM_CONFIG_FILE = ".docs-dashboard.json"

app = FastAPI(title="Docs Dashboard")
app.mount("/static/docs", StaticFiles(directory=str(DOCS_DIR)), name="static_docs")


# ---------------------------------------------------------------------------
# Category classification
# ---------------------------------------------------------------------------

def _load_custom_config() -> dict | None:
    """Load optional .docs-dashboard.json from the docs folder."""
    config_path = DOCS_DIR / CUSTOM_CONFIG_FILE
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def classify_doc(rel_path: str) -> str:
    """Auto-classify a document.

    Priority:
    1. Folder-based: docs/specs/foo.md → "Specs"
    2. Custom config: .docs-dashboard.json keywords
    3. Fallback: "General"
    """
    parts = Path(rel_path).parts

    # Strategy A: subfolder name as category
    if len(parts) > 1:
        return parts[0].replace("-", " ").replace("_", " ").title()

    # Strategy B: custom keyword config
    config = _load_custom_config()
    if config and "categories" in config:
        lower = rel_path.lower()
        for cat, keywords in config["categories"].items():
            if any(kw in lower for kw in keywords):
                return cat

    return "General"


# ---------------------------------------------------------------------------
# Document scanning
# ---------------------------------------------------------------------------

def is_custom_html(html_path: Path) -> bool:
    """Detect if HTML has custom content (D3, charts, large inline data)
    that should NOT be overwritten by MD→HTML sync."""
    size = html_path.stat().st_size
    if size > 50_000:
        return True
    try:
        head = html_path.read_text(encoding="utf-8")[:2000]
        if any(m in head for m in ["d3.js", "d3.v", "chart.js", "plotly", "<canvas"]):
            return True
    except Exception:
        pass
    return False


def scan_docs() -> list[dict]:
    """Scan docs directory and return metadata for all md/html files."""
    files: dict[str, dict] = {}

    for path in sorted(DOCS_DIR.rglob("*")):
        if path.is_dir():
            continue
        suffix = path.suffix.lower()
        if suffix not in (".md", ".html"):
            continue
        if path.name == CUSTOM_CONFIG_FILE:
            continue

        rel = path.relative_to(DOCS_DIR)
        stem = str(rel.with_suffix(""))
        mtime = path.stat().st_mtime
        size = path.stat().st_size

        if stem not in files:
            files[stem] = {
                "stem": stem,
                "category": classify_doc(str(rel)),
                "md": None,
                "html": None,
            }

        entry = {
            "path": str(rel),
            "mtime": mtime,
            "mtime_str": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M"),
            "size": size,
        }

        if suffix == ".md":
            files[stem]["md"] = entry
        else:
            files[stem]["html"] = entry

    result = []
    for stem, info in sorted(files.items()):
        md = info["md"]
        html = info["html"]

        custom = False
        if html:
            custom = is_custom_html(DOCS_DIR / html["path"])

        if md and html:
            if custom:
                sync = "custom_html"
            elif md["mtime"] > html["mtime"] + 60:
                sync = "outdated"
            else:
                sync = "synced"
        elif md and not html:
            sync = "missing_html"
        elif html and not md:
            sync = "html_only"
        else:
            sync = "unknown"

        result.append({
            "stem": stem,
            "category": info["category"],
            "md": md,
            "html": html,
            "sync": sync,
            "custom_html": custom,
        })

    return result


def render_md_to_html(md_path: Path) -> str:
    """Convert markdown file to HTML body string."""
    content = md_path.read_text(encoding="utf-8")
    return markdown.markdown(
        content,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
    )


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/config")
def get_config():
    return {"project_name": PROJECT_NAME, "html_lang": HTML_LANG}


@app.get("/api/docs")
def list_docs():
    return scan_docs()


@app.get("/api/docs/view/{path:path}")
def view_doc(path: str):
    full = DOCS_DIR / path
    if not full.exists() or not full.is_file():
        raise HTTPException(404, f"File not found: {path}")

    if full.suffix.lower() == ".html":
        return HTMLResponse(full.read_text(encoding="utf-8"))

    if full.suffix.lower() == ".md":
        body = render_md_to_html(full)
        return HTMLResponse(body)

    raise HTTPException(400, "Unsupported file type")


@app.post("/api/docs/sync")
def sync_all():
    docs = scan_docs()
    synced = []
    errors = []

    for doc in docs:
        if doc["sync"] in ("outdated", "missing_html"):
            if not doc["md"] or doc.get("custom_html"):
                continue
            md_path = DOCS_DIR / doc["md"]["path"]
            html_path = md_path.with_suffix(".html")
            try:
                body = render_md_to_html(md_path)
                title = doc["stem"].replace("-", " ").replace("/", " — ").title()
                html_content = generate_styled_html(title, body)
                html_path.write_text(html_content, encoding="utf-8")
                synced.append(str(html_path.relative_to(DOCS_DIR)))
            except Exception as e:
                errors.append({"file": doc["stem"], "error": str(e)})

    return {"synced": synced, "errors": errors, "total": len(synced)}


@app.post("/api/docs/sync/{path:path}")
def sync_one(path: str):
    md_path = DOCS_DIR / path
    if not md_path.exists() or md_path.suffix.lower() != ".md":
        raise HTTPException(400, "Path must be an existing .md file")

    html_path = md_path.with_suffix(".html")
    body = render_md_to_html(md_path)
    title = md_path.stem.replace("-", " ").replace("_", " ").title()
    html_content = generate_styled_html(title, body)
    html_path.write_text(html_content, encoding="utf-8")

    return {"synced": str(html_path.relative_to(DOCS_DIR))}


def generate_styled_html(title: str, body: str) -> str:
    """Wrap rendered markdown in a styled HTML document."""
    return f"""<!DOCTYPE html>
<html lang="{HTML_LANG}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, Roboto, 'Noto Sans', sans-serif;
    background: #f8f9fa; color: #333; padding: 40px 20px; line-height: 1.7;
}}
.container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }}
h1 {{ font-size: 1.8em; margin-bottom: 8px; color: #1a1a2e; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
h2 {{ font-size: 1.4em; margin: 30px 0 12px; color: #2c3e50; border-left: 4px solid #3498db; padding-left: 12px; }}
h3 {{ font-size: 1.15em; margin: 24px 0 8px; color: #34495e; }}
p {{ margin: 10px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
th {{ background: #37474f; color: #fff; padding: 10px 12px; text-align: left; font-size: 0.9em; }}
td {{ padding: 8px 12px; border-bottom: 1px solid #e0e0e0; font-size: 0.9em; }}
tr:hover {{ background: #f5f5f5; }}
code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 0.88em; }}
pre {{ background: #2d2d2d; color: #f8f8f2; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 12px 0; }}
pre code {{ background: none; color: inherit; }}
ul, ol {{ margin: 10px 0; padding-left: 24px; }}
li {{ margin: 4px 0; }}
hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 24px 0; }}
strong {{ color: #1a1a2e; }}
blockquote {{ border-left: 4px solid #3498db; padding: 10px 16px; margin: 12px 0; background: #f0f7ff; color: #555; }}
</style>
</head>
<body>
<div class="container">
<h1>{title}</h1>
{body}
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Dashboard SPA
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard():
    index_path = Path(__file__).parent / "templates" / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))
