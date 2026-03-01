

"""
Function helper module for Gemini Live API.

This module provides utilities for creating function declarations from Python files
and calling those functions dynamically. It depends on the google-genai library.
"""

import importlib.util
import inspect
from typing import Any, Dict, List, Tuple, Optional


def create_function_declarations_from_file(filename: str) -> Tuple[List[Dict], Any]:
    """
    Load a Python file and create function declarations for Gemini API.
    
    Args:
        filename: Path to the Python file containing function definitions.
        
    Returns:
        A tuple of (function_declarations, module) where function_declarations
        is a list of dicts suitable for the Gemini API, and module is the
        loaded Python module.
    """
    # Load the module from file
    spec = importlib.util.spec_from_file_location("imported_functions", filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {filename}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get all functions from the module
    functions = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and not name.startswith("_"):
            func_declaration = _create_function_declaration(obj)
            if func_declaration:
                functions.append(func_declaration)
    
    return functions, module


def _create_function_declaration(func: callable) -> Optional[Dict]:
    """
    Create a function declaration dict for a given function.
    
    Args:
        func: The function to create a declaration for.
        
    Returns:
        A dict representing the function declaration for Gemini API.
    """
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or ""
    
    # Parse parameters
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for param_name, param in sig.parameters.items():
        param_info = {"type": _get_json_type(param.annotation)}
        
        # Get parameter description from docstring if available
        param_desc = _extract_param_description(doc, param_name)
        if param_desc:
            param_info["description"] = param_desc
        
        parameters["properties"][param_name] = param_info
        
        # Mark as required if no default value
        if param.default is inspect.Parameter.empty:
            parameters["required"].append(param_name)
    
    return {
        "name": func.__name__,
        "description": doc.split("\n")[0] if doc else f"Function {func.__name__}",
        "parameters": parameters
    }


def _get_json_type(annotation: Any) -> str:
    """
    Convert Python type annotation to JSON schema type.
    
    Args:
        annotation: Python type annotation.
        
    Returns:
        JSON schema type string.
    """
    if annotation is inspect.Parameter.empty:
        return "string"
    
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }
    
    # Handle typing module types
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        if origin is list:
            return "array"
        if origin is dict:
            return "object"
    
    return type_map.get(annotation, "string")


def _extract_param_description(docstring: str, param_name: str) -> Optional[str]:
    """
    Extract parameter description from docstring.
    
    Supports Google-style and NumPy-style docstrings.
    
    Args:
        docstring: The function's docstring.
        param_name: The parameter name to find description for.
        
    Returns:
        The parameter description or None if not found.
    """
    if not docstring:
        return None
    
    lines = docstring.split("\n")
    in_args_section = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check for Args: section (Google-style)
        if stripped.lower() in ("args:", "arguments:", "parameters:"):
            in_args_section = True
            continue
        
        # Check for end of Args section
        if in_args_section and stripped and not stripped.startswith(param_name[0] if param_name else ""):
            if ":" in stripped and not stripped.startswith(" "):
                break
        
        # Look for parameter description
        if in_args_section:
            # Google-style: "param_name: description"
            if stripped.startswith(f"{param_name}:"):
                return stripped[len(param_name) + 1:].strip()
            # Google-style: "param_name (type): description"
            if stripped.startswith(f"{param_name} ("):
                parts = stripped.split(":", 1)
                if len(parts) > 1:
                    return parts[1].strip()
    
    return None


async def call_function(module: Any, function_name: str, **kwargs) -> Dict[str, Any]:
    """
    Call a function from a module with the given arguments.
    
    Args:
        module: The Python module containing the function.
        function_name: Name of the function to call.
        **kwargs: Arguments to pass to the function.
        
    Returns:
        A dict containing the function result or error.
    """
    func = getattr(module, function_name, None)
    
    if func is None:
        return {"error": f"Function '{function_name}' not found in module"}
    
    try:
        # Check if function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            result = await func(**kwargs)
        else:
            result = func(**kwargs)
        
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}
