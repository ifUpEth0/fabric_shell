"""
Plugin management system for loading and executing YAML-based plugins
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

console = Console()

class PluginManager:
    """Manages loading and execution of AI automation plugins"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        """
        Initialize the PluginManager with an optional directory path
        for finding and loading plugins. The default directory is 'plugins'.
        The directory is created if it does not already exist.
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.plugins = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all YAML plugin files"""
        for plugin_file in self.plugins_dir.glob("*.y*ml"):
            try:
                with open(plugin_file, 'r') as f:
                    plugin_data = yaml.safe_load(f)
                    self.plugins[plugin_file.stem] = plugin_data
                console.print(f"[green]✓[/green] Loaded plugin: {plugin_file.stem}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to load {plugin_file}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plugin configuration by name"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """Get list of all available plugin names"""
        return list(self.plugins.keys())
    
    def get_plugin_info(self, name: str) -> Dict[str, Any]:
        """Get detailed plugin information"""
        plugin = self.get_plugin(name)
        if not plugin:
            return {}
        return {
            'name': name,
            'description': plugin.get('description', 'No description'),
            'category': plugin.get('category', 'general'),
            'parameters': plugin.get('parameters', {}),
            'examples': plugin.get('examples', []),
            'preferred_model': plugin.get('preferred_model', None),
            'model_category': plugin.get('model_category', None)
        }
    
    def get_plugins_by_category(self) -> Dict[str, List[str]]:
        """Group plugins by category"""
        categories = {}
        for name, plugin in self.plugins.items():
            category = plugin.get('category', 'general')
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        return categories
    
    def reload_plugins(self):
        """Reload all plugins from disk"""
        self.plugins.clear()
        self._load_plugins()
        console.print(f"[green]Reloaded {len(self.plugins)} plugins[/green]")
    
    def validate_plugin(self, plugin_data: Dict[str, Any]) -> bool:
        """Validate plugin configuration"""
        required_fields = ['prompt']
        for field in required_fields:
            if field not in plugin_data:
                return False
        return True