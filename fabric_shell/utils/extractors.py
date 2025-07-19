"""
Text and command extraction utilities
"""

import re
from typing import Optional

class TextExtractor:
    """Utilities for extracting commands and code from AI responses"""
    
    @staticmethod
    def extract_clean_command(text: str) -> str:
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
    
    @staticmethod
    def extract_code_blocks(text: str) -> list:
        """Extract code blocks from AI response"""
        # Find code blocks
        code_pattern = r'```(?:(\w+))?\s*(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL | re.IGNORECASE)
        
        code_blocks = []
        for lang, code in matches:
            if len(code.strip()) > 5:
                code_blocks.append({
                    'language': lang.lower() if lang else None,
                    'code': code.strip()
                })
        
        return code_blocks
    
    @staticmethod
    def detect_language(code: str) -> str:
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
        
        return "bash"  # Default fallback