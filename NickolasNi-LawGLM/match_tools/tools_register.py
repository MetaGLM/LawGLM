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
from config import *
from interface import ToolObservation


ALL_TOOLS = {}

_TOOL_HOOKS = {}
_TOOL_DESCRIPTIONS = {}


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
            "parameters": {"type": "object", "properties": tool_params, "required": required_params},
        },
    }
    # print_log("[registered tool] " + pformat(tool_def))
    _TOOL_HOOKS[tool_name] = func
    _TOOL_DESCRIPTIONS[tool_name] = tool_def

    return func


def dispatch_tool(tool_name: str, code: str, session_id: str) -> list[ToolObservation]:
    print_log("TOOL CALL! ", tool_name, code, session_id)
    # Dispatch predefined tools
    if tool_name in ALL_TOOLS:
        return ALL_TOOLS[tool_name](code, session_id)

    code = code.strip().rstrip("<|observation|>").strip()

    # Dispatch custom tools
    try:
        tool_params = json.loads(code)
    except json.JSONDecodeError as e:
        err = f"Error decoding JSON: {e}"
        print_log("system_error", err)
        return err

    if tool_name not in _TOOL_HOOKS:
        err = f"Tool `{tool_name}` not found. Please use a provided tool."
        print_log("system_error", err)
        return err

    tool_hook = _TOOL_HOOKS[tool_name]

    # for k, v in tool_params.items():
    #     if "Items" in v:
    #         tool_params[k] = v["Items"]
    #     if "items" in v:
    #         tool_params[k] = v["items"]
    print_log("FFFFF", tool_name, tool_params)
    for i in range(3):
        try:
            if type(tool_params) == list:
                ret: str = tool_hook(tool_params)
            elif type(tool_params) == dict:
                ret: str = tool_hook(**tool_params)
            # return [ToolObservation(tool_name, str(ret))]
            # return json.dumps(ret, ensure_ascii=False)
            return ret
        except Exception:
            err = traceback.format_exc()
            print_log("system_error", err)

    return err


def get_tools() -> list[dict]:
    return copy.deepcopy(_TOOL_DESCRIPTIONS)


# if __name__ == "__main__":
#     # print_log(dispatch_tool("get_shell", {"query": "pwd"}))
#     print_log(get_tools())
