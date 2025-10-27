# Frontend Auto-modification Agent

## Table of Contents
- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Workflow](#workflow)
- [Features](#features)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Configuration](#configuration)
- [Security](#security)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)

## Introduction

Frontend Auto-modification Agent is an intelligent CLI tool designed to automate frontend project modifications using AI capabilities. It analyzes project structures, interacts with Qwen AI models, generates code suggestions, and safely applies changes to your project files with user confirmation.

## Quick Start

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   # Or directly install required packages
   pip install dashscope prompt_toolkit
   ```

2. Configure Qwen API Key
   - Set environment variable `DASHSCOPE_API_KEY`, or enter when prompted at runtime

3. Run agent
   ```bash
   python main.py
   ```

4. Enter your project path when prompted and follow the interactive commands

5. When prompted, choose whether to run the project or skip to modification mode directly

6. Enter your requirements in natural language, review AI-generated suggestions, and confirm changes

## Workflow

The agent follows a structured workflow to ensure safe and effective project modifications:

### 1. Initialization
- Launch the agent with `python main.py`
- Provide the path to your frontend project
- Agent checks if the project can be run and offers to start it

### 2. Project Analysis
- Agent automatically analyzes your project structure
- Identifies key files and directories
- Builds context for AI to understand your project

### 3. Requirement Input
- Enter your modification requirements in natural language
- Examples: "Add a dark mode toggle", "Create a contact form component", "Refactor the navigation menu"

### 4. AI Processing (ReAct Pattern)
The agent uses a ReAct (Reasoning + Action) pattern for processing your requests:
- **Thought**: AI analyzes your requirement and plans the implementation
- **Action**: AI performs actions like reading files or proposing changes
- **Observation**: Agent observes results and adjusts approach if needed
- **Final Answer**: AI presents the complete solution

### 5. Review and Confirmation
- Review AI-generated code suggestions
- Approve or reject proposed changes
- All file modifications require explicit user confirmation

### 6. Implementation
- Approved changes are safely applied to your project
- Project structure is re-analyzed to maintain consistency

### 7. Iteration
- Continue entering new requirements or exit the agent
- Run the updated project to see changes in effect

## Features

### 1. Project Analysis
Automatically analyzes frontend project structures and identifies key files and directories.

### 2. AI-assisted Development
Interacts with Qwen AI through ReAct mode to generate high-quality code modification suggestions.

### 3. Safe File Operations
All file operations are verified to prevent accidental modifications.

### 4. Project Runtime Management
Supports one-click dependency installation and project execution.

## Requirements

- Python 3.8+
- Node.js

## Project Structure

```
.
├── agents/                  # Main application logic
│   ├── __init__.py
│   └── application.py      # Main application class
├── commands/                # Command processing modules
│   ├── __init__.py
│   ├── ai_commands.py      # AI interaction commands
│   └── project_commands.py # Project management commands
├── exceptions/              # Custom exception classes
│   ├── __init__.py
│   └── project_exceptions.py
├── services/                # Business logic services
│   ├── __init__.py
│   ├── ai_interactor.py    # AI interaction service
│   ├── config.py           # Configuration management
│   ├── file_operator.py    # File operations
│   └── project_analyzer.py # Project analysis service
├── utils/                   # Utility functions
│   ├── __init__.py
│   └── helpers.py
├── main.py                  # Main program entry point
├── requirements.txt         # Dependency list
└── README.md                # Documentation
```

## Core Components

### Application Layer (agents/)
The main application controller that orchestrates all functionality.

### Service Layer (services/)
Contains business logic separated into distinct services:
- `ai_interactor.py`: Handles communication with Qwen AI APIs
- `project_analyzer.py`: Analyzes project structures and files
- `file_operator.py`: Manages safe file operations with backups
- `config.py`: Centralized configuration management

### Command Layer (commands/)
Processes user commands and interactions:
- `ai_commands.py`: Handles AI-related operations
- `project_commands.py`: Manages project lifecycle operations

### Utilities (utils/)
Helper functions used throughout the application.

### Exceptions (exceptions/)
Custom exception classes for better error handling.

## Configuration

### Environment Variables
- `DASHSCOPE_API_KEY`: Qwen API key (required)

### Internal Configuration
The application uses sensible defaults that can be customized in the [config.py](services/config.py) file:
- Model name: `qwen3-coder-plus` (default)
- Max retries: 3 attempts
- Timeout: 30 seconds

## Security

- All file paths are verified to prevent path traversal attacks
- Automatic backup is created before file modification
- Sensitive operations require user confirmation
- API keys are managed through secure environment variables

## Notes

- Supports all frontend project types
- Internet connection required for AI API calls
- Code modifications require manual confirmation before applying

## Troubleshooting

### API Key Issues
Ensure `DASHSCOPE_API_KEY` environment variable is set correctly.

### Dependency Installation Issues
Ensure Node.js and npm are properly installed and added to system PATH.

### File Modification Issues
If the AI-generated code does not meet expectations, you can reject the modification, and the system will automatically clean up related history records.