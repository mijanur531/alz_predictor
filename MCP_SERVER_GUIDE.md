# 🤖 Model Context Protocol (MCP) Server Integration Guide

This guide explains how to connect and run the **AlzPredictor MCP Server** (`mcp_server.py`) with MCP-compliant AI assistants such as **Claude Desktop**, **Cursor**, **Antigravity**, or any custom LLM client.

---

## 🛠️ Overview of Available Clinical MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `assess_alzheimers_risk` | `age`, `gender`, `education_level`, `bmi`, `smoking`, `cognitive_score`, `family_history`, `physical_activity` | Runs ML/DL inference to predict risk (Normal, MCI, Dementia) with probability percentage. |
| `scan_prescription_text` | `text` | Performs NLP drug matching for Alzheimer's therapeutics and generates interaction warnings. |
| `list_specialist_doctors` | `department` (optional) | Retrieves verified medical specialists, qualifications, and consultation hours. |
| `convert_vr_score_to_mmse` | `game_score`, `errors`, `time_taken` | Maps 3D VR cognitive game telemetry to clinical MMSE scale. |

---

## 🚀 Step 1: Verification & Running Locally

Test the MCP server directly from the command line:

```bash
# Test initialization
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}' | .\venv\Scripts\python mcp_server.py

# Test tools list
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}' | .\venv\Scripts\python mcp_server.py

# Test Alzheimer's risk assessment
echo '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "assess_alzheimers_risk", "arguments": {"age": 75, "gender": "Female", "education_level": "High School", "bmi": 24.2, "smoking": false, "cognitive_score": 19.5, "family_history": true, "physical_activity": 1.5}}}' | .\venv\Scripts\python mcp_server.py
```

---

## ⚙️ Step 2: Configure with Claude Desktop

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "alz-predictor": {
      "command": "C:\\Users\\HP\\.gemini\\antigravity\\scratch\\alz_predictor\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\HP\\.gemini\\antigravity\\scratch\\alz_predictor\\mcp_server.py"
      ],
      "env": {
        "DJANGO_SETTINGS_MODULE": "alz_predictor.settings.dev",
        "PYTHONPATH": "C:\\Users\\HP\\.gemini\\antigravity\\scratch\\alz_predictor"
      }
    }
  }
}
```

---

## 💡 Step 3: Example Prompts for the AI Assistant

Once connected, you can ask your AI:
1. *"Can you evaluate the Alzheimer's risk for a 72-year-old male with an MMSE score of 21 and family history?"*
2. *"I received a prescription with Donepezil 10mg and Memantine 10mg. Can you check for clinical precautions?"*
3. *"Show me the available neurology specialists for an intake appointment."*
4. *"A patient scored 85 on the VR memory task. What is their estimated MMSE score?"*
