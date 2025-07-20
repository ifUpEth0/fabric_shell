"""
Command execution utilities with fixed PowerShell handling
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

class CommandHistoryManager:
    """Manages command execution history and success tracking"""
    
    def __init__(self, history_file: str = "command_history.json"):
        self.history_file = Path(history_file)
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load command history from file"""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load history file: {e}[/yellow]")
            return []
    
    def _save_history(self):
        """Save command history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history[-100:], f, indent=2, ensure_ascii=False)  # Keep last 100 entries
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save history: {e}[/yellow]")
    
    def add_successful_command(self, command: str, task_description: str, shell_type: str, output: str = ""):
        """Add a successful command to history"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "task_description": task_description,
            "shell_type": shell_type,
            "output_preview": output[:200] + "..." if len(output) > 200 else output,
            "success": True
        }
        
        self.history.append(entry)
        self._save_history()
    
    def get_similar_commands(self, task_description: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar successful commands based on task description"""
        task_lower = task_description.lower()
        task_words = set(task_lower.split())
        
        # Score commands based on word overlap
        scored_commands = []
        for entry in self.history:
            if not entry.get('success', False):
                continue
                
            entry_words = set(entry['task_description'].lower().split())
            overlap = len(task_words.intersection(entry_words))
            
            if overlap > 0:
                score = overlap / len(task_words.union(entry_words))
                scored_commands.append((score, entry))
        
        # Sort by score and return top matches
        scored_commands.sort(key=lambda x: x[0], reverse=True)
        return [entry for score, entry in scored_commands[:limit]]
    
    def get_context_string(self, task_description: str) -> str:
        """Get context string for AI prompt based on similar commands"""
        similar = self.get_similar_commands(task_description)
        
        if not similar:
            return ""
        
        context = "\n## Previously Successful Commands\n"
        context += "Based on similar tasks, these commands have worked before:\n\n"
        
        for i, entry in enumerate(similar, 1):
            context += f"{i}. **Task:** {entry['task_description']}\n"
            context += f"   **Command:** `{entry['command']}`\n"
            context += f"   **Shell:** {entry['shell_type']}\n"
            if entry.get('output_preview'):
                context += f"   **Result:** {entry['output_preview']}\n"
            context += "\n"
        
        context += "Consider these successful patterns when generating the new command.\n"
        return context


class CommandExecutor:
    """Enhanced command executor with explain option and history tracking"""
    
    def __init__(self):
        self.history_manager = CommandHistoryManager()
    
    def get_command_context(self, task_description: str) -> str:
        """Get context from command history for AI prompt"""
        return self.history_manager.get_context_string(task_description)
    
    def execute_command_with_options(self, command: str, task_description: str = "", 
                                   shell_type: str = "bash", ai_chat_func = None,
                                   timeout: int = 30) -> Dict[str, Any]:
        """Execute command with y/n/e options (yes/no/explain)"""
        
        # Show the command
        console.print(Panel(command, title=f"[cyan]Generated {shell_type.upper()} Command[/cyan]", 
                          border_style="cyan"))
        
        while True:
            choice = Prompt.ask(
                f"Execute command? [green]Y[/green]es/[red]N[/red]o/[yellow]E[/yellow]xplain", 
                choices=["y", "n", "e", "yes", "no", "explain"], 
                default="n"
            ).lower()
            
            if choice in ["e", "explain"]:
                self._explain_command(command, task_description, shell_type, ai_chat_func)
                continue
            elif choice in ["y", "yes"]:
                result = self.execute_command(command, shell_type, timeout)
                
                # Show the result and ask for confirmation
                error = self.show_result(result, "Command executed successfully", 
                                       ask_confirmation=True, task_description=task_description)
                
                # Handle the different outcomes
                if result.get('success') and not error:
                    # Command succeeded and user confirmed it worked
                    if task_description and not result.get('user_confirmed_failure'):
                        self.history_manager.add_successful_command(
                            command, task_description, shell_type, result.get('stdout', '')
                        )
                        console.print("[green]✓ Command saved to history as successful[/green]")
                elif result.get('user_confirmed_failure'):
                    # Command executed but didn't accomplish the goal
                    console.print("[yellow]Command not saved to history (did not meet expectations)[/yellow]")
                
                return result
            else:  # "n", "no", or any other input
                return {'cancelled': True}
    
    def _explain_command(self, command: str, task_description: str, shell_type: str, ai_chat_func):
        """Explain what the command does using AI"""
        if not ai_chat_func:
            console.print("[yellow]AI explanation not available (no AI function provided)[/yellow]")
            return
        
        explain_prompt = f"""Explain this {shell_type} command in detail:

**Command:** `{command}`
**Task Context:** {task_description}

Please provide:

### What This Command Does
Clear explanation of the command's purpose and function.

### Command Breakdown
Break down each part of the command and explain what it does.

### Potential Effects
What will happen when this command runs? What files/systems will be affected?

### Safety Considerations
Are there any risks or things to be aware of?

### Expected Output
What kind of output or result should you expect?

Use clear, non-technical language where possible."""
        
        console.print(Panel("🤖 AI is analyzing the command...", 
                          title="[yellow]Generating Explanation[/yellow]", 
                          border_style="yellow"))
        
        try:
            explanation = ai_chat_func(explain_prompt)
            
            # Use the renderer if available, otherwise use a simple panel
            try:
                from ..rendering.renderer import ResponseRenderer
                renderer = ResponseRenderer()
                renderer.render_ai_response(explanation, "Command Explanation", "blue")
            except ImportError:
                console.print(Panel(explanation, title="[blue]Command Explanation[/blue]", 
                                  border_style="blue"))
        except Exception as e:
            console.print(f"[red]Error generating explanation: {e}[/red]")
    
    def _fix_powershell_command(self, command: str) -> str:
        """Fix common PowerShell command issues for -NoProfile execution"""
        
        # Common fixes for restricted PowerShell environment
        fixes = {
            # CIM class name fixes
            'CIMOperatingSystem': 'CIM_OperatingSystem',
            'CIMProcess': 'CIM_Process',
            'CIMService': 'CIM_Service',
            'CIMDisk': 'CIM_LogicalDisk',
            'CIMProcessor': 'CIM_Processor',
            'CIMMemory': 'CIM_PhysicalMemory',
            
            # Alternative approaches for common tasks that fail in -NoProfile
            'Get-CimInstance -ClassName CIM_OperatingSystem': 'Get-ComputerInfo',
            'Get-CimInstance -ClassName CIM_Process': 'Get-Process',
            'Get-CimInstance -ClassName CIM_Service': 'Get-Service',
            'Get-CimInstance -ClassName CIM_LogicalDisk': 'Get-WmiObject -Class Win32_LogicalDisk',
        }
        
        fixed_command = command
        for old, new in fixes.items():
            fixed_command = fixed_command.replace(old, new)
        
        return fixed_command
    
    def _get_powershell_execution_policy(self) -> str:
        """Get current PowerShell execution policy"""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-ExecutionPolicy"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return "Unknown"
    
    def _should_use_profile_powershell(self, command: str) -> bool:
        """Determine if we should use PowerShell with profile for this command"""
        
        # Commands that often need profile/modules
        profile_dependent_patterns = [
            'Get-CimInstance',
            'Import-Module',
            'Get-ADUser',
            'Get-ExchangeServer',
            'Connect-',
            'New-PSSession',
            'Enter-PSSession',
            'Invoke-Command',
        ]
        
        return any(pattern in command for pattern in profile_dependent_patterns)
    
    def execute_command(self, command: str, language: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command and return result"""
        shell_type = language or "bash"
        
        try:
            with console.status("[yellow]Executing...", spinner="dots"):
                # Build command based on shell type
                if shell_type == "powershell":
                    # Check if command needs profile or can work with -NoProfile
                    if self._should_use_profile_powershell(command):
                        console.print("[dim yellow]Using PowerShell with profile (command requires modules/features)[/dim yellow]")
                        # Use PowerShell with profile but set minimal execution policy
                        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", command]
                    else:
                        # Apply fixes for -NoProfile mode
                        fixed_command = self._fix_powershell_command(command)
                        if fixed_command != command:
                            console.print(f"[dim yellow]Applied PowerShell compatibility fixes[/dim yellow]")
                        
                        # Use -NoProfile for better compatibility
                        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", fixed_command]
                elif shell_type == "python":
                    cmd = ["python", "-c", command]
                else:
                    cmd = command
                
                result = subprocess.run(
                    cmd,
                    shell=(shell_type not in ["powershell", "python"]),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    encoding='utf-8',
                    errors='replace'
                )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'command': command,
                'fixed_command': self._fix_powershell_command(command) if shell_type == "powershell" else command
            }
        except subprocess.TimeoutExpired:
            return {'error': f'Command timed out after {timeout} seconds', 'command': command}
        except Exception as e:
            return {'error': str(e), 'command': command}
    
    def execute_raw_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute raw command without confirmation (for passthrough)"""
        try:
            with console.status(f"[yellow]Executing: {command[:50]}...[/yellow]", spinner="dots"):
                # Detect if this looks like a PowerShell command
                is_powershell = any(ps_indicator in command for ps_indicator in [
                    'Get-', 'Set-', 'New-', 'Remove-', 'Start-', 'Stop-',
                    '$env:', '$_', 'Where-Object', 'ForEach-Object', 'Select-Object'
                ])
                
                if is_powershell:
                    # Apply PowerShell fixes for raw commands too
                    if self._should_use_profile_powershell(command):
                        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-Command", command]
                    else:
                        fixed_command = self._fix_powershell_command(command)
                        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", fixed_command]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        encoding='utf-8',
                        errors='replace'
                    )
                else:
                    # Regular shell command
                    result = subprocess.run(
                        command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
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
            return {'error': f'Command timed out after {timeout} seconds', 'command': command}
        except Exception as e:
            return {'error': str(e), 'command': command}
    
    def show_result(self, result: Dict[str, Any], success_msg: str = "Command executed successfully", 
                    ask_confirmation: bool = False, task_description: str = "") -> Optional[str]:
        """Display command execution result and return error if any"""
        if result.get('cancelled'):
            console.print("[yellow]Execution cancelled[/yellow]")
        elif result.get('success'):
            stdout = result.get('stdout', '').strip()
            if stdout:
                console.print(Panel(stdout, title="[green]Output[/green]", border_style="green"))
            else:
                console.print(f"[green]{success_msg}[/green]")
            
            # Ask for confirmation if requested
            if ask_confirmation and task_description:
                worked_as_expected = Prompt.ask(
                    f"Did this accomplish your goal: '[cyan]{task_description}[/cyan]'? [green]Y[/green]es/[red]N[/red]o",
                    choices=["y", "n", "yes", "no"],
                    default="y"
                ).lower() in ["y", "yes"]
                
                if worked_as_expected:
                    console.print("[green]✓ Command worked as expected[/green]")
                    return None  # Success, no error
                else:
                    console.print("[yellow]Command didn't meet expectations[/yellow]")
                    result['user_confirmed_failure'] = True
                    return "User confirmed command didn't accomplish the goal"
        else:
            error = result.get('stderr') or result.get('error') or "Unknown error"
            console.print(Panel(error.strip(), title="[red]Error[/red]", border_style="red"))
            
            # Show helpful PowerShell troubleshooting if needed
            if 'powershell' in str(result.get('command', '')).lower():
                self._show_powershell_troubleshooting(error.strip())
            
            return error.strip()
        return None
    
    def _show_powershell_troubleshooting(self, error: str):
        """Show PowerShell-specific troubleshooting tips"""
        
        troubleshooting_tips = []
        
        if "execution policy" in error.lower():
            troubleshooting_tips.append("• Try: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
        
        if "invalid class" in error.lower() or "cim" in error.lower():
            troubleshooting_tips.append("• CIM classes may not be available in restricted mode")
            troubleshooting_tips.append("• Try using Get-WmiObject instead of Get-CimInstance")
            troubleshooting_tips.append("• Alternative: Use Get-ComputerInfo for system information")
        
        if "module" in error.lower():
            troubleshooting_tips.append("• Module may not be auto-loaded in -NoProfile mode")
            troubleshooting_tips.append("• Try: Import-Module <ModuleName> first")
        
        if "not recognized" in error.lower():
            troubleshooting_tips.append("• Command may be from a module not loaded")
            troubleshooting_tips.append("• Check available commands with: Get-Command *keyword*")
        
        if troubleshooting_tips:
            tips_text = "\n".join(troubleshooting_tips)
            console.print(Panel(
                tips_text,
                title="[blue]PowerShell Troubleshooting Tips[/blue]",
                border_style="blue"
            ))