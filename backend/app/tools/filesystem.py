import os
import shutil

from langchain_core.tools import tool

from app.core.config import get_settings

settings = get_settings()
WORKSPACE = os.path.abspath(settings.AGENT_WORKSPACE_PATH)

# Ensure workspace exists
os.makedirs(WORKSPACE, exist_ok=True)

def _get_safe_path(path: str) -> str:
    """Helper to ensure the path is within the workspace."""
    safe_path = os.path.abspath(os.path.join(WORKSPACE, path))
    if not safe_path.startswith(WORKSPACE):
        raise ValueError(f"Access denied: {path} is outside the workspace.")
    return safe_path

@tool
def list_files(directory: str = ".") -> list[str]:
    """Lists files in a given directory within the workspace."""
    safe_dir = _get_safe_path(directory)
    return os.listdir(safe_dir)

@tool
def read_file(filename: str) -> str:
    """Reads the content of a file within the workspace."""
    safe_file = _get_safe_path(filename)
    with open(safe_file, encoding="utf-8") as f:
        return f.read()

@tool
def write_file(filename: str, content: str):
    """Writes content to a file within the workspace. Overwrites if exists."""
    safe_file = _get_safe_path(filename)
    os.makedirs(os.path.dirname(safe_file), exist_ok=True)
    with open(safe_file, "w", encoding="utf-8") as f:
        f.write(content)

@tool
def delete_file(filename: str):
    """Deletes a file from the workspace."""
    safe_file = _get_safe_path(filename)
    if os.path.isfile(safe_file):
        os.remove(safe_file)
    elif os.path.isdir(safe_file):
        shutil.rmtree(safe_file)
