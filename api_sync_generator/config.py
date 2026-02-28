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
    openapi_url: Optional[str] = "http://localhost:8000/openapi.json"
    hooks_mode: str = "react_query" # "react", "react_query", "nextjs_actions", "none"
    exclude_tags: List[str] = ["@internal", "@admin_only"]

def load_config(config_path: Optional[str] = None) -> GeneratorConfig:
    path = Path(config_path) if config_path else Path.cwd() / "pyproject.toml"
    
    if not path.exists():
        print("Warning: Config not found, using defaults.")
        return GeneratorConfig()
        
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
        print(f"Error loading config: {e}. Using defaults.")
        
    return GeneratorConfig()

