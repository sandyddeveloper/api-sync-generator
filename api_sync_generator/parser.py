import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from .config import GeneratorConfig

class ParsedProperty(BaseModel):
    ts_type: str
    description: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    optional: bool = False

class ParsedInterface(BaseModel):
    name: str
    properties: Dict[str, ParsedProperty] # e.g. {"username": ParsedProperty(...)}
    is_enum: bool = False
    enum_values: List[str] = []
    description: Optional[str] = None

class ParsedParam(BaseModel):
    name: str
    type: str
    description: Optional[str] = None

class ParsedEndpoint(BaseModel):
    path: str
    method: str
    operation_id: str
    summary: Optional[str] = None
    description: Optional[str] = None
    url_params: List[ParsedParam]
    query_params: List[ParsedParam]
    request_body_type: Optional[str] = None
    response_body_type: Optional[str] = None
    is_array_response: bool = False
    
class SchemaParser:
    def __init__(self, raw_schema: Dict[str, Any], config: GeneratorConfig):
        self.schema = raw_schema
        self.config = config
        self.interfaces: Dict[str, ParsedInterface] = {}
        self.endpoints: List[ParsedEndpoint] = []
        
    def _translate_type(self, schema_prop: Dict[str, Any]) -> str:
        """Translates OpenAPI types to TypeScript types"""
        # Handle $ref
        if "$ref" in schema_prop:
            ref = schema_prop["$ref"]
            return ref.split("/")[-1]
            
        prop_type = schema_prop.get("type", "any")
        
        if prop_type == "string":
            if schema_prop.get("format") in ["date", "date-time"]:
                return "string" # ISO dates are strings in JSON
            return "string"
        elif prop_type == "integer" or prop_type == "number":
            return "number"
        elif prop_type == "boolean":
            return "boolean"
        elif prop_type == "array":
            items = schema_prop.get("items", {})
            return f"{self._translate_type(items)}[]"
        elif prop_type == "object":
            if "additionalProperties" in schema_prop:
                val_type = self._translate_type(schema_prop["additionalProperties"])
                return f"{{ [key: string]: {val_type} }}"
            return "any"
        
        # Handle AnyOf/AllOf/OneOf rudimentary cases
        if "anyOf" in schema_prop:
            types = [self._translate_type(t) for t in schema_prop["anyOf"] if t.get("type") != "null"]
            # Handle optionals
            if len(types) == 1:
                return types[0] # Often anyOf: [{type: 'string'}, {type: 'null'}] -> Optional
            return " | ".join(set(types))
            
        return "any"
        
    def parse_components(self):
        """Parse OpenAPI components/schemas into TS Interfaces"""
        schemas = self.schema.get("components", {}).get("schemas", {})
        
        for name, spec in schemas.items():
            description = spec.get("description") or spec.get("title")
            
            if "enum" in spec:
                self.interfaces[name] = ParsedInterface(
                    name=name,
                    properties={},
                    is_enum=True,
                    enum_values=[f"'{v}'" if isinstance(v, str) else str(v) for v in spec["enum"]],
                    description=description
                )
                continue
                
            properties = {}
            for prop_name, prop_spec in spec.get("properties", {}).items():
                ts_type = self._translate_type(prop_spec)
                prop_desc = prop_spec.get("description") or prop_spec.get("title")
                
                # Check required
                required = spec.get("required", [])
                optional = prop_name not in required
                if optional:
                    prop_name = f"{prop_name}?"
                    
                properties[prop_name] = ParsedProperty(
                    ts_type=ts_type, 
                    description=prop_desc,
                    min_length=prop_spec.get("minLength"),
                    max_length=prop_spec.get("maxLength"),
                    pattern=prop_spec.get("pattern"),
                    minimum=prop_spec.get("minimum"),
                    maximum=prop_spec.get("maximum"),
                    optional=optional
                )
                
            self.interfaces[name] = ParsedInterface(
                name=name,
                properties=properties,
                description=description
            )
            
    def parse_paths(self):
        """Parse OpenAPI paths into Endpoints"""
        paths = self.schema.get("paths", {})
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.lower() not in ["get", "post", "put", "patch", "delete"]:
                    continue
                    
                # Intelligent string replacements for TS
                tags = operation.get("tags", [])
                if any(t in self.config.exclude_tags for t in tags):
                    continue
                    
                desc = operation.get("description", "")
                if any(t in desc for t in self.config.exclude_tags):
                    continue

                operation_id = operation.get("operationId", f"{method}_{path.replace('/', '_')}")
                # Clean operation_id (FastAPI sometimes adds suffix)
                operation_id = re.sub(r'[^a-zA-Z0-9_]', '', operation_id)
                # camelCase it roughly
                parts = operation_id.split('_')
                operation_id = parts[0] + ''.join(p.capitalize() for p in parts[1:])

                summary = operation.get("summary")
                description = operation.get("description")

                url_params = []
                query_params = []
                
                for param in operation.get("parameters", []):
                    ptype = self._translate_type(param.get("schema", {}))
                    param_desc = param.get("description")
                    if param.get("in") == "path":
                        url_params.append(ParsedParam(name=param["name"], type=ptype, description=param_desc))
                    elif param.get("in") == "query":
                        qname = param["name"]
                        if not param.get("required", False):
                            qname = f"{qname}?"
                        query_params.append(ParsedParam(name=qname, type=ptype, description=param_desc))
                        
                req_body_type = None
                req_body = operation.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {})
                if req_body:
                    req_body_type = self._translate_type(req_body)
                    
                res_body_type = None
                is_array = False
                res_content = operation.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {})
                if res_content:
                    res_schema = res_content.get("schema", {})
                    if res_schema.get("type", "") == "array":
                        is_array = True
                        # we get the inner type and will wrap it later
                    # Even if array, translate type gives us Type[] 
                    res_body_type = self._translate_type(res_schema)

                
                self.endpoints.append(ParsedEndpoint(
                    path=path,
                    method=method.upper(),
                    operation_id=operation_id,
                    summary=summary,
                    description=description,
                    url_params=url_params,
                    query_params=query_params,
                    request_body_type=req_body_type,
                    response_body_type=res_body_type,
                    is_array_response=is_array
                ))

    def parse(self) -> Dict[str, Any]:
        self.parse_components()
        self.parse_paths()
        
        return {
            "interfaces": self.interfaces,
            "endpoints": self.endpoints
        }

def parse_schema(schema: Dict[str, Any], config: GeneratorConfig) -> Dict[str, Any]:
    parser = SchemaParser(schema, config)
    return parser.parse()
