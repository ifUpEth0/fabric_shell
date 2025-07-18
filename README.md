# AI Fabric Shell

A powerful local AI automation tool that combines the intelligence of large language models with system administration capabilities. Generate commands, troubleshoot issues, and automate tasks using natural language through an extensible plugin system.

## 🚀 Features

- **Smart Command Generation**: Generate shell commands from natural language descriptions
- **Cross-Platform Support**: Works on Windows (PowerShell/CMD), macOS, and Linux (bash/zsh/fish)
- **Plugin System**: Extensible YAML-based plugins for specialized tasks
- **AI-Powered Troubleshooting**: Automatic error analysis and fix suggestions
- **Rich Terminal UI**: Beautiful console interface with syntax highlighting
- **Local AI**: Uses Ollama for complete privacy and offline operation
- **Multi-Shell Detection**: Automatically detects and adapts to your current shell environment

## 📋 Prerequisites

- **Python 3.8+**
- **Ollama** - Local AI model server
- At least one language model installed via Ollama

## 🛠️ Installation

### 1. Install Ollama

Visit [ollama.ai](https://ollama.ai) and install Ollama for your platform.

### 2. Pull a Language Model

```bash
# Recommended models
ollama pull llama3.1        # General purpose, good balance
ollama pull codellama       # Code-focused tasks
ollama pull mistral         # Fast and efficient
```

### 3. Install Dependencies

```bash
pip install ollama rich pyyaml psutil
```

### 4. Clone and Run

```bash
git clone https://github.com/yourusername/ai-fabric-shell.git
cd ai-fabric-shell
python fabric_shell.py
```

## 🎯 Quick Start

1. **Start Ollama service** (if not already running):
   ```bash
   ollama serve
   ```

2. **Launch AI Fabric Shell**:
   ```bash
   python fabric_shell.py
   ```

3. **Try some commands**:
   ```
   fabric> cmd find all python files larger than 1MB
   fabric> run troubleshooter
   fabric> status
   fabric> chat
   ```

## 🔧 Core Commands

| Command | Description |
|---------|-------------|
| `cmd <task>` | Generate and execute one-liner commands |
| `run <plugin>` | Execute a specific plugin |
| `list` | Show available plugins |
| `status` | Display system status with AI analysis |
| `chat` | Enter free-form AI chat mode |
| `troubleshoot <issue>` | Quick AI troubleshooting |
| `help` | Show available commands |
| `quit` | Exit the application |

## 🔌 Plugin System

AI Fabric Shell uses YAML-based plugins for specialized tasks. Plugins are stored in the `plugins/` directory.

### Available Plugins

| Plugin | Category | Description |
|--------|----------|-------------|
| `cmd_generator` | Automation | Generate single-line commands |
| `script_generator` | Automation | Create automation scripts |
| `quick_command` | Automation | Fast command generation |
| `code_review` | Development | Review code quality and security |
| `docker_helper` | Containers | Docker configurations and troubleshooting |
| `file_operations` | System | File and directory operations |
| `log_analyzer` | System | Analyze log files for issues |
| `troubleshooter` | System | Diagnose system problems |
| `security_audit` | Security | Security configuration audits |
| `performance_optimizer` | Performance | System performance analysis |
| `deployment_planner` | Deployment | Plan application deployments |

### Creating Custom Plugins

Create a YAML file in the `plugins/` directory:

```yaml
name: my_plugin
description: My custom automation plugin
category: automation
parameters:
  task:
    type: string
    prompt: "What should this plugin do?"
    required: true
prompt: |
  Help the user accomplish: {task}
  
  Provide step-by-step instructions.
context: |
  You are an expert assistant helping with automation tasks.
post_process:
  type: execute
  confirm: true
```

## 💡 Usage Examples

### Generate Commands
```
fabric> cmd compress all log files older than 30 days
Generated BASH Command:
find /var/log -name "*.log" -mtime +30 -exec gzip {} \;

Execute: find /var/log -name "*.log" -mtime +30 -exec gzip {} \;? (y/n)
```

### Code Review
```
fabric> run code_review
Enter path to code file: ./my_script.py
```

### System Status
```
fabric> status
┌─ System Status ─┐  ┌─ AI Analysis ─┐
│ CPU Usage: 45%  │  │ • CPU usage is │
│ Memory: 67%     │  │   moderate      │
│ Disk: 23%       │  │ • Consider      │
└─────────────────┘  │   monitoring... │
                     └─────────────────┘
```

### Troubleshooting
```
fabric> troubleshoot docker container won't start
AI is analyzing the issue...

Troubleshooting Guide:
1. Check container logs: docker logs <container-name>
2. Verify port conflicts: netstat -tulpn
3. Check resource availability...
```

## 🔍 Testing Ollama Connection

If you encounter connection issues, use the included test script:

```bash
python ollama_test.py
```

This will help diagnose:
- Ollama service connectivity
- Available models
- Chat functionality

## 🛡️ Security Features

- **Command Confirmation**: All generated commands require user confirmation before execution
- **Timeout Protection**: Commands automatically timeout after 30 seconds
- **Error Handling**: Comprehensive error handling and reporting
- **Local Processing**: No data sent to external services

## 🎨 Rich Terminal Interface

- **Syntax Highlighting**: Commands displayed with proper syntax coloring
- **Progress Indicators**: Visual feedback for AI processing
- **Formatted Output**: Clean, readable command output
- **Error Display**: Clear error messages with troubleshooting suggestions

## 🔧 Configuration

### Environment Variables

- `SHELL`: Automatically detected, but can be overridden
- `PSModulePath`: Used to detect PowerShell on Windows

### Model Selection

The application will prompt you to select a model if the default isn't available:

```
Available models: llama3.1, codellama, mistral
Select a model [llama3.1]:
```

## 🚨 Troubleshooting

### Common Issues

**Ollama Connection Failed**
```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Test manually
ollama run llama3.1 "hello"
```

**No Models Available**
```bash
# Pull a model
ollama pull llama3.1
```

**Command Timeout**
- Commands are limited to 30 seconds
- For longer operations, run commands manually
- Consider breaking complex tasks into smaller steps

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Add your changes and tests
4. Submit a pull request

### Plugin Contributions

We welcome new plugins! Follow the existing plugin structure and include:
- Clear description and category
- Proper parameter definitions
- Helpful examples
- Documentation

## 📝 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local AI model server
- [Rich](https://github.com/Textualize/rich) - Terminal formatting
- [PyYAML](https://pyyaml.org/) - Plugin configuration parsing

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/ai-fabric-shell/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/ai-fabric-shell/discussions)
- **Documentation**: Check the `plugins/` directory for examples

---

**Made with ❤️ for system administrators, developers, and AI enthusiasts**