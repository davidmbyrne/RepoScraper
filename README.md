# RepoScraper

**Find GitHub repositories by architectural patterns using AI analysis.**

RepoScraper ingests repositories from GitHub, analyzes their architecture using GPT-5, and lets you search by patterns like "microservices", "event-driven", "clean architecture", and more.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5-purple)

---

## Features

- 🔍 **GitHub Search** — Search GitHub repos by language, stars, and keywords
- 🤖 **AI Analysis** — GPT-5 analyzes README and file structure to detect architectural patterns
- 🏷️ **Pattern Detection** — Identifies microservices, clean architecture, event-driven, serverless, and more
- 📊 **Confidence Scores** — Each detected pattern includes a confidence score
- 🎨 **Web Dashboard** — Beautiful UI for searching and managing indexed repos
- 🗄️ **SQLite Database** — Persistent storage of repos and their architecture tags

---

## Quick Start

### 1. Prerequisites

- Python 3.9+
- OpenAI API key
- GitHub Personal Access Token

### 2. Clone & Install

```bash
cd RepoScraper
pip3 install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
OPENAI_API_KEY="sk-your-openai-api-key"
GITHUB_TOKEN="github_pat_your-github-token"
```

**Getting API Keys:**

| Key | Where to get it |
|-----|-----------------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `GITHUB_TOKEN` | [github.com/settings/tokens](https://github.com/settings/tokens) → Generate new token (classic) → Select `public_repo` scope |

### 4. Run the Server

```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

### 5. Open the Dashboard

Navigate to **http://localhost:8000** in your browser.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web Dashboard                            │
│              (HTML/CSS/JS served by FastAPI)                │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ GitHub API   │  │ OpenAI API   │  │ SQLite DB    │       │
│  │ Integration  │  │ (GPT-5)      │  │              │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Ingestion Flow

1. **Search GitHub** → Find repos matching your criteria
2. **Fetch Metadata** → Get README, file tree, stars, language
3. **GPT-5 Analysis** → Send README + file structure to GPT-5
4. **Extract Patterns** → GPT-5 returns structured JSON with:
   - Architectural patterns (microservices, monolith, serverless, etc.)
   - Design patterns (repository, factory, observer, etc.)
   - Infrastructure (containerized, kubernetes, cloud-native, etc.)
   - Frameworks detected
5. **Store Results** → Save to SQLite with confidence scores
6. **Search** → Query indexed repos by pattern

---

## API Reference

### Health Check

```bash
GET /health
```

### GitHub Search

```bash
GET /api/github/search?language=python&min_stars=1000&max_results=20&query=web+framework
```

| Param | Type | Description |
|-------|------|-------------|
| `language` | string | Filter by programming language |
| `min_stars` | int | Minimum star count (default: 100) |
| `max_results` | int | Max repos to return (default: 20, max: 100) |
| `query` | string | Additional search terms |

### Ingest Repository

```bash
POST /api/repos/ingest/{owner}/{repo}?analyze=true
```

Fetches a repo from GitHub, stores it, and optionally runs GPT-5 analysis.

**Example:**
```bash
curl -X POST "http://localhost:8000/api/repos/ingest/fastapi/fastapi?analyze=true"
```

### Search by Architecture

```bash
GET /api/search?query=microservices+python&min_confidence=0.5&limit=20
```

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search terms (patterns, languages, frameworks) |
| `min_confidence` | float | Minimum confidence score 0-1 (default: 0.5) |
| `limit` | int | Max results (default: 20) |

### List Indexed Repos

```bash
GET /api/repos?language=python&min_stars=1000&limit=50
```

### List All Tags

```bash
GET /api/tags?tag_type=architectural_pattern
```

| Tag Types |
|-----------|
| `architectural_pattern` |
| `design_pattern` |
| `infrastructure` |
| `framework` |

### Re-analyze Repository

```bash
POST /api/repos/analyze/{repo_id}
```

---

## Dashboard Usage

### Search Tab
Search your indexed repositories by architectural patterns. Try queries like:
- `microservices python`
- `clean architecture`
- `kubernetes containerized`
- `event-driven kafka`

### Discover Tab
1. Enter search terms and select a language
2. Set minimum stars filter
3. Click "Search GitHub"
4. Click "Analyze & Index" on any repo to ingest it

### Indexed Tab
View all analyzed repositories with their detected architecture tags. Click on popular tags to search for similar repos.

---

## Project Structure

```
RepoScraper/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & routes
│   ├── database.py          # SQLAlchemy models (Repository, ArchitectureTag)
│   ├── schemas.py           # Pydantic request/response models
│   ├── config.py            # Environment configuration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── github_service.py    # GitHub API wrapper (PyGithub)
│   │   └── analysis_service.py  # GPT-5 architecture analysis
│   └── static/
│       ├── index.html       # Dashboard HTML
│       ├── styles.css       # Styling (custom dark theme)
│       └── app.js           # Frontend JavaScript
├── requirements.txt         # Python dependencies
├── .env                     # API keys (not committed)
├── reposcraper.db          # SQLite database (created on first run)
├── agents.md               # Original project plan
└── README.md               # This file
```

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `OPENAI_MODEL` | No | Model to use (default: `gpt-4o`) |
| `DEBUG` | No | Enable debug mode (`true`/`false`) |

### Changing the OpenAI Model

Edit `.env`:
```env
OPENAI_MODEL="gpt-5"
```

Or for cost savings during development:
```env
OPENAI_MODEL="gpt-4o-mini"
```

---

## Development

### Running in Development Mode

```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables hot reloading when you modify files.

### Viewing API Docs

FastAPI auto-generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Database

The SQLite database (`reposcraper.db`) is created automatically on first run. To reset:

```bash
rm reposcraper.db
```

---

## Troubleshooting

### "Rate limit exceeded" from GitHub

Without a `GITHUB_TOKEN`, you're limited to 60 requests/hour. With a token, you get 5,000/hour.

### "Address already in use"

Kill the existing process:
```bash
lsof -ti:8000 | xargs kill -9
```

### OpenAI API Errors

Check that your `OPENAI_API_KEY` is valid and has sufficient credits.

### No results in Search

Make sure you've ingested some repositories first using the Discover tab.

---

## Cost Estimates

| Service | Estimate |
|---------|----------|
| GitHub API | Free (5,000 req/hour with token) |
| OpenAI GPT-5 | ~$0.05-0.10 per repo analyzed |

With aggressive caching and limiting README size, you can analyze ~100-200 repos for $10-15.

---

## License

MIT

---

## Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) — Modern Python web framework
- [PyGithub](https://pygithub.readthedocs.io/) — GitHub API wrapper
- [OpenAI](https://openai.com/) — GPT-5 for architecture analysis
- [SQLAlchemy](https://www.sqlalchemy.org/) — Database ORM
