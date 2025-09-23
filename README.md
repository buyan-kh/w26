# Prompt Registry

A comprehensive prompt management system with MCP server integration, automatic grading, and input preprocessing.

## Features

- 🚀 **Package Manager Approach**: Install and manage prompts like npm packages
- 🧠 **MCP Server Integration**: AI copilots can directly access and manage prompts
- 📊 **Automatic Grading**: Grade prompt success and track performance
- 🔄 **Input Preprocessing**: Automatically improve user inputs for better results
- 📈 **Analytics & Optimization**: Track performance and improve prompts over time
- 🔍 **Search & Discovery**: Find the best prompts for your use case

## Quick Start

### Installation

```bash
# Install the prompt registry
pip install -e .

# Install MCP server dependencies
npm install
```

### Basic Usage

```python
from prompt_registry import PromptRegistry

# Initialize registry
registry = PromptRegistry()

# Install prompts
registry.install("examples/basic-prompts")

# Use a prompt
prompt = registry.get("customer-support", "v1.0")
response = llm.generate(prompt, user_input)
```

### MCP Server

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "prompt-registry": {
      "command": "node",
      "args": ["mcp-server/dist/index.js"],
      "env": {
        "PROMPT_REGISTRY_PATH": "./prompts"
      }
    }
  }
}
```

## Project Structure

```
prompt-registry/
├── prompt_registry/          # Python package
├── mcp-server/              # MCP server implementation
├── prompts/                 # Example prompts
├── examples/                # Usage examples
└── tests/                   # Test suite
```

## License

MIT
