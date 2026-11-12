#!/usr/bin/env python3
"""
AlzPredictor MCP Server
Model Context Protocol server for clinical Alzheimer's assessment,
prescription analysis, doctor consultation, and cognitive VR mapping.
"""
import sys
import json
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alz_predictor.settings.dev')
django.setup()

from core.engine import predictor_engine
from prescriptions.views import CLINICAL_DRUG_DATABASE
from appointments.models import Doctor, Appointment
from accounts.models import User, PatientProfile
from patients.models import PredictionRecord, VRTestRecord

TOOLS = [
    {
        "name": "assess_alzheimers_risk",
        "description": "Evaluates patient clinical & lifestyle metrics using the machine learning inference model to predict Alzheimer's risk class (Normal, MCI, Dementia) with confidence probability.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "age": {"type": "integer", "description": "Patient age in years (e.g. 72)"},
                "gender": {"type": "string", "enum": ["Male", "Female", "Other"]},
                "education_level": {"type": "string", "enum": ["High School", "Bachelor's", "Master's", "PhD"]},
                "bmi": {"type": "number", "description": "Body Mass Index (e.g. 24.5)"},
                "smoking": {"type": "boolean", "description": "Whether patient is an active smoker"},
                "cognitive_score": {"type": "number", "description": "Cognitive MMSE score (0.0 to 30.0)"},
                "family_history": {"type": "boolean", "description": "Family history of Alzheimer's disease"},
                "physical_activity": {"type": "number", "description": "Physical activity in hours/week"}
            },
            "required": ["age", "gender", "education_level", "bmi", "smoking", "cognitive_score", "family_history", "physical_activity"]
        }
    },
    {
        "name": "scan_prescription_text",
        "description": "Analyzes clinical prescription text using NLP drug matching and generates therapeutic precautions, standard dosages, and interaction warnings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Raw prescription text or OCR transcript (e.g. 'Rx: Donepezil 10mg daily at bedtime')"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "list_specialist_doctors",
        "description": "Lists available medical specialists, departments, ratings, and consultation hours.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "department": {"type": "string", "description": "Optional filter by department (e.g. 'Neurology', 'Cardiology', 'Geriatrics')"}
            }
        }
    },
    {
        "name": "convert_vr_score_to_mmse",
        "description": "Converts 3D VR cognitive game telemetry (completion time, errors, score 0-100) to standard 30-point MMSE score with clinical interpretation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "game_score": {"type": "number", "description": "VR game score from 0.0 to 100.0"},
                "errors": {"type": "integer", "description": "Number of navigation/recall errors"},
                "time_taken": {"type": "number", "description": "Time taken in seconds"}
            },
            "required": ["game_score"]
        }
    }
]

def handle_assess_alzheimers_risk(arguments):
    res = predictor_engine.predict(arguments)
    return {
        "prediction_class": res["class"],
        "probability": res["probability"],
        "confidence_percentage": f"{round(res['probability'] * 100, 1)}%",
        "model_version": res["model_version"],
        "disclaimer": "This is an academic ML screening tool and does not replace certified clinical neurology diagnosis."
    }

def handle_scan_prescription(arguments):
    text = arguments.get("text", "").lower()
    detected = []
    for key, val in CLINICAL_DRUG_DATABASE.items():
        if key in text:
            detected.append(val)
    
    analysis = {
        "detected_count": len(detected),
        "detected_medicines": [d["name"] for d in detected],
        "details": detected,
        "recommendations": "Combination therapy approved for moderate-to-severe AD. Monitor for cholinergic side effects." if len(detected) > 1 else "Standard single-agent therapy."
    }
    return analysis

def handle_list_doctors(arguments):
    dept = arguments.get("department")
    qs = Doctor.objects.filter(is_active=True)
    if dept:
        qs = qs.filter(department__icontains=dept)
    doctors = []
    for doc in qs[:10]:
        doctors.append({
            "id": doc.id,
            "name": doc.name,
            "specialty": doc.specialty,
            "department": doc.department,
            "rating": doc.rating,
            "consultation_fee": f"${doc.consultation_fee}",
            "available_hours": doc.available_hours,
            "phone": doc.phone
        })
    return {"doctors": doctors, "total": len(doctors)}

def handle_convert_vr_score(arguments):
    score = float(arguments.get("game_score", 100.0))
    mmse = round((score / 100.0) * 30.0, 1)
    
    if mmse >= 25:
        status = "Normal Cognitive Function"
    elif mmse >= 18:
        status = "Mild Cognitive Impairment (MCI) Indication"
    else:
        status = "Severe Cognitive Impairment Indication"
        
    return {
        "vr_score": score,
        "mapped_mmse": mmse,
        "clinical_category": status,
        "suggested_next_step": "Run full ML/DL multi-factor prediction with MMSE=" + str(mmse)
    }

def process_request(request):
    req_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }
    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        try:
            if tool_name == "assess_alzheimers_risk":
                result = handle_assess_alzheimers_risk(args)
            elif tool_name == "scan_prescription_text":
                result = handle_scan_prescription(args)
            elif tool_name == "list_specialist_doctors":
                result = handle_list_doctors(args)
            elif tool_name == "convert_vr_score_to_mmse":
                result = handle_convert_vr_score(args)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Tool '{tool_name}' not found"}
                }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(e)}
            }
    elif method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "alz-predictor-mcp", "version": "1.0.0"}
            }
        }
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not supported"}
        }

def main():
    """Main stdio loop for MCP server."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = process_request(req)
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == '__main__':
    main()
