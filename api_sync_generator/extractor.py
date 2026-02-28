import requests
import importlib
import sys
import os
from pydantic import BaseModel
from typing import Any, Dict
from .config import GeneratorConfig

class SchemaExtractor:
    def __init__(self, config: GeneratorConfig):
        self.config = config

    def extract(self) -> Dict[str, Any]:
        """
        Extract the OpenAPI schema based on the configured framework or URL.
        """
        if self.config.openapi_url and self.config.openapi_url.startswith("http"):
            urls_to_try = [self.config.openapi_url]
            
            # Smart URL fallbacks
            if not self.config.openapi_url.endswith(".json"):
                base = self.config.openapi_url.rstrip("/")
                urls_to_try.extend([f"{base}/openapi.json", f"{base}/api/schema/"])
                
            for url in urls_to_try:
                try:
                    print(f"Fetching schema from {url}...")
                    response = requests.get(url, timeout=5)
                    response.raise_for_status()
                    
                    # Ensure it's actually JSON and looks like openapi
                    data = response.json()
                    if "openapi" in data or "swagger" in data:
                        return data
                except (requests.exceptions.RequestException, ValueError) as e:
                    print(f" -> Failed parsing {url}")
            
            print("Falling back to framework hook extraction...")

        if self.config.framework == "fastapi":
            return self._extract_fastapi()
        elif self.config.framework == "django":
            return self._extract_django()
        else:
            raise ValueError(f"Unsupported framework: {self.config.framework}")

    def _extract_fastapi(self) -> Dict[str, Any]:
        """
        Dynamically import the FastAPI app and call .openapi()
        """
        if not self.config.app_module:
            raise ValueError("app_module config is required for fastapi extraction (e.g. main:app)")
        
        module_name, app_name = self.config.app_module.split(":")
        
        # Add current working directory to path to allow dynamic import
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
            
        try:
            print(f"Loading FastAPI app from {module_name}:{app_name}...")
            module = importlib.import_module(module_name)
            app = getattr(module, app_name)
            from fastapi.openapi.utils import get_openapi
            
            # app.openapi() generates it, but we can just use the internal app logic
            if not app.openapi_schema:
                app.openapi_schema = get_openapi(
                    title=app.title,
                    version=app.version,
                    openapi_version=app.openapi_version,
                    description=app.description,
                    routes=app.routes,
                )
            return app.openapi_schema
        except Exception as e:
            raise RuntimeError(f"Failed to extract FastAPI schema: {e}")

    def _extract_django(self) -> Dict[str, Any]:
        """
        Django schema extraction. Can hook into drf-spectacular or ninja.
        """
        if not self.config.django_settings:
            raise ValueError("django_settings config is required for django extraction")
        
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", self.config.django_settings)
        
        cwd = os.getcwd()
        if cwd not in sys.path:
            sys.path.insert(0, cwd)
            
        from django.core.wsgi import get_wsgi_application
        application = get_wsgi_application() # Initialize django
        
        print("Checking for drf-spectacular...")
        try:
            from drf_spectacular.generators import SchemaGenerator
            generator = SchemaGenerator()
            schema = generator.get_schema()
            from drf_spectacular.renderers import OpenApiJsonRenderer
            # Get plain dict
            from drf_spectacular.plumbing import build_basic_type, build_array_type, build_object_type
            import json
            renderer = OpenApiJsonRenderer()
            json_bytes = renderer.render(schema, generator.info)
            return json.loads(json_bytes.decode('utf-8'))
            
        except ImportError:
            pass
            
        print("Checking for Django Ninja...")
        try:
            # Ninja is a bit trickier because the api instance needs to be imported
            print("Django Ninja schema extraction requires standard URL fetching currently.")
            raise NotImplementedError("Direct ninja import not yet implemented, provide openapi_url instead.")
        except ImportError:
            pass
            
        raise RuntimeError("No supported Django schema generator found. Install drf-spectacular.")

def extract_schema(config: GeneratorConfig) -> Dict[str, Any]:
    extractor = SchemaExtractor(config)
    return extractor.extract()
