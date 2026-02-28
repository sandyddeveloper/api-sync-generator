import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, List

# Basic Config Model
class GeneratorConfig(BaseModel):
    frontend_dir: str = "./frontend"
    framework: str = "fastapi"  # "fastapi" or "django"
    app_module: Optional[str] = "main:app" # Example: myapp.main:app
    django_settings: Optional[str] = None # Example: myproject.settings
    openapi_url: Optional[str] = None
    curl_command: Optional[str] = None
    hooks_mode: str = "react_query" # "react", "react_query", "nextjs_actions", "none"
    exclude_tags: List[str] = ["@internal", "@admin_only"]

def auto_discover_config() -> GeneratorConfig:
    config = GeneratorConfig()
    
    # Auto-detect framework
    if os.path.exists("manage.py"):
        config.framework = "django"
        config.django_settings = "myproject.settings" # best guess, requires DRF
        print("🔍 Auto-discovered Django backend.")
    elif os.path.exists("main.py"):
        config.framework = "fastapi"
        config.app_module = "main:app"
        print("🔍 Auto-discovered FastAPI backend.")
    else:
        # Default fallback
        config.framework = "fastapi"
        config.app_module = "main:app"

    # Auto-detect frontend directory
    for root, dirs, files in os.walk("."):
        if "node_modules" in dirs:
            dirs.remove("node_modules") # don't recurse here
        if "venv" in dirs:
            dirs.remove("venv")
        if "env" in dirs:
            dirs.remove("env")
            
        if "package.json" in files:
            if "src" in dirs:
                auto_dir = os.path.join(root, "src", "api")
            else:
                auto_dir = os.path.join(root, "api")
            config.frontend_dir = auto_dir
            print(f"🔍 Auto-discovered Frontend directory: {auto_dir}")
            break
            
    return config

def load_config(config_path: Optional[str] = None) -> GeneratorConfig:
    path = Path(config_path) if config_path else Path.cwd() / "pyproject.toml"
    
    if not path.exists():
        print("Warning: Config not found, attempting auto-discovery...")
        return auto_discover_config()
        
    try:
        if path.suffix == ".toml":
            # For Python >= 3.11, tomllib is in stdlib
            try:
                import tomllib
                with open(path, "rb") as f:
                    data = tomllib.load(f)
            except ImportError:
                try:
                    import tomli
                    with open(path, "rb") as f:
                        data = tomli.load(f)
                except ImportError:
                    print("Warning: neither tomllib nor tomli is installed. Cannot parse pyproject.toml.")
                    return GeneratorConfig()
            
            tool_ts_sync = data.get("tool", {}).get("api-sync", {})
            return GeneratorConfig(**tool_ts_sync)
    except Exception as e:
        print(f"Error loading config: {e}. Attempting auto-discovery...")
        
    return auto_discover_config()

