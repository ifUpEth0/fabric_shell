"""
Main AI Fabric Shell application class
"""

import os
import platform
import psutil
import ollama
import re
from pathlib import Path
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models.manager import ModelManager
from ..plugins.manager import PluginManager
from ..rendering.renderer import ResponseRenderer
from ..core.system_info import SystemInfo
from ..utils.commands import CommandExecutor
from ..utils.extractors import TextExtractor

console = Console()

class AIFabricShell:
    """Main application class with enhanced Markdown rendering"""
    
    def __init__(self, model: str = "llama3.1"):
        """
        Initialize the AI Fabric Shell application.

        Args:
            model (str): Initial AI model to use. Defaults to "llama3.1".

        Notes:
            1. Finds the plugins directory by searching the following locations in order:
                - `./plugins`
                - `./fabric_shell/plugins`
                - `~/.fabric_shell/plugins`
            2. Tests the Ollama connection and switches to the specified model if it exists.
        """
        self.model_manager = ModelManager()
        self.system_info = SystemInfo()
        
        # Find plugins directory - try multiple locations
        plugins_dir = self._find_plugins_directory()
        self.plugin_manager = PluginManager(str(plugins_dir))
        
        self.renderer = ResponseRenderer()
        self.command_executor = CommandExecutor()
        self.text_extractor = TextExtractor()
        
        self.platform = platform.system().lower()
        self.current_shell = self._detect_shell()
        
        # Set initial model
        if model in self.model_manager.available_models:
            self.model_manager.current_model = model
        
        self._test_ollama()
    
    def _find_plugins_directory(self) -> Path:
        """Find the plugins directory in various possible locations"""
        # Get the directory where run.py or main.py is located
        possible_locations = [
            Path.cwd() / "plugins",  # Current working directory
            Path(__file__).parent.parent.parent / "plugins",  # Go up from fabric_shell/core/shell.py
            Path(__file__).parent.parent / "plugins",  # fabric_shell/plugins
            Path(__file__).parent / "plugins",  # fabric_shell/core/plugins
        ]
        
        for location in possible_locations:
            if location.exists() and any(location.glob("*.y*ml")):
                console.print(f"[green]Found plugins directory: {location}[/green]")
                return location
        
        # Default: create in current working directory
        default_location = Path.cwd() / "plugins"
        console.print(f"[yellow]No existing plugins found, using: {default_location}[/yellow]")
        return default_location
    
    def _detect_shell(self) -> str:
        """Detect the current shell being used"""
        if self.platform == "windows":
            return "powershell" if os.environ.get('PSModulePath') else "cmd"
        
        shell = os.environ.get('SHELL', '/bin/bash')
        for shell_type in ['zsh', 'fish', 'bash']:
            if shell_type in shell:
                return shell_type
        return "bash"
    
    def _test_ollama(self):
        """Test Ollama connection and model availability"""
        try:
            if not self.model_manager.available_models:
                console.print("[red]No models available. Install with: ollama pull llama3.1[/red]")
                raise SystemExit(1)
            
            # Check if current model exists
            current_model = self.model_manager.current_model
            if not any(current_model in model for model in self.model_manager.available_models):
                console.print(f"[yellow]Model '{current_model}' not found.[/yellow]")
                self.show_models()
                model_choice = Prompt.ask("Select a model", 
                                        choices=self.model_manager.available_models, 
                                        default=self.model_manager.available_models[0])
                self.model_manager.switch_model(model_choice)
            
            # Test chat functionality
            ollama.chat(model=self.model_manager.current_model, 
                       messages=[{'role': 'user', 'content': 'test'}])
            console.print(f"[green]✓[/green] Connected to Ollama (model: {self.model_manager.current_model})")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Ollama connection failed: {e}")
            console.print("Troubleshooting:")
            console.print("1. Install Ollama: https://ollama.ai")
            console.print("2. Start service: ollama serve") 
            console.print("3. Pull model: ollama pull llama3.1")
            raise SystemExit(1)
    
    def _chat_with_ai(self, prompt: str, context: str = "", model: str = None) -> str:
        """Send prompt to AI with system context and handle response formats"""
        # Use specified model or current model
        use_model = model or self.model_manager.current_model
        
        # Add system context to all AI interactions
        system_context = self.system_info.get_context_string()
        full_context = f"{system_context}\n\n{context}" if context else system_context
        full_prompt = f"{full_context}\n\n{prompt}" if full_context else prompt
        
        try:
            response = ollama.chat(model=use_model, messages=[{
                'role': 'user', 'content': full_prompt
            }])
            
            # Handle various response formats
            if isinstance(response, dict):
                return (response.get('message', {}).get('content') or 
                       response.get('response') or response.get('content') or str(response))
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                return response.message.content
            return str(response)
            
        except Exception as e:
            return f"AI communication error: {e}"
    
    def generate_oneliner(self, task: str, suggested_model: str = None):
        """Generate and execute one-liner command"""
        # Get model recommendations
        recommendations = self.model_manager.get_model_recommendations('quick')
        
        # Use suggested model, best recommendation, or current model
        use_model = suggested_model
        if not use_model and recommendations:
            use_model = recommendations[0][0]
        if not use_model:
            use_model = self.model_manager.current_model
        
        # Show model choice if different from current
        if use_model != self.model_manager.current_model:
            console.print(f"[dim]Using model: {use_model} (optimized for quick commands)[/dim]")
        
        shell_contexts = {
            "powershell": "PowerShell cmdlets",
            "bash": "bash/Unix utilities", 
            "zsh": "zsh/Unix utilities",
            "fish": "fish shell commands",
            "cmd": "Windows CMD commands"
        }
        
        context = shell_contexts.get(self.current_shell, "shell commands")
        prompt = f"""Generate a single-line {context} command to: {task}

Requirements:
- Single line only
- Use {self.current_shell} syntax
- Production-ready and safe
- Respond with ONLY the command (no explanation/markdown)"""
        
        console.print(Panel(f"Generating {self.current_shell.upper()} command for: {task}",
                          title="[cyan]Command Generator[/cyan]", border_style="cyan"))
        
        with console.status("[yellow]AI generating...", spinner="dots"):
            response = self._chat_with_ai(prompt, model=use_model).strip()
        
        command = self.text_extractor.extract_clean_command(response)
        
        if command:
            self.renderer.render_code_block(command, self.current_shell, f"Generated {self.current_shell.upper()} Command")
            
            if Confirm.ask(f"Execute: [cyan]{command[:100]}{'...' if len(command) > 100 else ''}[/cyan]?"):
                result = self.command_executor.execute_command(command, self.current_shell)
                error = self.command_executor.show_result(result)
                
                if error and Confirm.ask("[yellow]AI troubleshoot this error?[/yellow]"):
                    self._troubleshoot_error(command, error, task)
        else:
            console.print("[red]Could not extract valid command from AI response[/red]")
    
    def _troubleshoot_error(self, command: str, error: str, task: str):
        """AI troubleshooting for failed commands"""
        prompt = f"""A {self.current_shell} command failed. Analyze the error and provide a solution.

## Original Task
{task}

## Failed Command
```{self.current_shell}
{command}
```

## Error Output
```
{error}
```

## System Context
- Shell: {self.current_shell}
- Platform: {self.platform}

Please provide:
1. **Root Cause Analysis** - What went wrong?
2. **Corrected Command** - Fixed version that should work
3. **Alternative Approaches** - Other ways to accomplish the task

Format your response with clear sections and use code blocks for commands."""
        
        console.print(Panel("🔍 AI troubleshooting...", title="[yellow]Troubleshooting[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]Analyzing...", spinner="dots"):
            response = self._chat_with_ai(prompt).strip()
        
        # Use enhanced Markdown rendering
        self.renderer.render_ai_response(response, "Troubleshooting Analysis", "blue")
        
        corrected = self.text_extractor.extract_clean_command(response)
        
        if corrected and Confirm.ask("[green]Try corrected command?[/green]"):
            if Confirm.ask(f"Execute: [cyan]{corrected}[/cyan]?"):
                result = self.command_executor.execute_command(corrected, self.current_shell)
                self.command_executor.show_result(result, "Corrected command successful!")
    
    def run_plugin(self, plugin_name: str):
        """Execute a plugin with optimal model selection"""
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            return
        
        # Determine best model for this plugin
        use_model = self._get_optimal_model_for_plugin(plugin_name, plugin)
        
        # Show model choice if different from current
        if use_model != self.model_manager.current_model:
            model_info = self.model_manager.model_info.get(use_model, {})
            console.print(f"[dim]Using model: {use_model} - {model_info.get('description', '')}[/dim]")
        
        # Collect parameter values
        values = {}
        for param_name, config in plugin.get('parameters', {}).items():
            prompt_text = config.get('prompt', f"Enter {param_name}")
            
            if config.get('type') == 'file':
                file_path = Prompt.ask(prompt_text)
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        values[param_name] = f.read()
                else:
                    console.print(f"[red]File not found: {file_path}[/red]")
                    return
            else:
                default = config.get('default')
                if param_name == 'script_type' and not default:
                    default = self.current_shell
                values[param_name] = Prompt.ask(prompt_text, default=default)
        
        # Build and execute AI prompt
        ai_prompt = plugin['prompt'].format(**values)
        context = plugin.get('context', '').format(**values) if plugin.get('context') else ''
        
        console.print(Panel(f"[bold]Plugin:[/bold] {plugin_name}\n"
                          f"[bold]Description:[/bold] {plugin.get('description', 'N/A')}\n"
                          f"[bold]Category:[/bold] {plugin.get('category', 'general')}\n"
                          f"[bold]Model:[/bold] {use_model}",
                          title="[cyan]Executing Plugin[/cyan]", border_style="blue"))
        
        with console.status("[yellow]AI processing...", spinner="dots"):
            ai_response = self._chat_with_ai(ai_prompt, context, model=use_model)
        
        # Use enhanced Markdown rendering for plugin responses
        self.renderer.render_ai_response(ai_response, f"AI Response - {plugin_name}", "green")
        
        # Handle post-processing
        if plugin.get('post_process', {}).get('type') == 'execute':
            self._extract_and_execute(ai_response, plugin_name)
    
    def _get_optimal_model_for_plugin(self, plugin_name: str, plugin: Dict[str, Any]) -> str:
        """Determine the optimal model for a plugin"""
        # 1. Check if plugin specifies a preferred model
        preferred_model = plugin.get('preferred_model')
        if preferred_model and preferred_model in self.model_manager.available_models:
            return preferred_model
        
        # 2. Check if plugin specifies a model category
        model_category = plugin.get('model_category')
        if model_category:
            recommendations = self.model_manager.get_model_recommendations(model_category)
            if recommendations:
                return recommendations[0][0]
        
        # 3. Use plugin category to determine best model
        plugin_category = plugin.get('category', 'general')
        category_mapping = {
            'development': 'code',
            'code': 'code',
            'security': 'security',
            'performance': 'performance',
            'automation': 'quick',
            'containers': 'code',
            'system': 'analysis'
        }
        
        task_type = category_mapping.get(plugin_category, 'general')
        recommendations = self.model_manager.get_model_recommendations(task_type)
        if recommendations:
            return recommendations[0][0]
        
        # 4. Fallback to current model
        return self.model_manager.current_model
    
    def _extract_and_execute(self, response: str, plugin_name: str):
        """Extract and execute code from AI response"""
        # Find code blocks
        code_blocks = self.text_extractor.extract_code_blocks(response)
        
        code, language = None, None
        
        if code_blocks:
            first_block = code_blocks[0]
            code = first_block['code']
            language = first_block['language'] or self.text_extractor.detect_language(code)
        
        # Try raw command extraction for command plugins
        if not code and plugin_name in ['cmd_generator', 'quick_command', 'file_operations']:
            code = self.text_extractor.extract_clean_command(response)
            language = self.current_shell
        
        if code:
            self.renderer.render_code_block(code, language, f"Extracted {language.title()} Code")
            
            if Confirm.ask(f"Execute: [cyan]{code[:100]}{'...' if len(code) > 100 else ''}[/cyan]?"):
                result = self.command_executor.execute_command(code, language)
                error = self.command_executor.show_result(result)
                
                if error and Confirm.ask("[yellow]AI troubleshoot this error?[/yellow]"):
                    self._troubleshoot_script_error(code, error, language)
        else:
            console.print("[yellow]No executable code found in response[/yellow]")
    
    def _troubleshoot_script_error(self, code: str, error: str, language: str):
        """Troubleshoot script errors with AI"""
        prompt = f"""A {language} script failed. Analyze and provide a comprehensive solution.

## Failed Script
```{language}
{code}
```

## Error Output
```
{error}
```

## System Context
- Language: {language}
- Platform: {self.platform}
- Shell: {self.current_shell}

Please provide:

### 1. Root Cause Analysis
What exactly went wrong and why?

### 2. Corrected Script
Provide a fixed version with proper error handling.

### 3. Alternative Approaches
Suggest different ways to accomplish the same goal.

### 4. Best Practices
Tips to prevent similar issues in the future.

Use proper code blocks and clear explanations."""
        
        console.print(Panel("🔍 AI analyzing error...", title="[yellow]Troubleshooting[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]Troubleshooting...", spinner="dots"):
            response = self._chat_with_ai(prompt)
        
        # Use enhanced Markdown rendering
        self.renderer.render_ai_response(response, "Script Troubleshooting Analysis", "blue")
        
        code_blocks = self.text_extractor.extract_code_blocks(response)
        if code_blocks and Confirm.ask("[green]Try corrected script?[/green]"):
            self._extract_and_execute(response, "troubleshooter")
    
    def quick_troubleshoot(self, issue: str):
        """Quick AI troubleshooting with enhanced formatting"""
        # Use analysis-optimized model
        recommendations = self.model_manager.get_model_recommendations('analysis')
        use_model = recommendations[0][0] if recommendations else self.model_manager.current_model
        
        if use_model != self.model_manager.current_model:
            console.print(f"[dim]Using model: {use_model} (optimized for analysis)[/dim]")
        
        prompt = f"""Analyze and troubleshoot the following issue:

## Issue Description
{issue}

## System Context
- OS: {self.system_info.os_name}
- Shell: {self.current_shell}
- Platform: {self.platform}

Please provide a comprehensive troubleshooting guide with:

### 1. Likely Causes
What are the most probable reasons for this issue?

### 2. Diagnostic Commands
Shell commands to gather more information and diagnose the problem.

### 3. Step-by-Step Solutions
Detailed solutions ranked by likelihood of success.

### 4. Prevention Tips
How to avoid this issue in the future.

Use proper formatting with code blocks for commands and clear section headers."""
        
        console.print(Panel(f"Analyzing: {issue}", title="[yellow]Quick Troubleshoot[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]AI analyzing...", spinner="dots"):
            response = self._chat_with_ai(prompt, model=use_model)
        
        # Use enhanced Markdown rendering
        self.renderer.render_ai_response(response, "Troubleshooting Guide", "blue")
    
    def _handle_unknown_command(self, command: str):
        """Handle unrecognized commands by passing through to shell"""
        console.print(f"[yellow]Passing through to {self.current_shell}: {command}[/yellow]")
        
        result = self.command_executor.execute_raw_command(command)
        error = self.command_executor.show_result(result, f"Command '{command}' executed successfully")
        
        if error:
            console.print(f"[red]Command failed: {command}[/red]")
            if Confirm.ask("[yellow]Would you like AI to analyze and suggest a fix?[/yellow]"):
                self._troubleshoot_passthrough_error(command, error)
    
    def _troubleshoot_passthrough_error(self, command: str, error: str):
        """Troubleshoot failed passthrough commands"""
        prompt = f"""A {self.current_shell} command failed. Analyze the error and provide a corrected command.

**Failed Command:** {command}
**Error:** {error}
**Shell:** {self.current_shell}
**Platform:** {self.platform}

Provide:
1. Brief explanation of what went wrong
2. Corrected command that should work
3. Alternative approaches if applicable

Format your response with clear sections and code blocks for any commands."""
        
        console.print(Panel("🔍 AI analyzing failed command...", 
                          title="[yellow]Command Troubleshooting[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]AI troubleshooting...", spinner="dots"):
            response = self._chat_with_ai(prompt)
        
        # Use enhanced Markdown rendering
        self.renderer.render_ai_response(response, "AI Analysis & Fix", "blue")
        
        # Try to extract a corrected command
        corrected = self.text_extractor.extract_clean_command(response)
        if corrected and corrected != command:
            self.renderer.render_code_block(corrected, self.current_shell, "Suggested Fix")
            
            if Confirm.ask("[green]Try the suggested fix?[/green]"):
                if Confirm.ask(f"Execute: [cyan]{corrected}[/cyan]?"):
                    result = self.command_executor.execute_command(corrected, self.current_shell)
                    self.command_executor.show_result(result, "Fixed command executed successfully!")
    
    def show_plugins(self, category: str = None):
        """Display available plugins, optionally filtered by category"""
        if category:
            # Show plugins for specific category
            plugins_by_category = self.plugin_manager.get_plugins_by_category()
            if category not in plugins_by_category:
                console.print(f"[red]No plugins found in category: {category}[/red]")
                console.print(f"Available categories: {', '.join(plugins_by_category.keys())}")
                return
            
            plugin_list = plugins_by_category[category]
            table_title = f"Plugins - {category.title()} Category"
        else:
            # Show all plugins
            plugin_list = self.plugin_manager.list_plugins()
            table_title = "Available Plugins"
        
        from rich.table import Table
        table = Table(title=table_title)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="green")
        table.add_column("Optimal Model", style="yellow")
        
        for name in plugin_list:
            info = self.plugin_manager.get_plugin_info(name)
            plugin_data = self.plugin_manager.get_plugin(name)
            optimal_model = self._get_optimal_model_for_plugin(name, plugin_data)
            
            # Truncate model name if too long
            model_display = optimal_model[:15] + "..." if len(optimal_model) > 18 else optimal_model
            
            table.add_row(
                name, 
                info.get('category', 'general'), 
                info.get('description', 'N/A'),
                model_display
            )
        
        console.print(table)
        
        # Show categories if showing all plugins
        if not category:
            categories = self.plugin_manager.get_plugins_by_category()
            categories_text = " | ".join([f"[cyan]{cat}[/cyan] ({len(plugins)})" 
                                        for cat, plugins in categories.items()])
            console.print(f"\n[dim]Categories: {categories_text}[/dim]")
            console.print("[dim]Use 'list <category>' to filter by category[/dim]")
    
    def show_models(self):
        """Display available models with detailed information"""
        table = self.model_manager.list_models()
        console.print(table)
        
        # Show model recommendations for different task types
        console.print("\n[bold]Model Recommendations by Task Type:[/bold]")
        
        task_types = ['code', 'analysis', 'quick', 'security', 'performance']
        for task_type in task_types:
            recommendations = self.model_manager.get_model_recommendations(task_type)
            if recommendations:
                best_model, reason = recommendations[0]
                console.print(f"• [cyan]{task_type.title()}:[/cyan] {best_model} - {reason}")
    
    def switch_model(self, model_name: str = None):
        """Switch to a different AI model"""
        if not model_name:
            # Show available models and prompt for selection
            self.show_models()
            model_name = Prompt.ask("Select model", 
                                  choices=self.model_manager.available_models,
                                  default=self.model_manager.current_model)
        
        if self.model_manager.switch_model(model_name):
            # Show model info
            model_info = self.model_manager.model_info.get(model_name, {})
            console.print(Panel(
                f"[bold]Model:[/bold] {model_name}\n"
                f"[bold]Category:[/bold] {model_info.get('category', 'unknown')}\n"
                f"[bold]Description:[/bold] {model_info.get('description', 'N/A')}\n"
                f"[bold]Strengths:[/bold] {', '.join(model_info.get('strengths', []))}\n"
                f"[bold]Size:[/bold] {model_info.get('size', 'Unknown')}\n"
                f"[bold]Speed:[/bold] {model_info.get('speed', 'Unknown')}",
                title="[green]Model Switched[/green]",
                border_style="green"
            ))
    
    def show_status(self):
        """Show system status with AI analysis"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        from rich.table import Table
        table = Table(title="System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta") 
        table.add_column("Status", justify="center")
        
        table.add_row("CPU", f"{cpu:.1f}%", "🟢" if cpu < 80 else "🔴")
        table.add_row("Memory", f"{memory.percent:.1f}%", "🟢" if memory.percent < 80 else "🔴")
        table.add_row("Disk", f"{disk.percent:.1f}%", "🟢" if disk.percent < 90 else "🔴")
        table.add_row("OS", f"{self.system_info.os_name}", "ℹ️")
        table.add_row("Shell", f"{self.current_shell.upper()}", "ℹ️")
        table.add_row("AI Model", f"{self.model_manager.current_model}", "🤖")
        
        # Use performance-optimized model for analysis
        recommendations = self.model_manager.get_model_recommendations('performance')
        analysis_model = recommendations[0][0] if recommendations else self.model_manager.current_model
        
        with console.status("[yellow]AI analyzing...", spinner="dots"):
            analysis_prompt = f"""Analyze these system metrics and provide actionable recommendations:

## Current System Status
- **CPU Usage:** {cpu:.1f}%
- **Memory Usage:** {memory.percent:.1f}%  
- **Disk Usage:** {disk.percent:.1f}%
- **Operating System:** {self.system_info.os_name}
- **Current Shell:** {self.current_shell}

## Available Tools
{', '.join([tool for tool, available in self.system_info.available_tools.items() if available])}

Please provide:

### Performance Assessment
Overall system health evaluation.

### Optimization Recommendations
2-3 specific, actionable recommendations for this {self.system_info.os_name} system.

### Commands to Run
Specific shell commands that would help optimize performance.

Focus on practical, {self.system_info.os_name}-specific optimizations."""
            
            analysis = self._chat_with_ai(analysis_prompt, model=analysis_model)
        
        # Create a side-by-side layout with enhanced Markdown rendering
        console.print(table)
        self.renderer.render_section_divider("AI System Analysis")
        self.renderer.render_ai_response(analysis, "System Analysis & Recommendations", "blue")
        
        # Show available tools and models
        available_tools = [tool for tool, available in self.system_info.available_tools.items() if available]
        console.print(f"\n[dim]Available tools: {', '.join(available_tools)}[/dim]")
        console.print(f"[dim]Available models: {len(self.model_manager.available_models)} | Current: {self.model_manager.current_model}[/dim]")
    
    def _chat_mode(self):
        """Interactive chat mode with model selection and enhanced rendering"""
        current_chat_model = self.model_manager.current_model
        
        console.print(f"[yellow]Chat mode with {current_chat_model} (type 'model <name>' to switch, 'back'/'exit'/'quit' to return)[/yellow]")
        
        while True:
            try:
                user_input = Prompt.ask(f"chat({current_chat_model})>")
                
                if user_input.lower() in ['back', 'exit', 'quit', 'q']:
                    break
                
                if user_input.startswith('model '):
                    model_name = user_input[6:].strip()
                    if model_name in self.model_manager.available_models:
                        current_chat_model = model_name
                        console.print(f"[green]Switched to {model_name} for this chat session[/green]")
                    else:
                        console.print(f"[red]Model '{model_name}' not available[/red]")
                        console.print(f"Available: {', '.join(self.model_manager.available_models)}")
                    continue
                
                if not user_input.strip():
                    continue
                
                with console.status("[yellow]AI thinking...", spinner="dots"):
                    response = self._chat_with_ai(user_input, model=current_chat_model)
                
                # Use enhanced Markdown rendering for chat responses
                self.renderer.render_ai_response(response, f"AI Response ({current_chat_model})", "green")
                
            except KeyboardInterrupt:
                break
    
    def show_help(self):
        """Display comprehensive help information with enhanced formatting"""
        help_content = f"""# AI Fabric Shell - Enhanced Edition

Welcome to the AI Fabric Shell with **Markdown rendering support**! All AI responses now display with proper formatting including headers, code blocks, lists, and more.

## Core Commands

- **`cmd <task>`** - Generate one-liner commands
- **`run <plugin>`** - Execute specific plugin  
- **`list [category]`** - Show plugins (optionally by category)
- **`models`** - Show available AI models with capabilities
- **`switch [model]`** - Switch AI model (interactive if no model specified)
- **`status`** - System status with AI analysis
- **`chat`** - AI chat mode with Markdown rendering
- **`troubleshoot <issue>`** - Quick troubleshooting with formatted output
- **`help`** - Show this help
- **`quit`** - Exit

## Model Commands

- **`models`** - List all models with capabilities and recommendations
- **`switch <model>`** - Switch to specific model
- **`switch`** - Interactive model selection with detailed information

## Plugin Categories

{self._get_categories_summary_markdown()}

## Current Configuration

- **Model:** {self.model_manager.current_model}
- **Shell:** {self.current_shell.upper()}  
- **Platform:** {self.platform.title()}
- **Plugins:** {len(self.plugin_manager.list_plugins())} available
- **Available Models:** {len(self.model_manager.available_models)}

## Examples

```bash
# Generate a command to find large Python files
cmd find all python files larger than 1MB

# Run code review plugin with optimal model selection
run code_review

# List development category plugins
list development

# Switch to code-optimized model
switch codellama

# Get troubleshooting help with formatted output
troubleshoot docker container won't start
```

## New Features

- 🎨 **Rich Markdown Rendering** - AI responses display with proper formatting
- 🤖 **Smart Model Switching** - Automatic optimal model selection per task
- 📊 **Model Recommendations** - Get suggestions for different task types  
- 🔧 **Plugin-Model Optimization** - Plugins automatically use best models
- 📋 **Enhanced Categorization** - Better organization of plugins and features
"""
        
        # Use the enhanced Markdown renderer for help
        self.renderer.render_ai_response(help_content, "Help - AI Fabric Shell", "blue")
    
    def _get_categories_summary_markdown(self) -> str:
        """Get a markdown-formatted summary of plugin categories"""
        categories = self.plugin_manager.get_plugins_by_category()
        summary_lines = []
        for category, plugins in categories.items():
            plugin_list = ', '.join(plugins[:3])
            if len(plugins) > 3:
                plugin_list += f" *(+{len(plugins)-3} more)*"
            summary_lines.append(f"- **{category.title()}** ({len(plugins)}): {plugin_list}")
        return '\n'.join(summary_lines) if summary_lines else "- No plugin categories found"
    
    def run(self):
        """Main interactive shell with enhanced welcome message"""
        welcome_content = f"""# AI Fabric Shell - Enhanced Edition

**Current Configuration:**
- **Model:** {self.model_manager.current_model}
- **Shell:** {self.current_shell.upper()}
- **Platform:** {self.platform.title()}
- **Plugins:** {len(self.plugin_manager.list_plugins())} available
- **Models:** {len(self.model_manager.available_models)} available

## ✨ New Features

- 🎨 **Rich Markdown Rendering** - AI responses now display with proper formatting
- 📊 **Smart Model Recommendations** - Get optimal model suggestions by task type
- 🔧 **Plugin-Model Optimization** - Plugins automatically select best models
- 📋 **Enhanced Documentation** - Better help and status information

## Quick Start

Type **`help`** for all commands or **`models`** to see AI model options.

*Ready to automate with AI!*"""
        
        # Use enhanced rendering for welcome message
        self.renderer.render_ai_response(welcome_content, "Welcome", "cyan")
        
        while True:
            try:
                # Enhanced prompt showing current model
                model_short = self.model_manager.current_model.split(':')[0]  # Remove version tags
                cmd = Prompt.ask(f"fabric({model_short})>")
                
                if not cmd:
                    continue
                
                # Parse commands
                cmd_parts = cmd.split()
                cmd_main = cmd_parts[0].lower()
                cmd_args = cmd_parts[1:] if len(cmd_parts) > 1 else []
                
                # Check for built-in commands first
                if cmd_main in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif cmd_main in ['help', 'h']:
                    self.show_help()
                elif cmd_main in ['list', 'ls']:
                    category = cmd_args[0] if cmd_args else None
                    self.show_plugins(category)
                elif cmd_main == 'models':
                    self.show_models()
                elif cmd_main == 'switch':
                    model_name = cmd_args[0] if cmd_args else None
                    self.switch_model(model_name)
                elif cmd_main == 'status':
                    self.show_status()
                elif cmd_main == 'chat':
                    self._chat_mode()
                elif cmd_main == 'run':
                    if cmd_args:
                        plugin_name = cmd_args[0]
                        self.run_plugin(plugin_name)
                    else:
                        console.print("[yellow]Usage: run <plugin_name>[/yellow]")
                        console.print("Available plugins:")
                        self.show_plugins()
                elif cmd_main == 'cmd':
                    task = ' '.join(cmd_args) if cmd_args else Prompt.ask("Describe task")
                    self.generate_oneliner(task)
                elif cmd_main in ['troubleshoot', 'fix']:
                    issue = ' '.join(cmd_args) if cmd_args else Prompt.ask("Describe issue")
                    self.quick_troubleshoot(issue)
                elif cmd_main == 'debug':
                    self._debug_plugins()
                else:
                    # Unknown command - try passing through to shell
                    console.print(f"[yellow]Unknown fabric command. Trying as {self.current_shell} command...[/yellow]")
                    self._handle_unknown_command(cmd)
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def _debug_plugins(self):
        """Debug plugin loading and display issues"""
        debug_info = self.plugin_manager.debug_info()
        
        console.print("[cyan]Plugin Debug Information[/cyan]")
        console.print(f"Plugins directory: {debug_info['plugins_dir']}")
        console.print(f"Directory exists: {debug_info['plugins_dir_exists']}")
        console.print(f"YAML files found: {debug_info['yaml_files']}")
        console.print(f"Loaded plugins: {debug_info['loaded_plugins']}")
        console.print(f"Plugin count: {debug_info['plugin_count']}")
        
        console.print("\n[yellow]Plugin data structure:[/yellow]")
        for name, keys in debug_info['plugins_data'].items():
            console.print(f"  {name}: {keys}")
        
        # Test the list method
        plugin_list = self.plugin_manager.list_plugins()
        console.print(f"\nlist_plugins() returns: {plugin_list}")
        
        # Test each plugin's info
        console.print("\n[yellow]Plugin info test:[/yellow]")
        for name in plugin_list:
            info = self.plugin_manager.get_plugin_info(name)
            console.print(f"  {name}: {info}")
        
        # Test categories
        categories = self.plugin_manager.get_plugins_by_category()
        console.print(f"\nCategories: {categories}")
        
        # Try to manually create a table
        if plugin_list:
            console.print("\n[green]Manually creating table...[/green]")
            from rich.table import Table
            table = Table(title="Debug Table")
            table.add_column("Name", style="cyan")
            table.add_column("Category", style="magenta")
            table.add_column("Description", style="green")
            
            for name in plugin_list:
                info = self.plugin_manager.get_plugin_info(name)
                table.add_row(
                    name,
                    info.get('category', 'N/A'),
                    info.get('description', 'N/A')
                )
            console.print(table)
        else:
            console.print("[red]No plugins to display in table[/red]")