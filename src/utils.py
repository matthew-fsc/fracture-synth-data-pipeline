"""
Utility functions for the synthetic data pipeline.

Common utilities used across modules.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_json_load(file_path: Path, default: Any = None) -> Any:
    """
    Safely load JSON file with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data or default
    """
    try:
        if not file_path.exists():
            return default
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load JSON from {file_path}: {e}")
        return default


def safe_json_save(data: Any, file_path: Path, indent: int = 2) -> bool:
    """
    Safely save data to JSON file with error handling.
    
    Args:
        data: Data to save
        file_path: Path to JSON file
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save JSON to {file_path}: {e}")
        return False


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary (base)
        dict2: Second dictionary (updates)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def format_datetime(dt: datetime) -> str:
    """
    Format datetime to ISO string.
    
    Args:
        dt: Datetime object
        
    Returns:
        ISO formatted string
    """
    return dt.isoformat() if dt else ""


def calculate_percentage(value: float, total: float) -> float:
    """
    Calculate percentage safely.
    
    Args:
        value: Value
        total: Total
        
    Returns:
        Percentage (0-100) or 0.0 if total is 0
    """
    if total == 0:
        return 0.0
    return (value / total) * 100.0


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(value, max_val))


def get_nested_dict_value(data: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get nested dictionary value using dot notation.
    
    Args:
        data: Dictionary
        key_path: Dot-separated key path (e.g., "a.b.c")
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def set_nested_dict_value(data: Dict[str, Any], key_path: str, value: Any) -> bool:
    """
    Set nested dictionary value using dot notation.
    
    Args:
        data: Dictionary to update
        key_path: Dot-separated key path (e.g., "a.b.c")
        value: Value to set
        
    Returns:
        True if successful, False otherwise
    """
    keys = key_path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        elif not isinstance(current[key], dict):
            return False
        current = current[key]
    
    current[keys[-1]] = value
    return True

