## multi_agent_content_marketing

An end-to-end, free, local-first Multi‑Agent Content Marketing System. Given a topic or product, it generates:

- SEO keywords and competitor highlights
- A Markdown blog post with SEO tags
- Social media snippets (Twitter/X, LinkedIn, Instagram)
- Optional hero image and thumbnails via a local Stable Diffusion WebUI

### Why this project

- 100% free and local: no paid APIs required
- Parallel multi-agent orchestration with LangGraph
- Modular, documented, and GitHub-ready

### Quick Start

1) Install Python 3.10+

2) Create and activate a virtual environment

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell
```

3) Install dependencies

```bash
pip install -r requirements.txt
```

4) Configure environment

Copy `.env_example` to `.env` and edit values as needed.

```bash
copy .env_example .env  # Windows
```

5) (Optional) Use a cloud LLM to run without local models

Set one of the following in `.env`:

- OpenAI-compatible server: `TEXTGEN_BASE_URL`, `TEXTGEN_API_KEY`, `TEXTGEN_MODEL`
- Hugging Face Inference: `HUGGINGFACE_API_TOKEN`, `HUGGINGFACE_MODEL`

6) Run the CLI or Web UI

```bash
python run.py --topic "eco friendly water bottle"  # add --no-image to skip image generation

Web UI (FastAPI):

```bash
uvicorn web.app:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000` and use the form to generate content.
```

Outputs will be saved to `outputs/{timestamp}_{slug}/`.

### Project Structure

```text
multi_agent_content_marketing/
├─ agents/
│  ├─ research_agent.py
│  ├─ content_writer.py
│  ├─ social_media_agent.py
│  └─ image_agent.py
├─ orchestration/
│  └─ main_graph.py
├─ utils/
│  ├─ io_utils.py
│  └─ llm.py
├─ sample_outputs/
│  └─ eco_friendly_water_bottle/
│     ├─ research.json
│     ├─ blog.md
│     ├─ seo.json
│     └─ social.json
├─ outputs/  # gitignored
├─ run.py
├─ requirements.txt
├─ .env_example
├─ .gitignore
└─ LICENSE (MIT)
```

### Orchestration with LangGraph

The system uses LangGraph to coordinate agents. Research runs first, content writing uses research, then social and image generation run in parallel.

```mermaid
flowchart TD
    A[START] --> B[Research Agent]
    B --> C[Content Writer Agent]
    C --> D[Social Media Agent]
    C --> E[Image Agent (optional)]
    D --> F[END]
    E --> F[END]
```

### Agents

- Research Agent: `pytrends` for Google Trends, `BeautifulSoup4` + `requests` for competitor highlights (DuckDuckGo HTML results). Saves `research.json`.
- Content Writer Agent: Local LLM via `llama-cpp-python`. Generates Markdown blog and SEO tags. Saves `blog.md` and `seo.json`.
- Social Media Agent: Uses the same local LLM (or fallback templates) to create X/LinkedIn/Instagram snippets. Saves `social.json`.
- Image Agent (optional): Talks to local Stable Diffusion WebUI (`/sdapi/v1/txt2img`). Saves images into the output folder.

All agents gracefully degrade if tools are unavailable (e.g., missing local LLM or SD WebUI).

### Local LLM Setup (llama.cpp via llama-cpp-python)

1) Install `llama-cpp-python` (already in requirements). CPU-only works by default; GPU acceleration requires extra steps per your hardware.

2) Download a quantized GGUF model (pick one that fits your machine):

- [Qwen2-1.5B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2-1.5B-Instruct-GGUF)
- [Mistral-7B-Instruct-v0.2-GGUF](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF)
- [Phi-3-mini-4k-instruct-gguf](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf)

3) Set `LLM_MODEL_PATH` in `.env` to the `.gguf` file path. Optional tuning vars: `LLM_CTX_SIZE`, `LLM_N_THREADS`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE`.

If no model is found, the app falls back to deterministic templates so it still runs locally.

### Stable Diffusion (optional)

1) Install AUTOMATIC1111 Stable Diffusion WebUI locally and run it.

- [AUTOMATIC1111 WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui)

2) Ensure the API is enabled (usually default at `http://127.0.0.1:7860`).
3) Set `SD_WEBUI_URL` in `.env`. If unavailable, the image step is skipped.

### How to Run

```bash
python run.py --topic "your topic here"
```

Flags:

- `--no-image`: skip the Image Agent
- `--output-root`: override the default `outputs/` directory

### Example Output

See `sample_outputs/eco_friendly_water_bottle/` for example files.

### Security & Config

- `.env` and secrets are not committed. See `.env_example` for variables.
- Outputs and models are gitignored by default.

### License

MIT — see `LICENSE`.

# Multi_Agent_Content_Marketing