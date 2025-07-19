"""
AI Fabric Shell - Local AI automation with Rich UI, plugin system, and model switching
"""

__version__ = "2.0.0"
__author__ = "AI Fabric Shell"

# Core imports for easy access
from .core.shell import AIFabricShell
from .models.manager import ModelManager
from .plugins.manager import PluginManager
from .rendering.renderer import ResponseRenderer
from .core.system_info import SystemInfo

__all__ = [
    'AIFabricShell',
    'ModelManager', 
    'PluginManager',
    'ResponseRenderer',
    'SystemInfo'
]