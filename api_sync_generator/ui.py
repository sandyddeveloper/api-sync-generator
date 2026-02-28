import os
import sys
import socket
from pywebio import start_server
from pywebio.input import *
from pywebio.output import *
from .config import GeneratorConfig, load_config
from .generator import generate_code
from .extractor import extract_schema
from .parser import parse_schema

def find_framework():
    if os.path.exists("main.py"):
        return "fastapi"
    elif os.path.exists("manage.py"):
        return "django"
    return "fastapi"

def find_frontend():
    for root, dirs, files in os.walk("."):
        if "package.json" in files:
            if "src" in dirs:
                return os.path.join(root, "src", "api")
            return os.path.join(root, "api")
    return "./frontend/src/api"

def run_ui():
    put_markdown("# ⚡ api-sync-generator")
    put_text("The easiest way to generate your frontend API clients.")
    
    put_html("<hr>")
    
    auto_framework = find_framework()
    auto_frontend = find_frontend()

    config_data = input_group("Integration Settings", [
        select("Backend Framework", options=["fastapi", "django"], value=auto_framework, name="framework"),
        input("OpenAPI URL (Optional if using FastAPI/Django directly)", value="http://localhost:8000/openapi.json", name="url"),
        input("Frontend Output Directory", value=auto_frontend, name="out"),
        select("React Hooks Mode", options=["react_query", "react", "nextjs_actions", "none"], value="react_query", name="hooks")
    ])

    put_html("<hr>")
    
    with put_loading():
        put_text("Analyzing and Generating...")
        
        try:
            config = GeneratorConfig(
                framework=config_data['framework'],
                frontend_dir=config_data['out'],
                openapi_url=config_data['url'],
                hooks_mode=config_data['hooks']
            )
            
            if config.framework == "fastapi":
                config.app_module = "main:app"
            elif config.framework == "django":
                config.django_settings = "myproject.settings"

            raw_schema = extract_schema(config)
            parsed_data = parse_schema(raw_schema, config)
            generate_code(parsed_data, config)
            
            put_success(f"Success! Generated {len(parsed_data['endpoints'])} endpoints to {config_data['out']}")
            
            put_markdown("### Next Steps")
            put_code(f"import {{ useGetUsers }} from '{config_data['out']}/hooks'", "typescript")
            
        except Exception as e:
            put_error(f"Failed to generate: {str(e)}")
            put_text("Make sure your backend server is running if fetching from URL, or your dependencies are installed if extracting locally.")

def get_free_port(start_port=8080):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return start_port

def start_ui():
    port = get_free_port(8080)
    print(f"Starting Web Dashboard on http://localhost:{port}")
    start_server(run_ui, port=port, debug=True)

if __name__ == '__main__':
    start_ui()
