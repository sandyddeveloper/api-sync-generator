<div align="center">

# ⚡ api-sync-generator

**The Ultimate Developer Experience (DX) Automator for Python & TypeScript**

[![PyPI version](https://badge.fury.io/py/api-sync-generator.svg)](https://badge.fury.io/py/api-sync-generator)
[![Python Versions](https://img.shields.io/pypi/pyversions/api-sync-generator.svg)](https://pypi.org/project/api-sync-generator/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

*Stop writing manual API fetchers, standardizing types, and writing identical form validations twice.* <br> Let your backend write your frontend integration code **in less than 2 seconds**.

---

</div>

`api-sync-generator` is an intelligent bridge that connects your Python backend (**FastAPI** or **Django**) directly to your TypeScript frontend (**React**, **Next.js**, **Vite**). By reading your backend's OpenAPI schema, it instantly generates 100% type-safe API clients, advanced caching hooks, runtime form validations, and documentation.

## ✨ The Features That Make It Unbeatable

- **🪄 Zero-Config Interactive Setup**: Run `api-sync init` to get up and running through an interactive terminal wizard. No config files to memorize.
- **🛡️ Auto-Zod Runtime Validation**: We parse your backend Pydantic/Django constraints (`minLength`, `regex`, `max`) and generate strict `z.object()` schemas for perfect `react-hook-form` validation out of the box.
- **⚛️ TanStack React Query Ready**: Automatically generates professional `useQuery` and `useMutation` hooks giving your frontend free data caching, background refetching, and pagination primitives.
- **📚 Intelligent TSDoc Injection**: Your Python docstrings and API descriptions are injected directly into the generated TypeScript (`/** ... */`), giving your frontend team native IDE auto-completion guidance.
- **⏱️ Live Watch Daemon**: Run `api-sync --watch`. The moment a backend developer saves a Python file, the frontend TypeScript code is instantly regenerated in the background.
- **📖 Auto-Generated Dev Docs**: Dynamically generates comprehensive **Markdown Integration Guides** outlining the *What*, *Why*, and *How* of every exposed endpoint for your frontend team.

---

## 🚀 Quickstart (The 2-Minute Integration)

### 🥇 The "Zero-Install" Magic Command (Fastest)
If you don't even want to install the package or manage virtual environments, you can run it perfectly using `uvx` or `pipx` (just like `npx` in JavaScript!). This downloads the tool into a temporary environment, runs the Web UI, and cleans up when you close it:

```bash
pipx run --spec git+https://github.com/sandyddeveloper/api-sync-generator.git api-sync ui
```

### 🥈 Traditional Installation
If you prefer to install the package straight from GitHub into your backend or global environment:
```bash
pip install git+https://github.com/sandyddeveloper/api-sync-generator.git
```

**1. Initialize your Project**
Drop into your project and run the interactive setup wizard. It will ask you 3 simple questions (framework type, frontend output path, and hooks preference) and configure your setup automatically!
```bash
api-sync init
```

### 3. Generate!
Run the sync command. Watch it fetch your schema, strip internal routes, translate types, and generate your entire frontend data layer instantly:
```bash
api-sync
```

*(Want real-time sync while you code? Just run `api-sync --watch`!)*

### Or just use the Web UI!
If you don't like configuring via terminal or typing out URL flags, you can spin up the built-in localhost dashboard. It automatically scans your folders, pre-fills your frameworks, and generates your types through a beautiful web form:
```bash
api-sync ui
```

---

## 🛠️ What Exactly Gets Generated?

When you run `api-sync`, it targets your specified frontend directory (e.g., `./frontend/src/api/`) and generates a pristine, highly-optimized codebase:

| Generated File | What it does for you |
|---|---|
| `types.ts` | 100% perfectly translated TypeScript interfaces (`export interface User {...}`) mapped from Python types. |
| `validations.ts` | Strict **Zod** (`z.infer<>`) schemas mirroring backend constraints. Drop these straight into your frontend forms! |
| `api.ts` | The type-safe fetch client handling URL pathing, query params, and intelligent error bubbling. |
| `hooks.ts` | Ready-to-use TanStack `useQuery` / `useMutation` hooks so you never have to write a `useEffect` data fetcher again. |
| `API_INTEGRATION.md` | An auto-written guide with fully copy-pasteable React components demonstrating exactly how to call every endpoint. |
| `QUICKSTART.md` | A summarized fast-track guide tailored to your specific API schema. |

---

## ⚙️ Advanced Usage & Configuration

### Dynamic "One-Off" Runs (No Config Required)
Want to grab a schema from a remote server without setting up a `pyproject.toml` file? You can pass all configurations directly as flags!
```bash
api-sync --url https://api.mycompany.com/openapi.json --framework fastapi --hooks react_query --out ./src/api
```

### 🔒 Schemas Behind Authentication (The cURL Hack)
If your OpenAPI schema is hidden behind an API Key or Bearer Token limit, you can simply paste the raw `curl` command directly into the CLI. The tool will parse the headers out and extract the schema perfectly:
```bash
api-sync --curl "curl -X GET 'https://api.mycompany.com/openapi.json' -H 'Authorization: Bearer my-secret-token'"
```

### The `pyproject.toml` Configuration File
If you bypass the `api-sync init` wizard, you can manually configure the tool in the root of your Python backend via `pyproject.toml`:

```toml
[tool.api-sync]
# The path where generated TS files will be dropped
frontend_dir = "../frontend/src/api"

# Your backend framework ("fastapi" or "django")
framework = "fastapi"

# (FastAPI Only) Where your FastAPI app instance lives
app_module = "main:app"

# (Django Only) Where your Django settings module lives
django_settings = "myproject.settings"

# Hook Generation Strategy ("react_query", "react", "nextjs_actions", "none")
hooks_mode = "react_query"

# Exclude endpoints marked with these OpenAPI tags
exclude_tags = ["@internal", "@admin_only"]
```

## 🧠 Framework Support

### FastAPI
Works perfectly out of the box. ensure `app_module` points to the file where your `FastAPI()` instance is created. `api-sync` will spin up the app in memory, extract the live OpenAPI schema, and cleanly shut down.

### Django (Django REST Framework)
Requires the incredibly popular `drf-spectacular` package. `api-sync` hooks gracefully into spectacular's schema generation pipeline to extract models and viewsets accurately.

## 🤝 Contributing
Contributions are absolutely welcome! Please feel free to submit a Pull Request to help us make frontend integration a zero-friction experience for every Python team.

## 📄 License
MIT License. See `LICENSE` for more information.