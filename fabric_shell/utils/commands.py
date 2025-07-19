"""
Command execution utilities
"""

import subprocess
from typing import Dict, Any
from rich.console import Console

console = Console()

class CommandExecutor:
    """Handles command execution with proper error handling"""
    
    @staticmethod
    def execute_command(command: str, language: str = None, timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command and return result"""
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
                    timeout=timeout,
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
            return {'error': f'Command timed out after {timeout} seconds'}
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def execute_raw_command(command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute raw command without confirmation (for passthrough)"""
        try:
            with console.status(f"[yellow]Executing: {command[:50]}...[/yellow]", spinner="dots"):
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
    
    @staticmethod
    def show_result(result: Dict[str, Any], success_msg: str = "Command executed successfully") -> str:
        """Display command execution result and return error if any"""
        from rich.panel import Panel
        
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