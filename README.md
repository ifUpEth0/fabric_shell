# AI Fabric Shell - Enhanced Edition

A modular, AI-powered command-line automation tool with rich Markdown rendering, smart model switching, command history learning, and an extensible plugin system.

## 🎯 Features

- **🎨 Rich Markdown Rendering** - AI responses display with proper formatting
- **🤖 Smart Model Management** - Automatic optimal model selection per task
- **📊 Model Recommendations** - Get suggestions for different task types
- **🔧 Plugin System** - YAML-based plugins with model optimization
- **📋 Enhanced UI** - Beautiful tables, syntax highlighting, and progress indicators
- **🚀 Command Generation** - AI-powered one-liner command generation
- **🔍 Smart Troubleshooting** - AI analysis of failed commands and scripts
- **✨ Y/N/E Command Options** - Explain commands before executing them
- **📚 Command History & Learning** - System learns from successful commands
- **🛡️ Clean PowerShell Execution** - Runs without profile to avoid Oh My Posh errors

## 📁 Project Structure

```
fabric_shell/
├── __init__.py                 # Package initialization
├── main.py                     # Entry point
├── core/
│   ├── __init__.py
│   ├── shell.py               # Main AIFabricShell class
│   └── system_info.py         # SystemInfo class
├── models/
│   ├── __init__.py
│   └── manager.py             # ModelManager class
├── plugins/
│   ├── __init__.py
│   └── manager.py             # PluginManager class
├── rendering/
│   ├── __init__.py
│   └── renderer.py            # ResponseRenderer class
└── utils/
    ├── __init__.py
    ├── commands.py            # Enhanced command execution with history
    └── extractors.py          # Text/command extraction utilities
```

## 🚀 Installation & Setup

### Option 1: Simple Run (Recommended)
1. **Download/Clone the files** to a directory
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Install Ollama**
   ```bash
   # Visit https://ollama.ai for installation instructions
   ollama serve
   ollama pull llama3.1
   ```
4. **Run the shell**
   ```bash
   # Windows
   fabric.bat
   
   # Or use Python directly
   python run.py
   
   # Linux/Mac
   chmod +x fabric.sh
   ./fabric.sh
   
   # Or use Python directly
   python3 run.py
   ```

### Option 2: Install as Package
```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .

# Then run from anywhere
fabric-shell
```

### Option 3: Direct Python Execution
```bash
python main.py
```

## 📁 Required Directory Structure

Make sure your directory looks like this:
```
ai_fabric_shell/
├── main.py                    # Entry point option 1
├── run.py                     # Entry point option 2 (recommended)
├── fabric.bat                 # Windows batch script
├── fabric.sh                  # Unix shell script
├── setup.py                   # Package installation
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── command_history.json       # Auto-created command history
└── fabric_shell/              # Main package
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── shell.py
    │   └── system_info.py
    ├── models/
    │   ├── __init__.py
    │   └── manager.py
    ├── plugins/
    │   ├── __init__.py
    │   └── manager.py
    ├── rendering/
    │   ├── __init__.py
    │   └── renderer.py
    └── utils/
        ├── __init__.py
        ├── commands.py
        └── extractors.py
```

## 🎮 Usage

### Core Commands

- **`cmd <task>`** - Generate one-liner commands with Y/N/E options
- **`run <plugin>`** - Execute specific plugin  
- **`list [category]`** - Show plugins (optionally by category)
- **`models`** - Show available AI models with capabilities
- **`switch [model]`** - Switch AI model (interactive if no model specified)
- **`status`** - System status with AI analysis
- **`chat`** - AI chat mode with Markdown rendering
- **`troubleshoot <issue>`** - Quick troubleshooting with formatted output
- **`history`** - View command execution history and success patterns
- **`help`** - Show comprehensive help
- **`quit`** - Exit

### ✨ Enhanced Command Flow

When you generate commands, you now get three options:

```bash
fabric(llama3.1)> cmd find large Python files

Generated BASH Command
┌─────────────────────────────────────────┐
│ find . -name "*.py" -size +1M -type f   │
└─────────────────────────────────────────┘

Execute command? [Y]es/[N]o/[E]xplain: e
```

**Y** - Execute the command immediately  
**N** - Cancel and return to prompt  
**E** - Get AI explanation of what the command does

### 📚 Smart Learning System

After successful execution, the system asks for confirmation:

```bash
Output
┌─────────────────────────────────────────┐
│ ./scripts/large_script.py              │
│ ./data/process_data.py                  │
└─────────────────────────────────────────┘

Did this accomplish your goal: 'find large Python files'? [Y]es/[N]o: y
✓ Command saved to history as successful
```

- Commands are only saved to history if they **actually solved your problem**
- Future similar requests will reference successful patterns
- View your history with `history` command

### Examples

```bash
# Generate a command with explanation option
cmd find all python files larger than 1MB
# Choose E to explain, then Y to execute

# Run code review plugin with optimal model selection
run code_review

# List development category plugins
list development

# Switch to code-optimized model
switch codellama

# View your successful command history
history

# Get troubleshooting help with formatted output
troubleshoot docker container won't start
```

## 🔧 Plugin Development

Plugins are YAML files stored in the `plugins/` directory:

```yaml
name: "example_plugin"
description: "Example plugin description"
category: "development"
preferred_model: "codellama"  # Optional: specify preferred model
model_category: "code"        # Optional: specify model category

parameters:
  task:
    prompt: "What task would you like to accomplish?"
    type: "string"

prompt: |
  Help the user accomplish this task: {task}
  
  Provide detailed instructions and code examples.

context: |
  The user is working on: {task}

post_process:
  type: "execute"  # Optional: extract and execute code from response
```

## 🤖 Model Management

The shell automatically detects available Ollama models and provides intelligent recommendations:

- **Code Tasks**: CodeLlama, CodeGemma
- **Analysis**: Mixtral, Llama3.2
- **Quick Commands**: Phi3, Mistral
- **Security**: Mixtral, Llama3.2
- **Performance**: Mixtral, Llama3.2

## 📦 Dependencies

- **rich** - Terminal UI and Markdown rendering
- **ollama** - AI model interaction
- **PyYAML** - Plugin configuration parsing
- **psutil** - System information gathering

## 🏗️ Architecture

### Separation of Concerns

- **`core/shell.py`** - Main application orchestration and command routing
- **`models/manager.py`** - AI model detection, switching, and recommendations
- **`plugins/manager.py`** - Plugin loading, validation, and execution coordination
- **`rendering/renderer.py`** - Markdown rendering and UI formatting
- **`utils/commands.py`** - Enhanced command execution with history tracking and Y/N/E options
- **`utils/extractors.py`** - Text parsing and command extraction from AI responses

### Benefits of Modular Design

- **Maintainable** - Each component has a single responsibility
- **Testable** - Individual modules can be tested in isolation
- **Extensible** - Easy to add new features without affecting existing code
- **Reusable** - Components can be imported and used independently

## ✨ Enhanced Features (New!)

### Y/N/E Command Options

Every generated command now offers three choices:
- **[Y]es** - Execute immediately
- **[N]o** - Cancel execution
- **[E]xplain** - Get detailed AI explanation before deciding

### Smart Command Learning

- **Success Tracking**: Only commands that actually solve problems are saved
- **Pattern Recognition**: Similar tasks reference past successful commands
- **Context Injection**: AI gets historical context for better suggestions
- **User Confirmation**: "Did this work?" ensures quality learning data

### Clean PowerShell Execution

- **No Profile Loading**: PowerShell runs with `-NoProfile` flag
- **No Oh My Posh Errors**: Eliminates theme and prompt customization issues
- **Faster Execution**: Skip profile loading delays
- **Consistent Environment**: Same clean PowerShell every time

### Enhanced Error Handling

- **Technical vs Functional Errors**: Distinguishes between execution errors and wrong results
- **Alternative Approaches**: Offers different methods when commands don't meet expectations
- **Smart Troubleshooting**: Context-aware error analysis and fixes

## 🔄 Migration from Previous Versions

The enhanced version maintains 100% compatibility with existing functionality while adding:

1. **Better Command Interaction** - Y/N/E options for all generated commands
2. **Learning System** - Builds knowledge from successful command patterns
3. **Improved Reliability** - Clean PowerShell execution without profile interference
4. **Enhanced User Experience** - Better confirmation flows and error handling

## 🎨 Enhanced Features Details

### Rich Markdown Rendering

AI responses now support:
- Headers (##, ###, ####)
- Code blocks with syntax highlighting
- Lists (bulleted and numbered)
- **Bold** and *italic* text
- Tables
- Links

### Smart Model Selection

- Plugins automatically use optimal models for their tasks
- Model recommendations based on task complexity and type
- Seamless model switching with capability analysis

### Command History Intelligence

```bash
# View your command history
fabric(llama3.1)> history

Command History (Last 10)
┌────────────────────┬──────────────────────────────┬────────────────────────────────┬───────────┬────────┐
│ Date               │ Task                         │ Command                        │ Shell     │ Status │
├────────────────────┼──────────────────────────────┼────────────────────────────────┼───────────┼────────┤
│ 2025-01-19 10:30   │ find large Python files     │ find . -name "*.py" -size +1M  │ bash      │ ✅     │
│ 2025-01-19 10:25   │ check system memory          │ free -h                        │ bash      │ ✅     │
└────────────────────┴──────────────────────────────┴────────────────────────────────┴───────────┴────────┘
```

## 🚀 Performance Improvements

- **Faster Command Generation**: Historical context helps AI make better suggestions faster
- **Reduced Trial and Error**: Learn from past successes instead of repeating failures
- **Clean Execution Environment**: No profile loading delays or errors
- **Smart Model Routing**: Right model for each task type automatically

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes in the appropriate module
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

MIT License - feel free to use and modify as needed.

---

## 🆕 What's New in This Version

### Version 2.1.0 - Enhanced Command Intelligence

- **🔍 Y/N/E Command Options** - Explain any command before executing
- **📚 Smart Learning System** - Learns from commands that actually work
- **🛡️ Clean PowerShell** - No more Oh My Posh or profile errors
- **🎯 User Confirmation Flow** - Only save commands that solve the actual problem
- **🔄 Alternative Approaches** - Get different methods when first attempt doesn't work
- **📊 Enhanced History** - View and learn from successful command patterns

Ready to automate with enhanced AI intelligence! 🎯