import argparse
import sys
import os
from pathlib import Path
from .config import load_config, GeneratorConfig
from .extractor import extract_schema
from .parser import parse_schema
from .generator import generate_code
from .watcher import start_watcher

def run_init_wizard():
    print("Welcome to the api-sync-generator setup wizard! 🚀")
    print("Let's configure your frontend API integration in 3 quick steps.\n")
    
    framework = input("1. Which backend framework are you using? [fastapi/django] (default: fastapi): ").strip().lower() or "fastapi"
    if framework not in ["fastapi", "django"]:
        print("Invalid framework. Defaulting to fastapi.")
        framework = "fastapi"
        
    frontend_dir = input("2. Where should we generate the TypeScript files? (default: ./frontend/src/api): ").strip() or "./frontend/src/api"
    
    hooks_opt = input("3. Which hooks style do you prefer? [react/react_query/none] (default: react_query): ").strip().lower() or "react_query"
    if hooks_opt not in ["react", "react_query", "nextjs_actions", "none"]:
        hooks_opt = "react_query"
        
    toml_path = Path.cwd() / "pyproject.toml"
    
    config_str = f"""
[tool.api-sync]
framework = "{framework}"
frontend_dir = "{frontend_dir}"
hooks_mode = "{hooks_opt}"
"""
    
    if framework == "fastapi":
        config_str += 'app_module = "main:app"\n'
    elif framework == "django":
        config_str += 'django_settings = "myproject.settings"\n'

    if not toml_path.exists():
        print(f"\nCreating new {toml_path}...")
        with open(toml_path, "w") as f:
            f.write(config_str)
    else:
        print(f"\nAppending configuration to existing {toml_path}...")
        with open(toml_path, "a") as f:
            f.write("\n" + config_str)
            
    print("\n✅ Setup complete! You can now run `api-sync` to generate your frontend code.")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Generate TypeScript interfaces, Zod validations, and React hooks from an OpenAPI schema."
    )
    
    # Init Wizard Command
    parser.add_argument("command", nargs="?", help="Command to run (e.g. 'init')")
    
    # Core execution flags
    parser.add_argument("--watch", action="store_true", help="Run in continuous watch mode.")
    parser.add_argument("--config", type=str, help="Path to a specific config file (default: pyproject.toml).")
    
    # Dynamic Overrides
    parser.add_argument("--url", type=str, help="Dynamic fallback: Fetch OpenAPI schema directly from a URL (e.g., http://localhost:8000/openapi.json)")
    parser.add_argument("--framework", type=str, choices=["fastapi", "django"], help="Override backend framework.")
    parser.add_argument("--out", type=str, help="Override frontend output directory.")
    parser.add_argument("--hooks", type=str, choices=["react", "react_query", "nextjs_actions", "none"], help="Override hook generation mode.")
    
    args = parser.parse_args()
    
    if args.command == "init":
        run_init_wizard()
    
    print("Loading config...")
    config = load_config(args.config)
    
    # Apply Dynamic Overrides
    if args.url:
        config.openapi_url = args.url
    if args.framework:
        config.framework = args.framework
    if args.out:
        config.frontend_dir = args.out
    if args.hooks:
        config.hooks_mode = args.hooks
    
    print(f"Loaded config: {config}")
    
    if args.watch:
        start_watcher(config)
    else:
        # execute generation pipeline once
        try:
            schema = extract_schema(config)
            parsed_data = parse_schema(schema, config)
            generate_code(parsed_data, config)
        except Exception as e:
            print(f"Error during generation: {e}")
            sys.exit(1)
    
    print("Generation complete.")

if __name__ == "__main__":
    main()
