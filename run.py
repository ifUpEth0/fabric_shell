#!/usr/bin/env python3
"""
AI Fabric Shell - Simple entry point that works regardless of package structure
"""

import sys
import os
from pathlib import Path

# Ensure we can import from the fabric_shell directory
current_dir = Path(__file__).parent.resolve()
fabric_shell_path = current_dir / "fabric_shell"

if fabric_shell_path.exists():
    sys.path.insert(0, str(current_dir))
else:
    print(f"Error: fabric_shell directory not found at {fabric_shell_path}")
    print("Please ensure you have the correct directory structure:")
    print("├── run.py (this file)")
    print("├── fabric_shell/")
    print("│   ├── __init__.py")
    print("│   ├── core/")
    print("│   ├── models/")
    print("│   ├── plugins/")
    print("│   ├── rendering/")
    print("│   └── utils/")
    sys.exit(1)

try:
    from fabric_shell.core.shell import AIFabricShell
    from rich.console import Console
    
    console = Console()
    
    def main():
        """Entry point"""
        try:
            shell = AIFabricShell()
            shell.run()
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("\nMake sure all dependencies are installed:")
    print("pip install rich ollama pyyaml psutil")
    print(f"\nPython path: {sys.path}")
    sys.exit(1)