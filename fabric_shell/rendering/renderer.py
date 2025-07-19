"""
Response rendering module with Markdown support
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.rule import Rule

console = Console()

class ResponseRenderer:
    """Handles rendering AI responses with proper Markdown support"""
    
    @staticmethod
    def render_ai_response(content: str, title: str = "AI Response", border_style: str = "green") -> None:
        """Render AI response with proper Markdown formatting"""
        try:
            # Check if content contains significant Markdown elements
            markdown_indicators = [
                '##', '###', '####',  # Headers
                '```',                # Code blocks
                '- ',                 # Lists
                '* ',                 # Lists
                '1. ', '2. ',         # Numbered lists
                '**',                 # Bold
                '*',                  # Italic
                '[',                  # Links
                '|',                  # Tables
            ]
            
            has_markdown = any(indicator in content for indicator in markdown_indicators)
            
            if has_markdown:
                # Use Rich Markdown renderer
                md = Markdown(content, code_theme="monokai")
                console.print(Panel(md, title=f"[bold]{title}[/bold]", border_style=border_style))
            else:
                # Use regular panel for simple text
                console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style=border_style))
                
        except Exception as e:
            # Fallback to regular panel if Markdown rendering fails
            console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style=border_style))
            console.print(f"[dim yellow]Note: Markdown rendering failed: {e}[/dim yellow]")
    
    @staticmethod
    def render_code_block(code: str, language: str, title: str = "Code") -> None:
        """Render code block with syntax highlighting"""
        console.print(Panel(
            Syntax(code, language, theme="monokai", line_numbers=True),
            title=f"[bold]{title}[/bold]",
            border_style="yellow"
        ))
    
    @staticmethod
    def render_section_divider(text: str = None) -> None:
        """Render a section divider"""
        if text:
            console.print(Rule(f"[bold cyan]{text}[/bold cyan]"))
        else:
            console.print(Rule())