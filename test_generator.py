import os
from pathlib import Path
from api_sync_generator.config import GeneratorConfig
from api_sync_generator.parser import parse_schema
from api_sync_generator.generator import generate_code

# Mock schema based on test_app
MOCK_SCHEMA = {
    "openapi": "3.0.2",
    "info": {"title": "api-sync-test", "version": "1.0.0"},
    "paths": {
        "/users": {
            "get": {
                "tags": ["users"],
                "summary": "Get Users",
                "description": "Get all users",
                "operationId": "get_users_users_get",
                "parameters": [
                    {
                        "required": False,
                        "schema": {"title": "Active Only", "type": "boolean", "default": False},
                        "name": "active_only",
                        "in": "query"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "title": "Response Get Users Users Get",
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["users"],
                "summary": "Create User",
                "description": "Create a user",
                "operationId": "create_user_users_post",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateUserReq"}
                        }
                    },
                    "required": True
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    }
                }
            }
        },
        "/internal/stats": {
            "get": {
                "tags": ["@internal"],
                "summary": "Internal Stats",
                "description": "This should be ignored by the generator.",
                "operationId": "internal_stats_internal_stats_get",
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {"schema": {"title": "Response Internal Stats", "type": "object"}}
                        }
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "CreateUserReq": {
                "title": "CreateUserReq",
                "required": ["username", "password"],
                "type": "object",
                "properties": {
                    "username": {"title": "Username", "type": "string"},
                    "password": {"title": "Password", "type": "string"}
                }
            },
            "User": {
                "title": "User",
                "required": ["id", "username", "created_at"],
                "type": "object",
                "properties": {
                    "id": {"title": "Id", "type": "integer"},
                    "username": {"title": "Username", "type": "string"},
                    "is_active": {"title": "Is Active", "type": "boolean", "default": True},
                    "created_at": {"title": "Created At", "type": "string", "format": "date-time"}
                }
            }
        }
    }
}

def main():
    config = GeneratorConfig(
        frontend_dir="./frontend_test",
        hooks_mode="react_query"
    )
    
    # 1. Parse
    parsed_data = parse_schema(MOCK_SCHEMA, config)
    print("--- Parsed Data ---")
    print(parsed_data)
    
    # 2. Generate
    generate_code(parsed_data, config)
    print("Done generating.")

if __name__ == "__main__":
    main()
