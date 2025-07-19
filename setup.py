#!/usr/bin/env python3
"""
Setup script to create sample plugins in the correct location
"""

from pathlib import Path
from rich.console import Console

console = Console()

def create_sample_plugins():
    """Create sample plugins in the plugins directory"""
    
    # Create plugins directory in current working directory
    plugins_dir = Path.cwd() / "plugins"
    plugins_dir.mkdir(exist_ok=True)
    
    console.print(f"[cyan]Creating sample plugins in: {plugins_dir}[/cyan]")
    
    # Plugin 1: Command Generator
    cmd_generator = """name: "cmd_generator"
description: "Generate shell commands for specific tasks"
category: "automation"
model_category: "quick"

parameters:
  task:
    prompt: "What task do you want to accomplish?"
    type: "string"
  shell_type:
    prompt: "Shell type (bash/powershell/cmd)"
    type: "string"
    default: "bash"

prompt: |
  Generate a shell command to accomplish this task: {task}
  
  Requirements:
  - Use {shell_type} syntax
  - Single command line only
  - Production-ready and safe
  - Include brief explanation
  
  Task: {task}
  Shell: {shell_type}

context: |
  The user wants to: {task}
  Target shell: {shell_type}

post_process:
  type: "execute"

examples:
  - "Find all Python files larger than 1MB"
  - "Create a backup of the current directory"
  - "Monitor system CPU usage"
"""

    # Plugin 2: Code Review
    code_review = """name: "code_review"
description: "Perform comprehensive code review and analysis"
category: "development"
preferred_model: "codellama"
model_category: "code"

parameters:
  code_file:
    prompt: "Path to code file to review"
    type: "file"
  language:
    prompt: "Programming language (auto-detect if empty)"
    type: "string"
    default: ""

prompt: |
  Perform a comprehensive code review of this {language} code:
  
  ```{language}
  {code_file}
  ```
  
  Please provide:
  
  ## 🔍 Code Analysis
  
  ### Security Issues
  - Identify potential security vulnerabilities
  - Suggest secure coding practices
  
  ### Performance Optimization
  - Spot performance bottlenecks
  - Recommend optimizations
  
  ### Code Quality
  - Check for code smells
  - Suggest refactoring opportunities
  
  ### Best Practices
  - Adherence to language conventions
  - Design pattern recommendations
  
  ### Bug Detection
  - Potential runtime errors
  - Logic issues
  
  ## 🚀 Recommendations
  
  Provide specific, actionable improvements with code examples.

context: |
  Code review for: {code_file}
  Language: {language}

examples:
  - "Review a Python Flask application"
  - "Analyze JavaScript performance issues"
  - "Security audit of authentication code"
"""

    # Plugin 3: Quick Command
    quick_command = """name: "quick_command"
description: "Generate simple one-liner commands quickly"
category: "automation"
model_category: "quick"

parameters:
  action:
    prompt: "What do you want to do?"
    type: "string"

prompt: |
  Generate a single command to: {action}
  
  Respond with ONLY the command, no explanation.

context: |
  Quick command generation for: {action}

post_process:
  type: "execute"

examples:
  - "List all running processes"
  - "Check disk space"
  - "Find large files"
"""

    # Plugin 4: File Operations
    file_ops = """name: "file_operations"
description: "Generate file and directory management commands"
category: "system"
model_category: "quick"

parameters:
  operation:
    prompt: "What file operation do you need?"
    type: "string"
  target:
    prompt: "Target file/directory (optional)"
    type: "string"
    default: ""

prompt: |
  Generate commands for this file operation: {operation}
  Target: {target}
  
  Provide safe, production-ready commands with explanations.

context: |
  File operation: {operation}
  Target: {target}

examples:
  - "Backup a directory"
  - "Find duplicate files"
  - "Change file permissions"
"""

    # Write the plugins
    plugins = {
        "cmd_generator.yml": cmd_generator,
        "code_review.yml": code_review,
        "quick_command.yml": quick_command,
        "file_operations.yml": file_ops
    }
    
    for filename, content in plugins.items():
        plugin_file = plugins_dir / filename
        with open(plugin_file, 'w', encoding='utf-8') as f:
            f.write(content)
        console.print(f"[green]✓[/green] Created: {filename}")
    
    console.print(f"\n[green]Created {len(plugins)} sample plugins![/green]")
    console.print(f"Plugins directory: {plugins_dir}")
    console.print("\nYou can now run the fabric shell and use 'list' to see the plugins.")

if __name__ == "__main__":
    create_sample_plugins()