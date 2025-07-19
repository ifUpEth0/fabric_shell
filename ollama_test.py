#!/usr/bin/env python3
"""
Simple script to test Ollama connection and debug issues
"""

import ollama
import sys
from rich.console import Console
from rich.panel import Panel

console = Console()

def test_ollama():
    """
    Test the connection to Ollama and the availability of models.

    This function performs the following steps:
    1. Tests the basic connection to Ollama and retrieves the list of models.
    2. Parses the response to identify available models and prints them.
    3. Attempts to use the first available model to test chat functionality.
    
    Returns:
        bool: True if all tests pass, False otherwise.
    
    Raises:
        Exception: If there is an error during connection or chat testing.
    """

    console.print(Panel("Ollama Connection Test", style="bold blue"))
    
    try:
        console.print("1. Testing basic connection...")
        models_response = ollama.list()
        console.print(f"   Raw response: {models_response}")
        console.print("   ✓ Basic connection successful")
        
        console.print("\n2. Parsing available models...")
        if isinstance(models_response, dict):
            models_list = models_response.get('models', [])
        else:
            # Handle case where response has a 'models' attribute
            if hasattr(models_response, 'models'):
                models_list = models_response.models
            else:
                models_list = models_response
        
        console.print(f"   Models list type: {type(models_list)}")
        console.print(f"   Models list length: {len(models_list) if hasattr(models_list, '__len__') else 'unknown'}")
        
        available_models = []
        for i, model in enumerate(models_list):
            console.print(f"   Model {i}: {type(model)} - {model}")
            
            if hasattr(model, 'model'):
                # Model object with .model attribute
                model_name = model.model
                available_models.append(model_name)
                console.print(f"   Found model: {model_name}")
            elif isinstance(model, dict):
                # Dictionary format
                model_name = model.get('name') or model.get('model') or model.get('id')
                if model_name:
                    available_models.append(model_name)
                    console.print(f"   Found model: {model_name}")
            elif isinstance(model, str):
                # String format
                available_models.append(model)
                console.print(f"   Found model: {model}")
            else:
                console.print(f"   Unknown model format: {type(model)}")
        
        if not available_models:
            console.print("   [red]✗ No models found[/red]")
            console.print("   [yellow]Try: ollama pull llama3.1[/yellow]")
            return False
        
        console.print(f"   ✓ Found {len(available_models)} models")
        
        console.print("\n3. Testing chat functionality...")
        test_model = available_models[0]
        console.print(f"   Using model: {test_model}")
        
        try:
            response = ollama.chat(model=test_model, messages=[{
                'role': 'user',
                'content': 'Respond with just "Connection OK"'
            }])
            
            console.print(f"   Raw chat response type: {type(response)}")
            
            if isinstance(response, dict):
                if 'message' in response and 'content' in response['message']:
                    content = response['message']['content']
                elif 'response' in response:
                    content = response['response']
                elif 'content' in response:
                    content = response['content']
                else:
                    content = str(response)
            elif hasattr(response, 'message') and hasattr(response.message, 'content'):
                # Handle response objects with message.content attribute
                content = response.message.content
            else:
                content = str(response)
            
            console.print(f"   AI Response: {content}")
            console.print("   ✓ Chat test successful")
            
        except Exception as chat_error:
            console.print(f"   [red]✗ Chat test failed: {chat_error}[/red]")
            return False
        
        console.print(f"\n[green]✅ All tests passed! Available models:[/green]")
        for model in available_models:
            console.print(f"   • {model}")
        
        return True
        
    except Exception as e:
        console.print(f"\n[red]✗ Connection failed: {e}[/red]")
        console.print("\n[yellow]Troubleshooting:[/yellow]")
        console.print("1. Check if Ollama is installed: ollama --version")
        console.print("2. Start Ollama service: ollama serve")
        console.print("3. Pull a model: ollama pull llama3.1")
        console.print("4. Test manually: ollama run llama3.1 'hello'")
        return False

if __name__ == "__main__":
    success = test_ollama()
    sys.exit(0 if success else 1)