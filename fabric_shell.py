#!/usr/bin/env python3
"""
AI Fabric Shell - Local AI automation with Rich UI and plugin system
"""

import os
import sys
import yaml
import ollama
import subprocess
import platform
import psutil
import re
import glob
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.columns import Columns

console = Console()

class SystemInfo:
    """Detect and provide system information for AI context"""
    
    def __init__(self):
        self.os_name = platform.system()
        self.os_version = platform.version()
        self.architecture = platform.machine()
        self.python_version = platform.python_version()
        self.available_tools = self._detect_tools()
        
    def _detect_tools(self) -> Dict[str, bool]:
        """Detect available command-line tools"""
        tools = {
            'git': shutil.which('git') is not None,
            'docker': shutil.which('docker') is not None,
            'python': shutil.which('python') is not None,
            'node': shutil.which('node') is not None,
            'npm': shutil.which('npm') is not None,
            'curl': shutil.which('curl') is not None,
            'wget': shutil.which('wget') is not None,
            'ssh': shutil.which('ssh') is not None,
        }
        
        # Windows specific
        if self.os_name == 'Windows':
            tools.update({
                'powershell': shutil.which('powershell') is not None,
                'cmd': True,  # cmd is always available on Windows
                'wsl': shutil.which('wsl') is not None,
            })
        
        return tools
    
    def get_context_string(self) -> str:
        """Generate context string for AI interactions"""
        available_tools = [tool for tool, available in self.available_tools.items() if available]
        
        context = f"""System Context:
- OS: {self.os_name} {self.os_version}
- Architecture: {self.architecture}
- Python: {self.python_version}
- Available tools: {', '.join(available_tools)}"""
        
        if self.os_name == 'Windows':
            context += f"\n- Running in Windows environment with PowerShell/CMD support"
        elif self.os_name == 'Darwin':
            context += f"\n- Running on macOS with standard Unix utilities"
        else:
            context += f"\n- Running on Linux/Unix with standard shell utilities"
            
        return context

class WindowsCompleter:
    """Windows-specific tab completion using PSReadLine-like behavior"""
    
    def __init__(self, shell_instance):
        self.shell = shell_instance
        self.commands = ['list', 'ls', 'run', 'cmd', 'status', 'chat', 'troubleshoot', 'fix', 'help', 'h', 'quit', 'exit', 'q']
        
    def get_suggestions(self, partial_input: str) -> List[str]:
        """Get completion suggestions for Windows"""
        if not partial_input:
            return self.commands[:5]
            
        words = partial_input.split()
        
        # Main commands
        if len(words) == 1 and not partial_input.endswith(' '):
            matches = [cmd for cmd in self.commands if cmd.startswith(partial_input.lower())]
            return matches
        
        # Plugin completion for 'run'
        if partial_input.startswith('run '):
            plugin_part = partial_input[4:]
            if not partial_input.endswith(' '):
                plugins = [f"run {name}" for name in self.shell.plugin_manager.list_plugins() 
                          if name.startswith(plugin_part)]
                return plugins
        
        # Path completion
        return self._complete_paths(partial_input)
    
    def _complete_paths(self, text: str) -> List[str]:
        """Complete file paths on Windows"""
        try:
            # Handle different cases
            if '\\' in text or '/' in text:
                # Has path separators
                parts = text.replace('/', '\\').split('\\')
                if len(parts) > 1:
                    directory = '\\'.join(parts[:-1])
                    filename = parts[-1]
                else:
                    directory = '.'
                    filename = text
            else:
                directory = '.'
                filename = text
            
            if not os.path.exists(directory):
                return []
            
            matches = []
            for item in os.listdir(directory):
                if item.lower().startswith(filename.lower()):
                    full_path = os.path.join(directory, item)
                    if os.path.isdir(full_path):
                        matches.append(f"{text[:len(text)-len(filename)]}{item}\\")
                    else:
                        matches.append(f"{text[:len(text)-len(filename)]}{item}")
            
            return sorted(matches)[:8]
            
        except (OSError, PermissionError):
            return []

class CrossPlatformPrompt:
    """Cross-platform prompt with OS-specific completion"""
    
    def __init__(self, shell_instance):
        self.shell = shell_instance
        self.is_windows = platform.system() == 'Windows'
        
        if self.is_windows:
            self.completer = WindowsCompleter(shell_instance)
        else:
            self.completer = AutoCompleter(shell_instance)
    
    def ask_with_completion(self, prompt_text: str) -> str:
        """Ask for input with platform-appropriate completion"""
        if self.is_windows:
            return self._windows_prompt(prompt_text)
        else:
            return self._unix_prompt(prompt_text)
    
    def _windows_prompt(self, prompt_text: str) -> str:
        """Windows-specific prompt with manual completion"""
        console.print(f"[bold cyan]{prompt_text}[/bold cyan]", end=" ")
        
        try:
            user_input = input().strip()
            
            # Show suggestions if input looks incomplete
            if user_input and len(user_input.split()) <= 2:
                suggestions = self.completer.get_suggestions(user_input)
                if suggestions and len(suggestions) > 1:
                    console.print(f"[dim]💡 Suggestions: {', '.join(suggestions[:5])}[/dim]")
            
            return user_input
            
        except (EOFError, KeyboardInterrupt):
            return ""
    
    def _unix_prompt(self, prompt_text: str) -> str:
        """Unix-specific prompt with readline"""
        try:
            import readline
            
            def complete(text, state):
                try:
                    line = readline.get_line_buffer()
                    completions = self.completer.get_completions(text, line)
                    return completions[state] if state < len(completions) else None
                except Exception:
                    return None
            
            readline.set_completer(complete)
            readline.parse_and_bind("tab: complete")
            
            return Prompt.ask(prompt_text)
            
        except ImportError:
            return Prompt.ask(prompt_text)

class PluginManager:
    """Manages loading and execution of AI automation plugins"""
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(exist_ok=True)
        self.plugins = {}
        self._load_plugins()
    
    def _load_plugins(self):
        """Load all YAML plugin files"""
        for plugin_file in self.plugins_dir.glob("*.y*ml"):
            try:
                with open(plugin_file, 'r') as f:
                    self.plugins[plugin_file.stem] = yaml.safe_load(f)
                console.print(f"[green]✓[/green] Loaded plugin: {plugin_file.stem}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to load {plugin_file}: {e}")
    
    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())
    
    def get_plugin_info(self, name: str) -> Dict[str, Any]:
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
        self.system_info = SystemInfo()
        self.plugin_manager = PluginManager()
        self.platform = platform.system().lower()
        self.current_shell = self._detect_shell()
        self.prompt_handler = CrossPlatformPrompt(self)
        self._test_ollama()
    
    def _detect_shell(self) -> str:
        """Detect the current shell being used"""
        if self.platform == "windows":
            return "powershell" if os.environ.get('PSModulePath') else "cmd"
        
        shell = os.environ.get('SHELL', '/bin/bash')
        for shell_type in ['zsh', 'fish', 'bash']:
            if shell_type in shell:
                return shell_type
        return "bash"
    
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
    
    def _test_ollama(self):
        """Test Ollama connection and model availability"""
        try:
            models_response = ollama.list()
            available_models = self._extract_models(models_response)
            
            if not available_models:
                console.print("[red]No models available. Install with: ollama pull llama3.1[/red]")
                sys.exit(1)
            
            # Check if default model exists
            if not any(self.model in model for model in available_models):
                console.print(f"[yellow]Model '{self.model}' not found.[/yellow]")
                console.print(f"Available: {', '.join(available_models)}")
                self.model = Prompt.ask("Select a model", choices=available_models, default=available_models[0])
            
            # Test chat functionality
            ollama.chat(model=self.model, messages=[{'role': 'user', 'content': 'test'}])
            console.print(f"[green]✓[/green] Connected to Ollama (model: {self.model})")
            
        except Exception as e:
            console.print(f"[red]✗[/red] Ollama connection failed: {e}")
            console.print("Troubleshooting:")
            console.print("1. Install Ollama: https://ollama.ai")
            console.print("2. Start service: ollama serve") 
            console.print("3. Pull model: ollama pull llama3.1")
            sys.exit(1)
    
    def _chat_with_ai(self, prompt: str, context: str = "") -> str:
        """Send prompt to AI with system context and handle response formats"""
        # Add system context to all AI interactions
        system_context = self.system_info.get_context_string()
        full_context = f"{system_context}\n\n{context}" if context else system_context
        full_prompt = f"{full_context}\n\n{prompt}" if full_context else prompt
        
        try:
            response = ollama.chat(model=self.model, messages=[{
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
    
    def _execute_command(self, command: str, language: str = None, confirm: bool = True) -> Dict[str, Any]:
        """Execute shell command with confirmation"""
        language = language or self.current_shell
        
        if confirm and not Confirm.ask(f"Execute: [cyan]{command[:100]}{'...' if len(command) > 100 else ''}[/cyan]?"):
            return {'cancelled': True}
        
        try:
            with console.status("[yellow]Executing...", spinner="dots"):
                # Build command based on shell type
                if language == "powershell":
                    cmd = ["powershell", "-Command", command]
                elif language == "python":
                    cmd = ["python", "-c", command]
                else:
                    cmd = command
                
                result = subprocess.run(
                    cmd,
                    shell=(language not in ["powershell", "python"]),
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
    
    def _execute_raw_command(self, command: str) -> Dict[str, Any]:
        """Execute raw command without confirmation (for passthrough)"""
        try:
            with console.status(f"[yellow]Executing: {command[:50]}...[/yellow]", spinner="dots"):
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
                'returncode': result.returncode,
                'command': command
            }
        except subprocess.TimeoutExpired:
            return {'error': 'Command timed out', 'command': command}
        except Exception as e:
            return {'error': str(e), 'command': command}
    
    def _handle_unknown_command(self, command: str):
        """Handle unrecognized commands by passing through to shell"""
        console.print(f"[yellow]Passing through to {self.current_shell}: {command}[/yellow]")
        
        result = self._execute_raw_command(command)
        error = self._show_result(result, f"Command '{command}' executed successfully")
        
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

Format: Explanation first, then the corrected command clearly marked."""
        
        console.print(Panel("🔍 AI analyzing failed command...", 
                          title="[yellow]Command Troubleshooting[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]AI troubleshooting...", spinner="dots"):
            response = self._chat_with_ai(prompt)
        
        console.print(Panel(response, title="[blue]AI Analysis & Fix[/blue]", border_style="blue"))
        
        # Try to extract a corrected command
        corrected = self._extract_clean_command(response)
        if corrected and corrected != command:
            console.print(Panel(Syntax(corrected, self.current_shell, theme="monokai"),
                              title="[green]Suggested Fix[/green]", border_style="green"))
            
            if Confirm.ask("[green]Try the suggested fix?[/green]"):
                result = self._execute_command(corrected, self.current_shell)
                self._show_result(result, "Fixed command executed successfully!")
    
    def _extract_clean_command(self, text: str) -> str:
        """Extract clean command from AI response"""
        # Remove markdown and backticks more aggressively
        text = re.sub(r'```[\w]*\s*', '', text)
        text = re.sub(r'```', '', text)
        text = text.replace('`', '')
        
        # Remove common AI response patterns
        text = re.sub(r'\*\*[^*]+\*\*', '', text)  # Remove **bold** text
        text = re.sub(r'^\s*[\*\-]\s*', '', text, flags=re.MULTILINE)  # Remove bullet points
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            # Skip explanatory text patterns
            skip_patterns = [
                'note:', 'here', 'this', 'you', 'the', 'explanation', 'import', 
                'modification', 'corrected', 'command', 'alternative', 'approach',
                'if you', 'can:', 'should', 'would', 'could', 'example:', 'description'
            ]
            
            if any(pattern in line.lower() for pattern in skip_patterns):
                continue
                
            # Skip lines that are clearly not commands
            if (line.endswith('.') or line.endswith(':') or 
                len(line) > 200 or len(line.split()) > 25 or
                line.startswith(('#', '//', '/*', '<!--'))):
                continue
            
            # Look for actual command patterns
            if line and not line.lower().startswith(('the ', 'this ', 'that ', 'a ', 'an ')):
                # Clean up any remaining markdown
                line = re.sub(r'[*_`]', '', line)
                return line.strip()
        
        # If no good line found, try to find git/common commands
        for line in lines:
            line_clean = re.sub(r'[*_`]', '', line).strip()
            if re.match(r'^(git|ls|cd|pwd|mkdir|rm|cp|mv|cat|grep|find|ps|top)\b', line_clean):
                return line_clean
        
        return lines[0] if lines else ""
    
    def _detect_language(self, code: str) -> str:
        """Auto-detect programming language"""
        code_lower = code.lower()
        
        patterns = {
            "powershell": ['$', 'get-', 'set-', 'new-', 'import-module'],
            "bash": ['#!/bin/bash', 'echo', 'grep', 'awk', 'sed'],
            "python": ['import ', 'def ', 'print(', 'if __name__'],
            "javascript": ['function', 'var ', 'const ', 'let ']
        }
        
        for lang, keywords in patterns.items():
            if any(keyword in code_lower for keyword in keywords):
                return lang
        
        return self.current_shell
    
    def _show_result(self, result: Dict[str, Any], success_msg: str = "Command executed successfully"):
        """Display command execution result"""
        if result.get('cancelled'):
            console.print("[yellow]Execution cancelled[/yellow]")
        elif result.get('success'):
            stdout = result.get('stdout', '').strip()
            if stdout:
                console.print(Panel(stdout, title="[green]Output[/green]", border_style="green"))
            else:
                console.print(f"[green]{success_msg}[/green]")
        else:
            error = result.get('stderr') or result.get('error') or "Unknown error"
            console.print(Panel(error.strip(), title="[red]Error[/red]", border_style="red"))
            return error.strip()
        return None
    
    def generate_oneliner(self, task: str):
        """Generate and execute one-liner command"""
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
            response = self._chat_with_ai(prompt).strip()
        
        command = self._extract_clean_command(response)
        
        if command:
            console.print(Panel(Syntax(command, self.current_shell, theme="monokai"),
                              title=f"[bold]Generated {self.current_shell.upper()} Command[/bold]",
                              border_style="green"))
            
            result = self._execute_command(command, self.current_shell)
            error = self._show_result(result)
            
            if error and Confirm.ask("[yellow]AI troubleshoot this error?[/yellow]"):
                self._troubleshoot_error(command, error, task)
        else:
            console.print("[red]Could not extract valid command from AI response[/red]")
    
    def _troubleshoot_error(self, command: str, error: str, task: str):
        """AI troubleshooting for failed commands"""
        prompt = f"""A {self.current_shell} command failed. Provide ONLY a corrected command.

Original Task: {task}
Failed Command: {command}
Error: {error}
Shell: {self.current_shell}
Platform: {self.platform}

Respond with ONLY the corrected command (no explanation/markdown)."""
        
        console.print(Panel("🔍 AI troubleshooting...", title="[yellow]Troubleshooting[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]Analyzing...", spinner="dots"):
            response = self._chat_with_ai(prompt).strip()
        
        corrected = self._extract_clean_command(response)
        
        if corrected:
            console.print(Panel(Syntax(corrected, self.current_shell, theme="monokai"),
                              title="[blue]Corrected Command[/blue]", border_style="blue"))
            
            if Confirm.ask("[green]Try corrected command?[/green]"):
                result = self._execute_command(corrected, self.current_shell)
                self._show_result(result, "Corrected command successful!")
    
    def run_plugin(self, plugin_name: str):
        """Execute a plugin"""
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if not plugin:
            console.print(f"[red]Plugin '{plugin_name}' not found[/red]")
            return
        
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
                          f"[bold]Category:[/bold] {plugin.get('category', 'general')}",
                          title="[cyan]Executing Plugin[/cyan]", border_style="blue"))
        
        with console.status("[yellow]AI processing...", spinner="dots"):
            ai_response = self._chat_with_ai(ai_prompt, context)
        
        console.print(Panel(ai_response, title=f"[green]AI Response - {plugin_name}[/green]", border_style="green"))
        
        # Handle post-processing
        if plugin.get('post_process', {}).get('type') == 'execute':
            self._extract_and_execute(ai_response, plugin_name)
    
    def _extract_and_execute(self, response: str, plugin_name: str):
        """Extract and execute code from AI response"""
        # Find code blocks
        code_pattern = r'```(?:(\w+))?\s*(.*?)```'
        matches = re.findall(code_pattern, response, re.DOTALL | re.IGNORECASE)
        
        code, language = None, None
        
        if matches:
            for lang, extracted in matches:
                if len(extracted.strip()) > 5:
                    code, language = extracted.strip(), lang.lower() if lang else None
                    break
        
        # Try raw command extraction for command plugins
        if not code and plugin_name in ['cmd_generator', 'quick_command', 'file_operations']:
            code = self._extract_clean_command(response)
            language = self.current_shell
        
        if code:
            language = language or self._detect_language(code)
            
            console.print(Panel(Syntax(code, language, theme="monokai", line_numbers=True),
                              title=f"[bold]Extracted {language.title()} Code[/bold]", border_style="yellow"))
            
            result = self._execute_command(code, language)
            error = self._show_result(result)
            
            if error and Confirm.ask("[yellow]AI troubleshoot this error?[/yellow]"):
                self._troubleshoot_script_error(code, error, language)
        else:
            console.print("[yellow]No executable code found in response[/yellow]")
    
    def _troubleshoot_script_error(self, code: str, error: str, language: str):
        """Troubleshoot script errors with AI"""
        prompt = f"""A {language} script failed. Analyze and provide:
1. Root cause analysis
2. Corrected script
3. Alternative approaches

**Script:**
```{language}
{code}
```

**Error:** {error}"""
        
        console.print(Panel("🔍 AI analyzing error...", title="[yellow]Troubleshooting[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]Troubleshooting...", spinner="dots"):
            response = self._chat_with_ai(prompt)
        
        console.print(Panel(response, title="[blue]Troubleshooting Analysis[/blue]", border_style="blue"))
        
        if "```" in response and Confirm.ask("[green]Try corrected script?[/green]"):
            self._extract_and_execute(response, "troubleshooter")
    
    def quick_troubleshoot(self, issue: str):
        """Quick AI troubleshooting"""
        prompt = f"""Troubleshoot: {issue}

Provide:
1. Likely causes
2. Diagnostic commands  
3. Solutions
4. Prevention tips

Focus on actionable advice."""
        
        console.print(Panel(f"Analyzing: {issue}", title="[yellow]Quick Troubleshoot[/yellow]", border_style="yellow"))
        
        with console.status("[yellow]AI analyzing...", spinner="dots"):
            response = self._chat_with_ai(prompt)
        
        console.print(Panel(response, title="[blue]Troubleshooting Guide[/blue]", border_style="blue"))
    
    def show_plugins(self):
        """Display available plugins"""
        table = Table(title="Available Plugins")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Category", style="magenta")
        table.add_column("Description", style="green")
        
        for name in self.plugin_manager.list_plugins():
            info = self.plugin_manager.get_plugin_info(name)
            table.add_row(name, info.get('category', 'general'), info.get('description', 'N/A'))
        
        console.print(table)
    
    def show_status(self):
        """Show system status with AI analysis"""
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        table = Table(title="System Status")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta") 
        table.add_column("Status", justify="center")
        
        table.add_row("CPU", f"{cpu:.1f}%", "🟢" if cpu < 80 else "🔴")
        table.add_row("Memory", f"{memory.percent:.1f}%", "🟢" if memory.percent < 80 else "🔴")
        table.add_row("Disk", f"{disk.percent:.1f}%", "🟢" if disk.percent < 90 else "🔴")
        table.add_row("OS", f"{self.system_info.os_name}", "ℹ️")
        table.add_row("Shell", f"{self.current_shell.upper()}", "ℹ️")
        
        with console.status("[yellow]AI analyzing...", spinner="dots"):
            analysis = self._chat_with_ai(f"""Analyze system metrics and provide 2-3 actionable recommendations:
- CPU: {cpu:.1f}%
- Memory: {memory.percent:.1f}%  
- Disk: {disk.percent:.1f}%
- Current Shell: {self.current_shell}

Focus on {self.system_info.os_name}-specific optimizations.""")
        
        console.print(Columns([
            Panel(table, title="[bold]System Metrics[/bold]"),
            Panel(analysis, title="[bold]AI Analysis[/bold]", width=50)
        ]))
        
        # Show available tools
        available_tools = [tool for tool, available in self.system_info.available_tools.items() if available]
        console.print(f"\n[dim]Available tools: {', '.join(available_tools)}[/dim]")
    
    def run(self):
        """Main interactive shell"""
        welcome = f"""[bold green]AI Fabric Shell[/bold green]
Model: {self.model} | Shell: {self.current_shell.upper()} | Platform: {self.platform.title()}
Plugins: {len(self.plugin_manager.list_plugins())}

Commands:
• [cyan]list[/cyan] - Show plugins
• [cyan]run <plugin>[/cyan] - Execute plugin  
• [cyan]cmd <task>[/cyan] - Generate command
• [cyan]status[/cyan] - System status
• [cyan]chat[/cyan] - AI chat mode
• [cyan]troubleshoot <issue>[/cyan] - Quick troubleshooting
• [cyan]help[/cyan] - Show help
• [cyan]quit[/cyan] - Exit"""
        
        console.print(Panel(welcome, title="[cyan]Welcome[/cyan]", border_style="blue"))
        
        while True:
            try:
                # Use cross-platform prompt with completion
                cmd = self.prompt_handler.ask_with_completion("fabric>")
                
                if not cmd:
                    continue
                
                # Check for built-in commands first
                if cmd.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                elif cmd.lower() in ['help', 'h']:
                    console.print(Panel(welcome, title="[bold]Help[/bold]", border_style="blue"))
                elif cmd.lower() in ['list', 'ls']:
                    self.show_plugins()
                elif cmd.lower() == 'status':
                    self.show_status()
                elif cmd.lower() == 'chat':
                    self._chat_mode()
                elif cmd.startswith('run '):
                    plugin_name = cmd[4:].strip()
                    if plugin_name:
                        self.run_plugin(plugin_name)
                    else:
                        console.print("[yellow]Usage: run <plugin_name>[/yellow]")
                        console.print("Available plugins:")
                        self.show_plugins()
                elif cmd.startswith('cmd '):
                    task = cmd[4:].strip() or Prompt.ask("Describe task")
                    self.generate_oneliner(task)
                elif cmd.startswith(('troubleshoot ', 'fix ')):
                    issue = cmd.split(' ', 1)[1] if ' ' in cmd else Prompt.ask("Describe issue")
                    self.quick_troubleshoot(issue)
                else:
                    # Unknown command - try passing through to shell
                    console.print(f"[yellow]Unknown fabric command. Trying as {self.current_shell} command...[/yellow]")
                    self._handle_unknown_command(cmd)
            
            except KeyboardInterrupt:
                console.print("\n[yellow]Use 'quit' to exit[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    def _chat_mode(self):
        """Interactive chat mode with completion"""
        console.print("[yellow]Chat mode (type 'back'/'exit'/'quit' to return)[/yellow]")
        while True:
            try:
                user_input = self.prompt_handler.ask_with_completion("chat>")
                if user_input.lower() in ['back', 'exit', 'quit', 'q']:
                    break
                
                if not user_input.strip():
                    continue
                
                with console.status("[yellow]AI thinking...", spinner="dots"):
                    response = self._chat_with_ai(user_input)
                
                console.print(Panel(response, border_style="green"))
            except KeyboardInterrupt:
                break

def main():
    """Entry point"""
    try:
        AIFabricShell().run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")

if __name__ == "__main__":
    main()