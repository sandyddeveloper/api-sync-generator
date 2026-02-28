import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
from .config import GeneratorConfig

class CodeGenerator:
    def __init__(self, parsed_data: Dict[str, Any], config: GeneratorConfig):
        self.parsed_data = parsed_data
        self.config = config
        self.output_dir = Path(config.frontend_dir) / "api"
        
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def _write_file(self, filename: str, content: str):
        filepath = self.output_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {filepath}")

    def generate_types(self):
        template = self.env.get_template("types.ts.j2")
        content = template.render(interfaces=self.parsed_data["interfaces"].values())
        self._write_file("types.ts", content)

    def generate_api_client(self):
        template = self.env.get_template("api.ts.j2")
        content = template.render(endpoints=self.parsed_data["endpoints"])
        self._write_file("api.ts", content)

    def generate_hooks(self):
        if self.config.hooks_mode in ["react", "react_query"]:
            template = self.env.get_template("hooks.ts.j2")
            content = template.render(endpoints=self.parsed_data["endpoints"], config=self.config)
            self._write_file("hooks.ts", content)
        elif self.config.hooks_mode == "nextjs_actions":
            template = self.env.get_template("server_actions.ts.j2")
            content = template.render(endpoints=self.parsed_data["endpoints"], config=self.config)
            self._write_file("actions.ts", content)

    def generate_docs(self):
        template_integration = self.env.get_template("API_INTEGRATION.md.j2")
        content_int = template_integration.render(endpoints=self.parsed_data["endpoints"])
        self._write_file("API_INTEGRATION.md", content_int)

        template_quickstart = self.env.get_template("QUICKSTART.md.j2")
        content_qs = template_quickstart.render(endpoints=self.parsed_data["endpoints"])
        self._write_file("QUICKSTART.md", content_qs)

    def generate_zod(self):
        template = self.env.get_template("zod.ts.j2")
        content = template.render(interfaces=self.parsed_data["interfaces"].values())
        self._write_file("validations.ts", content)

    def generate(self):
        print(f"Outputting generated files to {self.output_dir}...")
        self.generate_types()
        self.generate_zod()
        self.generate_api_client()
        if self.config.hooks_mode != "none":
            self.generate_hooks()
        self.generate_docs()

def generate_code(parsed_data: Dict[str, Any], config: GeneratorConfig):
    generator = CodeGenerator(parsed_data, config)
    generator.generate()
