# Frontend Auto-modification Agent

## Function Introduction
- Command-line interaction, automatically modify frontend projects
- Call AI interface to automatically generate code and tasks
- Automatically split tasks and check completion status

## Usage
1. Install dependencies
   ```bash
   pip install -r requirements.txt
   # Or directly install dashscope
   pip install dashscope prompt_toolkit
   ```
2. Configure Qwen API Key
   - Set environment variable `DASHSCOPE_API_KEY`, or enter when prompted at runtime
3. Run agent
   ```bash
   python main.py
   ```
4. Enter commands as prompted

## Environment Requirements
- Python 3.8+
- Node.js
- npm

## Project Structure
```
.
├── core/                 # Core module
│   ├── __init__.py
│   ├── application.py    # Main application class
│   ├── ai_interactor.py  # AI interaction module
│   ├── config.py         # Configuration management module
│   ├── file_operator.py  # File operation module
│   └── project_analyzer.py # Project analysis module
├── exceptions/           # Custom exception module
│   ├── __init__.py
│   └── project_exceptions.py
├── utils/                # Utilities module
│   ├── __init__.py
│   └── helpers.py
├── main.py               # Main program entry
├── requirements.txt      # Dependency list
└── README.md             # Documentation
```

## Core Features

### 1. Project Analysis
Automatically analyze frontend project structure and identify key files and directories.

### 2. AI-assisted Development
Interact with AI through ReAct mode to generate high-quality code modification suggestions.

### 3. Safe File Operations
All file operations are verified and automatically backed up to prevent accidental modifications.

### 4. Project Runtime Management
Support one-click dependency installation and project execution.

## Configuration Instructions

### Environment Variables
- `DASHSCOPE_API_KEY`: Qwen API key (required)

### Configuration Items
- `model_name`: AI model name to use, default is `qwen3-coder-plus`
- `max_retries`: Maximum API call retries, default is 3 times
- `timeout`: API call timeout, default is 30 seconds

## Security Features
- All file paths are verified to prevent path traversal attacks
- Automatic backup is created before file modification
- Sensitive operations require user confirmation

## Notes
- Supports all frontend projects
- Requires internet connection to call AI API
- Code auto-write requires manual confirmation
- Project will automatically re-analyze project structure after modifying files

## Troubleshooting

### API Key Issues
Ensure `DASHSCOPE_API_KEY` environment variable is set correctly.

### Dependency Installation Issues
Ensure Node.js and npm are properly installed and added to system PATH.

### File Modification Issues
If the AI-generated code does not meet expectations, you can reject the modification, and the system will automatically clean up related history records.