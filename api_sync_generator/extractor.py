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
        Extract the OpenAPI schema based on the configured framework or URL or cURL string.
        """
        if self.config.curl_command:
            try:
                return self._extract_from_curl(self.config.curl_command)
            except Exception as e:
                print(f"Failed to fetch schema from cURL: {e}")
                print("Falling back to URL/framework hook...")
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
            
    def _extract_from_curl(self, curl_str: str) -> Dict[str, Any]:
        """
        Parse a raw full cURL command string into a python requests call.
        """
        import shlex
        
        args = shlex.split(curl_str)
        if args[0] != "curl":
            raise ValueError("String must start with 'curl'")
            
        url = None
        headers = {}
        method = "GET"
        data = None
        
        i = 1
        while i < len(args):
            arg = args[i]
            if arg in ("-H", "--header"):
                i += 1
                header = args[i]
                if ":" in header:
                    key, val = header.split(":", 1)
                    headers[key.strip()] = val.strip()
            elif arg in ("-X", "--request"):
                i += 1
                method = args[i].upper()
            elif arg in ("-d", "--data", "--data-raw"):
                i += 1
                data = args[i]
                if method == "GET":
                    method = "POST"
            elif not arg.startswith("-"):
                # Usually the URL is the only non-flag argument
                url = arg
            i += 1
            
        if not url:
            raise ValueError("Could not extract URL from cURL string")
            
        print(f"Executing extracted cURL request against {url}...")
        response = requests.request(method, url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json()

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
