# Kalanaya - Voice-Controlled Calendar Assistant

A voice-controlled calendar assistant that uses speech-to-text (Whisper) and LLM-based intent parsing (Ollama) to manage Google Calendar events through natural language commands.

## Prerequisites

1. **Python 3.9+** installed
2. **Ollama** running locally with `llama3.2:latest` model
   - Install from: https://ollama.ai
   - Run: `ollama pull llama3.2:latest`
   - Ensure Ollama is running on `http://localhost:11434`
3. **Google Calendar API Credentials**
   - Place `google_client_secret.json` in the `credentials/` directory
   - First run will prompt for OAuth authentication

## Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd "C:\Users\vmuno\OneDrive\Desktop\Personal Projects\kalanaya"
   ```

2. **Activate the virtual environment:**
   
   **Windows PowerShell:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   **Windows Command Prompt:**
   ```cmd
   venv\Scripts\activate.bat
   ```

3. **Install dependencies (if not already installed):**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

### Method 1: Install as a Command (Recommended)

Install Kalanaya as a command that you can run from anywhere:

**Step 1: Install the package**
```powershell
# Activate virtual environment first
.\venv\Scripts\Activate.ps1

# Install in development mode
pip install -e .
```

**Step 2: Add to PATH (choose one method)**

**Option A: Using PowerShell script (Recommended)**
```powershell
.\install-command.ps1
```

**Option B: Using Batch script**
```cmd
install-command.bat
```

**Option C: Manual PATH setup**
1. Copy the path to `venv\Scripts` (e.g., `C:\Users\vmuno\OneDrive\Desktop\Personal Projects\kalanaya\venv\Scripts`)
2. Add it to your system PATH:
   - Press `Win + X` → System → Advanced system settings → Environment Variables
   - Under "User variables", select "Path" → Edit → New
   - Paste the path and save

**Step 3: Restart your terminal**

After restarting, you can run `kalanaya` from any directory!

**Note:** The command only works when the virtual environment is activated, OR when you've added `venv\Scripts` to your PATH.

### Method 2: Using Wrapper Scripts

**Option A: Add to PATH (Windows)**

1. Copy `kalanaya.bat` (for Command Prompt) or `kalanaya.ps1` (for PowerShell) to a directory in your PATH
2. Or add the project directory to your PATH:
   ```powershell
   # PowerShell - Add to PATH for current session
   $env:PATH += ";C:\Users\vmuno\OneDrive\Desktop\Personal Projects\kalanaya"
   
   # To make it permanent, add to System Environment Variables
   ```
3. Then run: `kalanaya`

**Option B: Run from project directory**
```bash
# PowerShell
.\kalanaya.ps1

# Command Prompt
kalanaya.bat
```

### Method 3: Run as Python module
```bash
python -m src.main
```

### Method 4: Run directly
```bash
python src/main.py
```

## Usage

### Text Mode (Default)
When you start the application, you'll be in text mode:

```
🎙️  Kalanaya - Voice Calendar Assistant (Text Mode)
============================================================
Type your calendar command. Commands:
  - 'voice' or 'v' to switch to voice mode
  - 'exit' or 'quit' to quit
============================================================

🗣️  You: Schedule a meeting tomorrow at 2 pm
```

### Voice Mode
Type `voice` or `v` to switch to voice mode:

```
🎤  Kalanaya - Voice Calendar Assistant (Voice Mode)
============================================================
Voice commands:
  - Press Enter to start recording
  - Press Enter again to stop recording
  - Type 'text' or 't' to switch to text mode
  - Type 'exit' or 'quit' to quit
============================================================

Press Enter to start recording, or type command: 
🎙️  Press Enter to start recording...
[Press Enter]
🔴 Recording... Press Enter to stop.
[Press Enter when done speaking]
⏹️  Recording stopped.
🔄 Transcribing...
```

### Example Commands

**Create Event:**
- "Schedule a meeting tomorrow at 2 pm"
- "Block 3 to 5 pm today for deep work"
- "Add dentist appointment tomorrow at 10 am"

**List Events:**
- "What do I have today?"
- "Show my calendar for tomorrow"
- "List all events today"

**Update Event:**
- "Move my meeting tomorrow to 3 pm"
- "Reschedule dentist appointment to 11 am tomorrow"

**Delete Event:**
- "Cancel my gym session tomorrow morning"
- "Delete the meeting with Rohan tomorrow"

## Troubleshooting

### Ollama Connection Error
If you see `500 Server Error: Internal Server Error for url: http://localhost:11434/api/generate`:
- Ensure Ollama is running: `ollama serve`
- Verify the model is installed: `ollama list`
- Check if the model exists: `ollama pull llama3.2:latest`

### Google Calendar Authentication
- First run will open a browser for OAuth authentication
- Ensure `google_client_secret.json` is in the `credentials/` directory
- The token will be saved in `credentials/token.pickle` for future runs

### Module Import Errors
If you see `ModuleNotFoundError`:
- Ensure virtual environment is activated
- Install dependencies: `pip install -r requirements.txt`
- Run from project root directory

### Audio/Recording Issues (Voice Mode)
- Ensure microphone permissions are granted
- Check if `sounddevice` is installed: `pip install sounddevice`
- Try text mode if voice mode has issues

## Logs

Application logs are saved in the `logs/` directory:
- `logs/main.log` - Main application logs
- `logs/router.log` - Router and action execution logs

## Project Structure

```
kalanaya/
├── src/
│   ├── main.py          # Main entry point
│   ├── speech/          # Audio recording and transcription
│   ├── intent/          # Intent parsing with Ollama
│   ├── router/          # Intent routing to actions
│   ├── actions/         # Google Calendar API operations
│   └── utils/           # Utilities (logging, validation)
├── config/              # Configuration files
├── credentials/         # OAuth credentials (gitignored)
├── tests/               # Test suites
├── logs/                # Application logs
└── requirements.txt     # Python dependencies
```

## Development

### Installing as a Command

To install Kalanaya as a command-line tool that works from any directory:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install in development mode (editable install)
pip install -e .
```

This will:
- Install Kalanaya as a Python package
- Create a `kalanaya` command that works from any directory
- Keep the code editable (changes are immediately available)

After installation, you can simply run:
```bash
kalanaya
```

from any directory in your terminal!

### Uninstalling

If you installed with `pip install -e .`, you can uninstall with:
```bash
pip uninstall kalanaya
```

### Running Tests
```bash
# Activate venv first
.\venv\Scripts\Activate.ps1

# Run all tests
python tests/actions/test_actions.py
python tests/intent/test_intent.py
python tests/speech/test_speech.py
```

## License

MIT License

Copyright (c) 2025 Kalanaya

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

