import os
import sys
import socket
import time
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from pywebio.pin import *
from .config import GeneratorConfig, load_config, auto_discover_config
from .generator import generate_code
from .extractor import extract_schema
from .parser import parse_schema

# --- CUSTOM CSS ---
CSS = """
.pywebio { background-color: #f8fafc; font-family: 'Inter', sans-serif; }
.footer { display: none; }
.card { border-radius: 12px; padding: 20px; background: white; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
button { border-radius: 8px !important; font-weight: 600 !important; transition: 0.2s !important; }
.log-terminal { background: #1e293b; color: #38bdf8; font-family: 'Fira Code', monospace; padding: 15px; border-radius: 8px; font-size: 0.85rem; height: 250px; overflow-y: auto; }
"""

def log_message(msg, type="info"):
    colors = {"info": "#38bdf8", "success": "#4ade80", "error": "#f87171"}
    timestamp = time.strftime("%H:%M:%S")
    with use_scope('logs', clear=False):
        put_html(f'<div style="color: {colors.get(type)}">[{timestamp}] {msg}</div>')
    scroll_to('logs', position='bottom')

def handle_generate():
    # Retrieve data from pinned widgets
    framework = pin.framework
    url = pin.url
    out = pin.out
    hooks = pin.hooks

    with use_scope('status_area', clear=True):
        put_loading(shape='grow', color='primary').style('display: inline-block; margin-right: 10px;')
        put_text("Processing Schema...").style('display: inline-block;')

    log_message(f"Starting generation for {framework}...")
    
    try:
        config = GeneratorConfig(
            framework=framework,
            frontend_dir=out,
            openapi_url=url,
            hooks_mode=hooks
        )

        # Smart defaults logic
        if config.framework == "fastapi": config.app_module = "main:app"
        elif config.framework == "django": config.django_settings = "myproject.settings"

        raw_schema = extract_schema(config)
        log_message("Schema extracted successfully.", "success")
        
        parsed_data = parse_schema(raw_schema, config)
        log_message(f"Parsed {len(parsed_data.get('endpoints', []))} endpoints.")
        
        generate_code(parsed_data, config)
        log_message("Code emission complete.", "success")

        with use_scope('status_area', clear=True):
            put_success(f"✨ Successfully generated code to {out}")
            put_markdown(f"**Integration Ready:** `import {{ useGetUsers }} from '{out}/hooks'`")

    except Exception as e:
        log_message(f"Error: {str(e)}", "error")
        with use_scope('status_area', clear=True):
            put_error(f"Generation Failed: Check logs below.")

def run_ui():
    config_pywebio(title="API Sync Gen", theme="dark")
    put_html(f"<style>{CSS}</style>")

    # --- TOP NAV ---
    put_row([
        put_html("<h2>⚡ api-sync-generator</h2>").style('margin: 0;'),
        put_link("Documentation", url="#").style('text-align: right; align-self: center;')
    ], size="70% 30%").style('padding: 20px 0; border-bottom: 2px solid #e2e8f0; margin-bottom: 20px;')

    auto_config = auto_discover_config()

    # --- MAIN CONTENT LAYOUT ---
    put_row([
        # LEFT COLUMN: Settings
        put_column([
            put_html("<div class='card'>"),
            put_markdown("### ⚙️ Configuration"),
            
            put_text("Backend Framework"),
            put_select("framework", options=["fastapi", "django"], value=auto_config.framework),
            
            put_text("OpenAPI URL / Path"),
            put_input("url", value=auto_config.openapi_url or "http://localhost:8000/openapi.json"),
            
            put_text("Frontend Output Directory"),
            put_input("out", value=auto_config.frontend_dir),
            
            put_text("React Mode"),
            put_select("hooks", options=["react_query", "react", "nextjs_actions", "none"], value="react_query"),
            
            put_button("Generate Client Assets", onclick=handle_generate, color="primary", block=True).style('margin-top: 20px;'),
            put_html("</div>")
        ]),

        # RIGHT COLUMN: Status & Logs
        put_column([
            put_scope('status_area'),
            put_html("<div class='card' style='margin-top: 20px;'>"),
            put_markdown("### 📜 Activity Log"),
            put_html("<div class='log-terminal'>"),
            put_scope('logs'),
            put_html("</div>"),
            put_html("</div>")
        ])
    ], size="40% 60%").style('gap: 30px;')

# --- SERVER BOILERPLATE ---
def get_free_port(start_port=8080):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError: continue
    return start_port

def start_ui():
    port = get_free_port(8080)
    print(f"🚀 Dashboard running at: http://localhost:{port}")
    start_server(run_ui, port=port, debug=True, auto_open_webbrowser=True)

if __name__ == '__main__':
    start_ui()