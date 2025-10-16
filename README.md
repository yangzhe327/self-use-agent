# Frontend Auto-modification Agent

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Usage](#usage)
- [Requirements](#requirements)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Configuration](#configuration)
- [Security](#security)
- [Notes](#notes)
- [Troubleshooting](#troubleshooting)

## Introduction

Frontend Auto-modification Agent is an intelligent CLI tool designed to automate frontend project modifications using AI capabilities. It analyzes project structures, interacts with Qwen AI models, generates code suggestions, and safely applies changes to your project files with user confirmation.

## Features

### 1. Project Analysis
Automatically analyzes frontend project structures and identifies key files and directories.

### 2. AI-assisted Development
Interacts with Qwen AI through ReAct mode to generate high-quality code modification suggestions.

### 3. Safe File Operations
All file operations are verified and automatically backed up to prevent accidental modifications.

### 4. Project Runtime Management
Supports one-click dependency installation and project execution.

## Usage

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

## Requirements

- Python 3.8+
- Node.js
- npm

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
- Project automatically re-analyzes structure after file modifications

## Troubleshooting

### API Key Issues
Ensure `DASHSCOPE_API_KEY` environment variable is set correctly.

### Dependency Installation Issues
Ensure Node.js and npm are properly installed and added to system PATH.

### File Modification Issues
If the AI-generated code does not meet expectations, you can reject the modification, and the system will automatically clean up related history records.