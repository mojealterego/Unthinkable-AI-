"""API wrapper/OpenAPI generator from manually declared, owned API operations.

No external API is queried. The output is a reusable contract, not a proxy
or a claim that the upstream backend has been discovered or migrated.
"""
from __future__ import annotations

import re
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class ApiOperation(BaseModel):
    operation_id: str = Field(min_length=2, max_length=70, pattern=r"^[a-z][a-z0-9_]*$")
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    path: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=240)
    request_fields: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def check_path(self):
        if not re.fullmatch(r"/(?:[a-zA-Z0-9_-]+/?){1,15}", self.path) or "//" in self.path:
            raise ValueError("Use simple documented API paths, not URLs or arbitrary templates")
        if len(set(self.request_fields)) != len(self.request_fields) or any(
            not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", f) for f in self.request_fields
        ):
            raise ValueError("Invalid or duplicate request fields")
        if self.method == "GET" and self.request_fields:
            raise ValueError("GET operations cannot have JSON request bodies")
        return self


class WrapperDesign(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    version: str = Field(default="1.0.0", pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    operations: list[ApiOperation] = Field(min_length=1, max_length=60)

    @model_validator(mode="after")
    def unique_routes(self):
        endpoints = [(o.path, o.method) for o in self.operations]
        if len(endpoints) != len(set(endpoints)):
            raise ValueError("Duplicate API path and HTTP method")
        if len({o.operation_id for o in self.operations}) != len(self.operations):
            raise ValueError("Duplicate operation IDs")
        return self


def build_openapi(spec: WrapperDesign) -> dict:
    paths: dict = {}
    for op in spec.operations:
        request_body = None
        if op.request_fields:
            request_body = {
                "required": True,
                "content": {"application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {name: {"type": "string", "maxLength": 4000}
                                       for name in op.request_fields},
                        "additionalProperties": False,
                    },
                }},
            }
        paths.setdefault(op.path, {})[op.method.lower()] = {
            "operationId": op.operation_id,
            "summary": op.summary,
            "responses": {"200": {"description": "Response from the owned API, implementation required"}},
            **({"requestBody": request_body} if request_body else {}),
        }
    return {
        "openapi": "3.1.0",
        "info": {"title": spec.title, "version": spec.version,
                 "description": "NoCode contract only; underlying API not automatically deployed"},
        "paths": paths,
        "x-unthinkable-capabilities": {
            "contract_generated": True, "backend_connected": False,
            "credentials_extracted": False, "proxy_started": False,
        },
    }
