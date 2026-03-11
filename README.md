# docs-dashboard

Lightweight web dashboard for browsing any project's `docs/` folder.
Auto-classifies documents, shows MD/HTML sync status, and renders content in-browser.

## Quick Start

```bash
git clone https://github.com/YOUR_USER/docs-dashboard.git
cd docs-dashboard

# Setup for your project
./setup.sh /path/to/your/project/docs my-project

# Run
docker compose up -d --build
```

Open **http://localhost:15000**

## Features

- **Auto-classification**: Documents grouped by subfolder name, or by custom keywords via `.docs-dashboard.json`
- **Sync status**: Green (synced), Yellow (outdated), Red (missing HTML), Purple (HTML only), Blue (custom HTML)
- **MD/HTML viewer**: Tab switch between rendered formats
- **Sync engine**: One-click MD to HTML conversion (preserves custom HTML like D3.js visualizations)
- **Docker**: Single container, volume-mounted docs folder

## Custom Categories

Place `.docs-dashboard.json` in your `docs/` folder:

```json
{
  "categories": {
    "Architecture": ["architecture", "design"],
    "Reports": ["report", "analysis"],
    "API": ["api", "endpoint", "spec"]
  }
}
```

Without this file, documents are classified by subfolder name (files in root go to "General").

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCS_PATH` | `.` | Path to docs folder |
| `PROJECT_NAME` | _(empty)_ | Shown in dashboard header |
| `PORT` | `15000` | Host port |
| `HTML_LANG` | `en` | `lang` attribute for generated HTML |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Dashboard configuration |
| GET | `/api/docs` | Document list with metadata |
| GET | `/api/docs/view/<path>` | Render document content |
| POST | `/api/docs/sync` | Sync all outdated MD to HTML |
| POST | `/api/docs/sync/<path>` | Sync single file |

## Claude Code Skill

Copy `skill/setup-docs-dashboard.md` to your project's `.claude/commands/` to enable `/setup-docs-dashboard`:

```bash
cp skill/setup-docs-dashboard.md /path/to/project/.claude/commands/
```

## License

MIT
