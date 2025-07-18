#!/usr/bin/env python3
"""
AI Fabric Shell - Local AI automation with Rich UI and plugin system
"""

import os
import sys
import json
import yaml
import ollama
import subprocess
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.live import Live
from rich.columns import Columns
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
import psutil
import time
import re

console = Console()

class PluginManager:
    """Manages loading and execution of AI automation plugins"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.plugins = {}
        self.load_plugins()
    
    def load_plugins(self):
        """Load all YAML plugin files"""
        plugin_files = list(self.plugins_dir.glob("*.yaml")) + list(self.plugins_dir.glob("*.yml"))
        
        for plugin_file in plugin_files:
            try:
                with open(plugin_file, 'r') as f:
                    plugin_data = yaml.safe_load(f)
                    plugin_name = plugin_file.stem
                    self.plugins[plugin_name] = plugin_data
                    console.print(f"[green]✓[/green] Loaded plugin: {plugin_name}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to load {plugin_file}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a plugin by name"""
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        """List all available plugins"""
        return list(self.plugins.keys())
    
    def get_plugin_info(self, name: str) -> Dict[str, Any]:
        """Get plugin information"""
        plugin = self.get_plugin(name)
        if not plugin:
            return {}
        
        return {
            'name': name,
            'description': plugin.get('description', 'No description'),
            'category': plugin.get('category', 'general'),
            'parameters': plugin.get('parameters', {}),
            'examples': plugin.get('examples', [])
        }

class AIFabricShell:
    """Main application class"""
    
    def __init__(self, model: str = "llama3.1"):
        self.model = model
        self.plugin_manager = PluginManager()
        self.console = console
        self.history = []
        
        # Detect current shell and platform
        self.current_shell = self.detect_current_shell()
        self.platform = platform.system().lower()
        
        # Test Ollama connection
        self.test_ollama_connection()
    
    def detect_current_shell(self) -> str:
        """Detect the current shell being used"""
        if platform.system().lower() == "windows":
            # Check if running in PowerShell
            if os.environ.get('PSModulePath'):
                return "powershell"
            else:
                return "cmd"
        else:
            # Unix-like systems
            shell = os.environ.get('SHELL', '/bin/bash')
            if 'zsh' in shell:
                return "zsh"
            elif 'fish' in shell:
                return "fish"
            elif 'bash' in shell:
                return "bash"
            else:
                return "bash"  # Default fallback
    
    def test_ollama_connection(self):
        """Test if Ollama is running and accessible"""
        try:
            # Test basic connection first
            models_response = ollama.list()
            
            # Handle different response formats
            if isinstance(models_response, dict):
                models_list = models_response.get('models', [])
            else:
                # Handle case where response has a 'models' attribute
                if hasattr(models_response, 'models'):
                    models_list = models_response.models
                else:
                    models_list = models_response
            
            # Extract model names safely
            available_models = []
            for model in models_list:
                if hasattr(model, 'model'):
                    # Model object with .model attribute (newer Ollama versions)
                    model_name = model.model
                    available_models.append(model_name)
                elif isinstance(model, dict):
                    # Dictionary format
                    model_name = model.get('name') or model.get('model') or model.get('id')
                    if model_name:
                        available_models.append(model_name)
                elif isinstance(model, str):
                    # String format
                    available_models.append(model)
            
            if not available_models:
                console.print("[red]No models available. Please install a model first.[/red]")
                console.print("Example commands:")
                console.print("  ollama pull llama3.1")
                console.print("  ollama pull codellama")
                console.print("  ollama pull mistral")
                sys.exit(1)
            
            # Check if our default model exists (exact match or partial match)
            model_exists = any(self.model in model for model in available_models)
            
            if not model_exists:
                console.print(f"[yellow]Warning: Model '{self.model}' not found.[/yellow]")
                console.print(f"Available models: {', '.join(available_models)}")
                
                # Try to find a suitable default
                suitable_models = [m for m in available_models if any(name in m.lower() for name in ['llama', 'mistral', 'codellama', 'gemma'])]
                
                if suitable_models:
                    new_model = Prompt.ask("Select a model", choices=available_models, default=suitable_models[0])
                else:
                    new_model = Prompt.ask("Select a model", choices=available_models, default=available_models[0])
                
                self.model = new_model
            
            # Test actual chat functionality
            try:
                test_response = ollama.chat(model=self.model, messages=[{
                    'role': 'user',
                    'content': 'Hello, respond with just "OK" to test connection.'
                }])
                
                if test_response and 'message' in test_response:
                    console.print(f"[green]✓[/green] Connected to Ollama (model: {self.model})")
                else:
                    console.print("[yellow]Warning: Unexpected response format from Ollama[/yellow]")
                    console.print(f"[green]✓[/green] Connected to Ollama (model: {self.model})")
                    
            except Exception as chat_error:
                console.print(f"[red]✗[/red] Chat test failed: {chat_error}")
                console.print("Try pulling a different model or check Ollama status")
                sys.exit(1)
            
        except Exception as e:
            console.print(f"[red]✗[/red] Cannot connect to Ollama: {e}")
            console.print("\nTroubleshooting steps:")
            console.print("1. Make sure Ollama is installed: https://ollama.ai")
            console.print("2. Start Ollama service: ollama serve")
            console.print("3. Pull a model: ollama pull llama3.1")
            console.print("4. Test manually: ollama run llama3.1 'hello'")
            sys.exit(1)
    
    def chat_with_ai(self, prompt: str, context: str = "") -> str:
        """Send a prompt to the AI model"""
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        try:
            response = ollama.chat(model=self.model, messages=[{
                'role': 'user',
                'content': full_prompt
            }])
            
            # Handle different response formats
            if isinstance(response, dict):
                if 'message' in response and 'content' in response['message']:
                    return response['message']['content']
                elif 'response' in response:
                    return response['response']
                elif 'content' in response:
                    return response['content']
            elif isinstance(response, str):
                return response
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                # Handle response objects with message.content attribute
                return response.message.content
            
            return f"Unexpected response format: {response}"
            
        except Exception as e:
            return f"Error communicating with AI: {e}"
    
    def execute_command(self, command: str, language: str = None, confirm: bool = True) -> Dict[str, Any]:
        """Execute a shell command with optional confirmation"""
        # Use detected shell if no language specified
        if not language:
            language = self.current_shell
            
        if confirm:
            if not Confirm.ask(f"Execute: [bold cyan]{command[:100]}{'...' if len(command) > 100 else ''}[/bold cyan]?"):
                return {'cancelled': True}
        
        try:
            with console.status("[bold yellow]Executing...", spinner="dots"):
                # Determine how to execute based on language
                if language.lower() == "powershell":
                    # Execute PowerShell script
                    result = subprocess.run(
                        ["powershell", "-Command", command],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )
                elif language.lower() == "python":
                    # Execute Python script
                    result = subprocess.run(
                        ["python", "-c", command],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )
                elif language.lower() == "cmd":
                    # Execute CMD command
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )
                else:
                    # Default to shell execution (bash/zsh/fish)
                    result = subprocess.run(
                        command, 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        timeout=30,
                        encoding='utf-8',
                        errors='replace'
                    )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Command timed out'}
        except Exception as e:
            return {'error': str(e)}
    
    def extract_and_execute_script(self, ai_response: str, plugin_name: str):
        """Extract script from AI response and offer to execute it"""
        
        extracted_code = None
        detected_language = None
        
        # First, try to find markdown code blocks
        code_block_pattern = r'```(?:(\w+))?\s*(.*?)```'
        matches = re.findall(code_block_pattern, ai_response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            for lang, code in matches:
                code = code.strip()
                if len(code) > 5:  # Must be substantial
                    extracted_code = code
                    detected_language = lang.lower() if lang else None
                    break
        
        # If no code blocks, try to extract raw commands for command generator plugins
        if not extracted_code and plugin_name in ['cmd_generator', 'quick_command', 'file_operations']:
            extracted_code = self.extract_clean_command(ai_response)
            if extracted_code:
                detected_language = self.current_shell
        
        if extracted_code:
            # Auto-detect language if not specified
            if not detected_language:
                detected_language = self.detect_language(extracted_code)
            
            console.print(Panel(
                Syntax(extracted_code, detected_language, theme="monokai", line_numbers=True),
                title=f"[bold]Extracted {detected_language.title()} Command[/bold]",
                border_style="yellow"
            ))
            
            result = self.execute_command(extracted_code, detected_language)
            
            if result.get('cancelled'):
                console.print("[yellow]Execution cancelled[/yellow]")
            elif result.get('success'):
                stdout = result.get('stdout', '').strip()
                if stdout:
                    console.print(Panel(
                        stdout,
                        title="[green]Command Output[/green]",
                        border_style="green"
                    ))
                else:
                    console.print("[green]Command executed successfully (no output)[/green]")
            else:
                error_msg = (result.get('stderr') or result.get('error') or "Unknown error").strip()
                console.print(Panel(
                    error_msg,
                    title="[red]Command Failed[/red]",
                    border_style="red"
                ))
                
                if Confirm.ask("[yellow]Would you like AI to analyze this error and suggest a fix?[/yellow]"):
                    self.troubleshoot_command_error(extracted_code, error_msg, "command execution")
        else:
            console.print("[yellow]No executable commands found in AI response[/yellow]")
    
    def detect_language(self, code: str) -> str:
        """Detect the programming language of code"""
        code_lower = code.lower()
        
        if any(keyword in code_lower for keyword in ['$', 'get-', 'set-', 'new-', 'import-module']):
            return "powershell"
        elif any(keyword in code_lower for keyword in ['#!/bin/bash', 'echo', 'grep', 'awk', 'sed']):
            return "bash"
        elif any(keyword in code_lower for keyword in ['import ', 'def ', 'print(', 'if __name__']):
            return "python"
        elif any(keyword in code_lower for keyword in ['function', 'var ', 'const ', 'let ']):
            return "javascript"
        else:
            return self.current_shell
    
    def generate_oneliner(self, task_description: str):
        """Generate and execute a one-liner command"""
        
        # Create a context-aware prompt based on current shell
        shell_context = {
            "powershell": "PowerShell cmdlets and syntax",
            "bash": "bash commands and Unix utilities", 
            "zsh": "zsh commands and Unix utilities",
            "fish": "fish shell commands and Unix utilities",
            "cmd": "Windows Command Prompt commands"
        }
        
        context = shell_context.get(self.current_shell, "shell commands")
        
        oneliner_prompt = f"""
        Generate a single-line {context} command to: {task_description}
        
        Requirements:
        - Must be a single line command
        - Use {self.current_shell} syntax
        - Be production-ready and safe to execute
        
        Respond with ONLY the command. No explanation, no markdown, no backticks.
        """
        
        console.print(Panel(
            f"Generating {self.current_shell.upper()} one-liner for: {task_description}",
            title="[bold cyan]Command Generator[/bold cyan]",
            border_style="cyan"
        ))
        
        with console.status("[bold yellow]AI generating command...", spinner="dots"):
            response = self.chat_with_ai(oneliner_prompt).strip()
        
        # Extract clean command
        command = self.extract_clean_command(response)
        
        if command:
            # Show the generated command
            console.print(Panel(
                Syntax(command, self.current_shell, theme="monokai"),
                title=f"[bold]Generated {self.current_shell.upper()} Command[/bold]",
                border_style="green"
            ))
            
            # Execute the command
            result = self.execute_command(command, self.current_shell)
            
            if result.get('cancelled'):
                console.print("[yellow]Execution cancelled[/yellow]")
            elif result.get('success'):
                if result.get('stdout'):
                    # Clean and format the output
                    output = result['stdout'].strip()
                    if output:
                        console.print(Panel(
                            output,
                            title="[green]Command Output[/green]",
                            border_style="green"
                        ))
                    else:
                        console.print("[green]Command executed successfully (no output)[/green]")
                else:
                    console.print("[green]Command executed successfully (no output)[/green]")
            else:
                # Command failed - show error and offer troubleshooting
                error_msg = result.get('stderr') or result.get('error') or "Unknown error"
                error_msg = error_msg.strip()
                
                console.print(Panel(
                    error_msg,
                    title="[red]Command Failed[/red]",
                    border_style="red"
                ))
                
                # Offer automatic troubleshooting
                if Confirm.ask("[yellow]Would you like AI to analyze this error and suggest a fix?[/yellow]"):
                    self.troubleshoot_command_error(command, error_msg, task_description)
        else:
            console.print("[red]Could not extract a valid command from AI response[/red]")
    
    def troubleshoot_command_error(self, command: str, error_message: str, original_task: str):
        """Troubleshoot a failed one-liner command"""
        
        troubleshoot_prompt = f"""
        A {self.current_shell} command failed. Please provide ONLY a corrected command.
        
        **Original Task:** {original_task}
        **Failed Command:** {command}
        **Error:** {error_message}
        **Shell:** {self.current_shell}
        **Platform:** {self.platform}
        
        Respond with ONLY the corrected command. No explanation, no notes, no markdown - just the command.
        """
        
        console.print(Panel(
            "🔍 AI is analyzing the command error...",
            title="[bold yellow]Command Troubleshooting[/bold yellow]",
            border_style="yellow"
        ))
        
        with console.status("[bold yellow]AI troubleshooting...", spinner="dots"):
            response = self.chat_with_ai(troubleshoot_prompt).strip()
        
        # Clean up the response more aggressively
        corrected_command = self.extract_clean_command(response)
        
        if corrected_command:
            console.print(Panel(
                Syntax(corrected_command, self.current_shell, theme="monokai"),
                title="[bold blue]Corrected Command[/bold blue]",
                border_style="blue"
            ))
            
            if Confirm.ask("[green]Would you like to try the corrected command?[/green]"):
                result = self.execute_command(corrected_command, self.current_shell)
                
                if result.get('cancelled'):
                    console.print("[yellow]Execution cancelled[/yellow]")
                elif result.get('success'):
                    if result.get('stdout'):
                        console.print(Panel(
                            result['stdout'],
                            title="[green]Output[/green]",
                            border_style="green"
                        ))
                    else:
                        console.print("[green]Corrected command executed successfully![/green]")
                else:
                    error_msg = result.get('stderr') or result.get('error') or "Unknown error"
                    console.print(Panel(
                        error_msg,
                        title="[red]Corrected Command Also Failed[/red]",
                        border_style="red"
                    ))
        else:
            console.print("[red]Could not extract a clean command from AI response[/red]")
    
    def extract_clean_command(self, text: str) -> str:
        """Extract a clean command from potentially messy AI response"""
        
        # Remove markdown code blocks
        text = re.sub(r'```[\w]*\s*', '', text)
        text = re.sub(r'```', '', text)
        
        # Remove backticks
        text = text.replace('`', '')
        
        # Split into lines and find the best command line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Skip obvious explanatory text
            if any(skip in line.lower() for skip in [
                'note:', 'here', 'this', 'you', 'the', 'explanation',
                'import', 'modification', 'profile', 'relevant',
                'didn\'t include', 'not include'
            ]):
                continue
            
            # Skip lines that end with periods (explanatory sentences)
            if line.endswith('.'):
                continue
            
            # Skip lines that are too long to be commands (likely explanations)
            if len(line) > 200:
                continue
            
            # If we find a line that looks like a command, return it
            if line and len(line.split()) <= 20:  # Reasonable command length
                return line
        
        # If no good line found, return the first non-empty line
        return lines[0] if lines else ""
    
    def troubleshoot_script_error(self, script_code: str, error_message: str, language: str):
        """Use AI to troubleshoot script execution errors"""
        
        troubleshoot_prompt = f"""
        I have a {language} script that failed to execute. Please analyze the error and provide:
        1. Root cause analysis of the error
        2. Specific fixes for the script
        3. Corrected version of the script
        4. Alternative approaches if needed
        
        **Original Script:**
        ```{language}
        {script_code}
        ```
        
        **Error Message:**
        {error_message}
        
        Please provide a corrected script that addresses these issues.
        """
        
        console.print(Panel(
            "🔍 AI is analyzing the error...",
            title="[bold yellow]Troubleshooting[/bold yellow]",
            border_style="yellow"
        ))
        
        with console.status("[bold yellow]AI troubleshooting...", spinner="dots"):
            troubleshoot_response = self.chat_with_ai(troubleshoot_prompt)
        
        console.print(Panel(
            troubleshoot_response,
            title="[bold blue]AI Troubleshooting Analysis[/bold blue]",
            border_style="blue"
        ))
        
        # Try to extract a corrected script from the response
        if "```" in troubleshoot_response:
            if Confirm.ask("[green]Would you like to try executing the corrected script?[/green]"):
                self.extract_and_execute_script(troubleshoot_response, "troubleshooter")
    
    def quick_troubleshoot(self, error_description: str):
        """Quick troubleshooting for any error"""
        console.print(Panel(
            f"Analyzing: {error_description}",
            title="[bold yellow]Quick Troubleshoot[/bold yellow]",
            border_style="yellow"
        ))
        
        troubleshoot_prompt = f"""
        Help troubleshoot this issue: {error_description}
        
        Provide:
        1. Likely causes
        2. Step-by-step diagnostic commands
        3. Specific solutions
        4. Prevention tips
        
        Focus on practical, actionable advice.
        """
        
        with console.status("[bold yellow]AI analyzing...", spinner="dots"):
            response = self.chat_with_ai(troubleshoot_prompt)
        
        console.print(Panel(
            response,
            title="[bold blue]Troubleshooting Guide[/bold blue]",
            border_style="blue"
        ))
    
    def run_plugin(self, plugin_name: str, user_input: str = ""):
        """Execute a plugin"""
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            return
        
        # Get plugin parameters
        parameters = plugin.get('parameters', {})
        values = {}
        
        for param_name, param_config in parameters.items():
            if param_name not in values:
                prompt_text = param_config.get('prompt', f"Enter {param_name}")
                default = param_config.get('default')
                
                if param_config.get('type') == 'file':
                    # File input
                    file_path = Prompt.ask(prompt_text)
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            values[param_name] = f.read()
                    else:
                        console.print(f"[red]File not found: {file_path}[/red]")
                        return
                else:
                    # Regular input - use current shell as default for script_type
                    if param_name == 'script_type' and not param_config.get('default'):
                        default_value = self.current_shell
                    else:
                        default_value = param_config.get('default')
                    
                    user_value = Prompt.ask(prompt_text, default=default_value)
                    values[param_name] = user_value or user_input or default_value
        
        # Build the AI prompt
        ai_prompt = plugin['prompt'].format(**values)
        
        # Add context if specified
        context = plugin.get('context', '')
        if context:
            context = context.format(**values)
        
        # Show what we're doing
        console.print(Panel(
            f"[bold]Plugin:[/bold] {plugin_name}\n"
            f"[bold]Description:[/bold] {plugin.get('description', 'No description')}\n"
            f"[bold]Category:[/bold] {plugin.get('category', 'general')}",
            title="[bold cyan]Executing Plugin[/bold cyan]",
            border_style="blue"
        ))
        
        # Get AI response
        with console.status("[bold yellow]AI is processing...", spinner="dots"):
            ai_response = self.chat_with_ai(ai_prompt, context)
        
        # Display result
        console.print(Panel(
            ai_response,
            title=f"[bold green]AI Response - {plugin_name}[/bold green]",
            border_style="green"
        ))
        
        # Handle post-processing
        post_process = plugin.get('post_process')
        if post_process:
            if post_process.get('type') == 'execute':
                # Extract and execute commands
                self.extract_and_execute_script(ai_response, plugin_name)
    
    def show_plugins(self):
        """Display available plugins in a nice table"""
        table = Table(title="Available Plugins")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="green")
        
        for plugin_name in self.plugin_manager.list_plugins():
            info = self.plugin_manager.get_plugin_info(plugin_name)
            table.add_row(
                plugin_name,
                info.get('category', 'general'),
                info.get('description', 'No description')
            )
        
        console.print(table)
    
    def show_system_status(self):
        """Show system status with AI analysis"""
        # Get system stats
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Create system table
        table = Table(title="System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Status", justify="center")
        
        table.add_row("CPU Usage", f"{cpu_percent:.1f}%", "🟢" if cpu_percent < 80 else "🔴")
        table.add_row("Memory", f"{memory.percent:.1f}%", "🟢" if memory.percent < 80 else "🔴")
        table.add_row("Disk", f"{disk.percent:.1f}%", "🟢" if disk.percent < 90 else "🔴")
        
        # Get AI analysis
        with console.status("[bold yellow]AI analyzing system...", spinner="dots"):
            analysis_prompt = f"""
            Analyze these system metrics and provide brief recommendations:
            - CPU: {cpu_percent:.1f}%
            - Memory: {memory.percent:.1f}%
            - Disk: {disk.percent:.1f}%
            
            Provide 2-3 bullet points with actionable advice.
            """
            ai_analysis = self.chat_with_ai(analysis_prompt)
        
        # Display results
        layout = Columns([
            Panel(table, title="[bold]Metrics[/bold]"),
            Panel(ai_analysis, title="[bold]AI Analysis[/bold]", width=50)
        ])
        
        console.print(layout)
    
    def interactive_shell(self):
        """Main interactive shell"""
        console.print(Panel(
            "[bold green]AI Fabric Shell[/bold green]\n"
            f"Model: {self.model}\n"
            f"Shell: {self.current_shell.upper()}\n"
            f"Platform: {self.platform.title()}\n"
            f"Plugins: {len(self.plugin_manager.list_plugins())}\n\n"
            "Commands:\n"
            "  • [cyan]list[/cyan] - Show available plugins\n"
            "  • [cyan]run <plugin>[/cyan] - Run a plugin\n"
            "  • [cyan]cmd <task>[/cyan] - Generate & execute one-liner command\n"
            "  • [cyan]status[/cyan] - Show system status\n"
            "  • [cyan]chat[/cyan] - Free-form AI chat\n"
            "  • [cyan]troubleshoot <issue>[/cyan] - Quick AI troubleshooting\n"
            "  • [cyan]help[/cyan] - Show this help\n"
            "  • [cyan]quit[/cyan] - Exit",
            title="[bold cyan]Welcome[/bold cyan]",
            border_style="blue"
        ))
        
        while True:
            try:
                command = Prompt.ask("\n[bold cyan]fabric>[/bold cyan]")
                
                if command.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                elif command.lower() in ['help', 'h']:
                    console.print(Panel(
                        "Available commands:\n"
                        "  • [cyan]list[/cyan] - Show available plugins\n"
                        "  • [cyan]run <plugin>[/cyan] - Run a plugin\n"
                        "  • [cyan]cmd <task>[/cyan] - Generate & execute one-liner command\n"
                        "  • [cyan]status[/cyan] - Show system status\n"
                        "  • [cyan]chat[/cyan] - Free-form AI chat\n"
                        "  • [cyan]troubleshoot <issue>[/cyan] - Quick AI troubleshooting\n"
                        "  • [cyan]help[/cyan] - Show this help\n"
                        "  • [cyan]quit[/cyan] - Exit\n\n"
                        f"Current shell: {self.current_shell.upper()}",
                        title="[bold]Help[/bold]",
                        border_style="blue"
                    ))
                
                elif command.lower() in ['list', 'ls']:
                    self.show_plugins()
                
                elif command.lower() == 'status':
                    self.show_system_status()
                
                elif command.lower() == 'chat':
                    console.print("[yellow]Entering chat mode (type 'back', 'exit', or 'quit' to return)[/yellow]")
                    while True:
                        chat_input = Prompt.ask("[bold green]chat>[/bold green]")
                        if chat_input.lower() in ['back', 'exit', 'quit', 'q']:
                            break
                        
                        with console.status("[bold yellow]AI thinking...", spinner="dots"):
                            response = self.chat_with_ai(chat_input)
                        
                        console.print(Panel(response, border_style="green"))
                
                elif command.startswith('run '):
                    plugin_name = command[4:].strip()
                    self.run_plugin(plugin_name)
                
                elif command.startswith('cmd '):
                    # One-liner command generator
                    task = command[4:].strip()
                    if not task:
                        task = Prompt.ask("Describe what you want to do")
                    self.generate_oneliner(task)
                
                elif command.startswith('troubleshoot ') or command.startswith('fix '):
                    # Quick troubleshooting command
                    error_description = command.split(' ', 1)[1] if ' ' in command else ""
                    if not error_description:
                        error_description = Prompt.ask("Describe the error or issue")
                    
                    self.quick_troubleshoot(error_description)
                
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    console.print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

def main():
    """Main entry point"""
    try:
        app = AIFabricShell()
        app.interactive_shell()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")

if __name__ == "__main__":
    main()