"""
AI Model management with capability analysis and recommendations
"""

import re
import ollama
from typing import List, Dict, Any, Tuple
from rich.console import Console
from rich.table import Table

console = Console()

class ModelManager:
    """Manages AI model selection and switching"""
    
    def __init__(self):
        self.current_model = "llama3.1"  # Default model
        self.available_models = []
        self.model_info = {}
        self._detect_models()
    
    def _detect_models(self):
        """Detect available Ollama models and their capabilities"""
        try:
            models_response = ollama.list()
            self.available_models = self._extract_models(models_response)
            self._analyze_model_capabilities()
        except Exception as e:
            console.print(f"[red]Error detecting models: {e}[/red]")
    
    def _extract_models(self, models_response) -> List[str]:
        """Extract model names from various response formats"""
        if isinstance(models_response, dict):
            models_list = models_response.get('models', [])
        elif hasattr(models_response, 'models'):
            models_list = models_response.models
        else:
            models_list = models_response
        
        models = []
        for model in models_list:
            if hasattr(model, 'model'):
                models.append(model.model)
            elif isinstance(model, dict):
                name = model.get('name') or model.get('model') or model.get('id')
                if name:
                    models.append(name)
            elif isinstance(model, str):
                models.append(model)
        return models
    
    def _analyze_model_capabilities(self):
        """Analyze and categorize model capabilities"""
        model_profiles = {
            # Code-focused models
            'codellama': {
                'category': 'code',
                'description': 'Specialized for code generation and analysis',
                'strengths': ['Programming', 'Code review', 'Debugging', 'Script generation'],
                'best_for': ['code_review', 'script_generator', 'docker_helper'],
                'size': 'Large',
                'speed': 'Medium'
            },
            'codegemma': {
                'category': 'code',
                'description': 'Google\'s code-focused model',
                'strengths': ['Code completion', 'Refactoring', 'Documentation'],
                'best_for': ['code_review', 'script_generator'],
                'size': 'Medium',
                'speed': 'Fast'
            },
            
            # General purpose models
            'llama3.1': {
                'category': 'general',
                'description': 'Balanced model for general tasks',
                'strengths': ['General knowledge', 'Problem solving', 'Command generation'],
                'best_for': ['cmd_generator', 'troubleshooter', 'quick_command'],
                'size': 'Large',
                'speed': 'Medium'
            },
            'llama3.2': {
                'category': 'general',
                'description': 'Latest Llama model with improved capabilities',
                'strengths': ['Reasoning', 'Analysis', 'System administration'],
                'best_for': ['troubleshooter', 'security_audit', 'performance_optimizer'],
                'size': 'Large',
                'speed': 'Medium'
            },
            'mistral': {
                'category': 'general',
                'description': 'Fast and efficient general-purpose model',
                'strengths': ['Quick responses', 'System commands', 'Basic troubleshooting'],
                'best_for': ['cmd_generator', 'quick_command', 'file_operations'],
                'size': 'Medium',
                'speed': 'Fast'
            },
            'mixtral': {
                'category': 'analysis',
                'description': 'Mixture of experts model for complex reasoning',
                'strengths': ['Complex analysis', 'Multi-step reasoning', 'Performance optimization'],
                'best_for': ['performance_optimizer', 'security_audit', 'log_analyzer'],
                'size': 'Large',
                'speed': 'Slow'
            },
            
            # Specialized models
            'phi3': {
                'category': 'lightweight',
                'description': 'Small, efficient model for quick tasks',
                'strengths': ['Speed', 'Low resource usage', 'Simple commands'],
                'best_for': ['quick_command', 'file_operations'],
                'size': 'Small',
                'speed': 'Very Fast'
            },
            'gemma': {
                'category': 'general',
                'description': 'Google\'s efficient general model',
                'strengths': ['Balanced performance', 'Good reasoning'],
                'best_for': ['troubleshooter', 'deployment_planner'],
                'size': 'Medium',
                'speed': 'Fast'
            }
        }
        
        # Populate model info for available models
        for model in self.available_models:
            # Extract base model name (remove version suffixes)
            base_name = re.split(r'[:.-]', model.lower())[0]
            
            # Find matching profile
            profile = None
            for profile_name, profile_data in model_profiles.items():
                if profile_name in model.lower() or base_name == profile_name:
                    profile = profile_data.copy()
                    break
            
            # Default profile for unknown models
            if not profile:
                profile = {
                    'category': 'unknown',
                    'description': 'Unknown model capabilities',
                    'strengths': ['General tasks'],
                    'best_for': [],
                    'size': 'Unknown',
                    'speed': 'Unknown'
                }
            
            self.model_info[model] = profile
    
    def get_best_model_for_plugin(self, plugin_name: str) -> str:
        """Get the best available model for a specific plugin"""
        # Check if plugin has a preferred model that's available
        for model, info in self.model_info.items():
            if plugin_name in info.get('best_for', []):
                return model
        
        # Fallback to current model
        return self.current_model
    
    def switch_model(self, model_name: str) -> bool:
        """Switch to a different model"""
        if model_name not in self.available_models:
            console.print(f"[red]Model '{model_name}' not available[/red]")
            return False
        
        # Test the model before switching
        try:
            ollama.chat(model=model_name, messages=[{'role': 'user', 'content': 'test'}])
            self.current_model = model_name
            console.print(f"[green]✓ Switched to model: {model_name}[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to switch to {model_name}: {e}[/red]")
            return False
    
    def list_models(self) -> Table:
        """Create a table of available models with their info"""
        table = Table(title="Available AI Models")
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Size", style="yellow")
        table.add_column("Speed", style="green")
        table.add_column("Description", style="white")
        table.add_column("Current", justify="center")
        
        for model in self.available_models:
            info = self.model_info.get(model, {})
            current_marker = "🟢" if model == self.current_model else ""
            
            table.add_row(
                model,
                info.get('category', 'unknown'),
                info.get('size', 'Unknown'),
                info.get('speed', 'Unknown'),
                info.get('description', 'No description'),
                current_marker
            )
        
        return table
    
    def get_model_recommendations(self, task_type: str) -> List[Tuple[str, str]]:
        """Get model recommendations for a task type"""
        recommendations = []
        
        task_categories = {
            'code': ['codellama', 'codegemma'],
            'analysis': ['mixtral', 'llama3.2', 'llama3.1'],
            'quick': ['phi3', 'mistral', 'gemma'],
            'general': ['llama3.1', 'llama3.2', 'mistral'],
            'security': ['mixtral', 'llama3.2'],
            'performance': ['mixtral', 'llama3.2']
        }
        
        preferred_models = task_categories.get(task_type, task_categories['general'])
        
        for model_preference in preferred_models:
            for available_model in self.available_models:
                if model_preference in available_model.lower():
                    info = self.model_info.get(available_model, {})
                    reason = f"Best for: {', '.join(info.get('strengths', []))}"
                    recommendations.append((available_model, reason))
                    break
        
        return recommendations[:3]  # Top 3 recommendations