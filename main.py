#!/usr/bin/env python3
"""
AI Fabric Shell - Main entry point
"""

import sys
import os
from pathlib import Path
from rich.console import Console

# Add the current directory to Python path so we can import fabric_shell
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

console = Console()

def main():
    """Entry point"""
    try:
        # Import here to avoid import issues
        from fabric_shell.core.shell import AIFabricShell
        
        shell = AIFabricShell()
        shell.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except ImportError as e:
        console.print(f"[red]Import error: {e}[/red]")
        console.print("[yellow]Make sure all dependencies are installed:[/yellow]")
        console.print("pip install rich ollama pyyaml psutil")
        console.print(f"[yellow]Current directory: {current_dir}[/yellow]")
        console.print(f"[yellow]Python path: {sys.path}[/yellow]")
        
        # Check if fabric_shell directory exists
        fabric_shell_dir = current_dir / "fabric_shell"
        if fabric_shell_dir.exists():
            console.print(f"[green]✓ fabric_shell directory found at: {fabric_shell_dir}[/green]")
        else:
            console.print(f"[red]✗ fabric_shell directory not found at: {fabric_shell_dir}[/red]")
            console.print("[yellow]Please ensure the fabric_shell package directory exists[/yellow]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()