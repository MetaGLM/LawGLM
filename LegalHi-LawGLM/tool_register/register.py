"""
This code is the tool registration part. By registering the tool, the model can call the tool.
This code provides extended functionality to the model, enabling it to call and interact with a variety of utilities
through defined interfaces.
"""

from collections.abc import Callable
import copy
import inspect
import json
from pprint import pformat
import traceback
from types import GenericAlias
from typing import get_origin, Annotated
import subprocess
import requests
from enum import Enum

from tool_register.interface import ToolObservation

ALL_TOOLS = {}

_TOOL_HOOKS = {}
_TOOL_DESCRIPTIONS = []


def register_tool_one(func: Callable):
    tool_name = func.__name__
    tool_description = inspect.getdoc(func).strip()
    python_params = inspect.signature(func).parameters
    tool_params = {}
    required_params = []
    for name, param in python_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{name}` missing type annotation")
        if get_origin(annotation) != Annotated:
            raise TypeError(f"Annotation type for `{name}` must be typing.Annotated")

        typo, (description, required) = annotation.__origin__, annotation.__metadata__
        typ: str = str(typo) if isinstance(typo, GenericAlias) else typo.__name__
        if not isinstance(description, str):
            raise TypeError(f"Description for `{name}` must be a string")
        if not isinstance(required, bool):
            raise TypeError(f"Required for `{name}` must be a bool")

        tool_params[name] = {
            "description": description,
            "type": typ,
        }

        if required:
            required_params.append(name)

        try:
            if issubclass(typo, Enum):
                tool_params[name]["enum"] = [e.value for e in typo]
        except Exception as e:
            pass

    tool_def = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": {
                "type": "object",
                "properties": tool_params,
                "required": required_params,
            },
        },
    }
    # print("[registered tool] " + pformat(tool_def))

    return tool_def


def register_tool(func: Callable):
    tool_name = func.__name__
    tool_description = inspect.getdoc(func).strip()
    python_params = inspect.signature(func).parameters
    tool_params = {}
    required_params = []
    for name, param in python_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{name}` missing type annotation")
        if get_origin(annotation) != Annotated:
            raise TypeError(f"Annotation type for `{name}` must be typing.Annotated")

        typo, (description, required) = annotation.__origin__, annotation.__metadata__
        typ: str = str(typo) if isinstance(typo, GenericAlias) else typo.__name__
        if not isinstance(description, str):
            raise TypeError(f"Description for `{name}` must be a string")
        if not isinstance(required, bool):
            raise TypeError(f"Required for `{name}` must be a bool")

        tool_params[name] = {
            "description": description,
            "type": typ,
        }

        if required:
            required_params.append(name)

        try:
            if issubclass(typo, Enum):
                tool_params[name]["enum"] = [e.value for e in typo]
        except Exception as e:
            pass

    tool_def = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description,
            "parameters": {
                "type": "object",
                "properties": tool_params,
                "required": required_params,
            },
        },
    }
    # print("[registered tool] " + pformat(tool_def))
    _TOOL_HOOKS[tool_name] = func
    _TOOL_DESCRIPTIONS.append(tool_def)

    return func


def get_tools() -> list[dict]:
    return copy.deepcopy(_TOOL_DESCRIPTIONS)


if __name__ == "__main__":
    print(get_tools())
