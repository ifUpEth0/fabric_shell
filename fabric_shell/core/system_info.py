"""
System information detection and context generation
"""

import platform
import shutil
from typing import Dict

class SystemInfo:
    """Detect and provide system information for AI context"""
    
    def __init__(self):
        """
        Initialize system information detection

        Sets the following instance variables:

        - os_name: The name of the operating system (e.g. 'Windows', 'Darwin', 'Linux')
        - os_version: The version of the operating system (e.g. '10', '19.3.0', '5.3.0-46-generic')
        - architecture: The system architecture (e.g. 'x86_64', 'AMD64', 'armv7l')
        - python_version: The version of Python being used (e.g. '3.7.3', '3.8.0rc1')
        - available_tools: A dictionary of available command-line tools, where the keys are the names
          of the tools and the values are boolean flags indicating whether the tool is available
        """
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