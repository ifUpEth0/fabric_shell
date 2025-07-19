# AI Fabric Shell - Enhanced Edition

A modular, AI-powered command-line automation tool with rich Markdown rendering, smart model switching, and an extensible plugin system.

## 🎯 Features

- **🎨 Rich Markdown Rendering** - AI responses display with proper formatting
- **🤖 Smart Model Management** - Automatic optimal model selection per task
- **📊 Model Recommendations** - Get suggestions for different task types
- **🔧 Plugin System** - YAML-based plugins with model optimization
- **📋 Enhanced UI** - Beautiful tables, syntax highlighting, and progress indicators
- **🚀 Command Generation** - AI-powered one-liner command generation
- **🔍 Smart Troubleshooting** - AI analysis of failed commands and scripts

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
    ├── commands.py            # Command execution utilities
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

- **`cmd <task>`** - Generate one-liner commands
- **`run <plugin>`** - Execute specific plugin  
- **`list [category]`** - Show plugins (optionally by category)
- **`models`** - Show available AI models with capabilities
- **`switch [model]`** - Switch AI model (interactive if no model specified)
- **`status`** - System status with AI analysis
- **`chat`** - AI chat mode with Markdown rendering
- **`troubleshoot <issue>`** - Quick troubleshooting with formatted output

### Examples

```bash
# Generate a command to find large Python files
cmd find all python files larger than 1MB

# Run code review plugin with optimal model selection
run code_review

# List development category plugins
list development

# Switch to code-optimized model
switch codellama

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
- **`utils/commands.py`** - Command execution with proper error handling
- **`utils/extractors.py`** - Text parsing and command extraction from AI responses

### Benefits of Modular Design

- **Maintainable** - Each component has a single responsibility
- **Testable** - Individual modules can be tested in isolation
- **Extensible** - Easy to add new features without affecting existing code
- **Reusable** - Components can be imported and used independently

## 🔄 Migration from Monolithic Version

The refactored version maintains 100% compatibility with the original functionality while providing:

1. **Better Organization** - Related code grouped together
2. **Cleaner Imports** - Clear dependencies between modules
3. **Easier Testing** - Individual components can be unit tested
4. **Improved Maintainability** - Changes isolated to specific areas

## 🎨 Enhanced Features

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
- Model recommendations based on task complexity
- Seamless model switching with capability analysis

### Improved User Experience

- Enhanced welcome messages with Markdown formatting
- Better error handling and troubleshooting workflows
- Comprehensive help system with examples
- Real-time system status with AI analysis

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes in the appropriate module
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

MIT License - feel free to use and modify as needed.