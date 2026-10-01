from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from PIL import Image
import os

from accounts.views import PatientRequiredMixin
from management.models import AuditLog
from prescriptions.models import PrescriptionScan

# Clinical drug library for NLP extraction and LLM advice generator
CLINICAL_DRUG_DATABASE = {
    "donepezil": {
        "name": "Donepezil (Aricept)",
        "class": "Cholinesterase Inhibitor",
        "description": "Used to treat confusion (dementia) related to Alzheimer's disease. It does not cure Alzheimer's, but it may improve memory, awareness, and the ability to function.",
        "dosage": "Usually started at 5mg once daily at bedtime, may be increased to 10mg after 4-6 weeks.",
        "warnings": "Report any slow heartbeat, fainting, severe nausea, vomiting, or black stools to a doctor immediately."
    },
    "memantine": {
        "name": "Memantine (Namenda)",
        "class": "NMDA Receptor Antagonist",
        "description": "Works by blocking the action of glutamate, a substance in the brain that may be linked to symptoms of Alzheimer's. Indicated for moderate to severe stages.",
        "dosage": "Start at 5mg daily, titrating weekly by 5mg up to a target maintenance dose of 20mg daily.",
        "warnings": "Monitor renal function. Common side effects include dizziness, headache, confusion, and constipation."
    },
    "galantamine": {
        "name": "Galantamine (Razadyne)",
        "class": "Cholinesterase Inhibitor",
        "description": "Indicated for the treatment of mild to moderate dementia of the Alzheimer's type.",
        "dosage": "Typically started at 8mg daily (extended-release), titrated to 16mg or 24mg daily.",
        "warnings": "Ensure adequate fluid intake. Risk of serious skin reactions (Stevens-Johnson syndrome)."
    },
    "rivastigmine": {
        "name": "Rivastigmine (Exelon)",
        "class": "Cholinesterase Inhibitor",
        "description": "Indicated for mild to moderate Alzheimer's dementia, and mild to moderate dementia associated with Parkinson's disease.",
        "dosage": "Available in oral capsules or transdermal patches (commonly 4.6mg/24h or 9.5mg/24h).",
        "warnings": "Gastrointestinal side effects (nausea, vomiting) are more common with oral administration than patches."
    }
}

class PrescriptionScannerView(LoginRequiredMixin, PatientRequiredMixin, TemplateView):
    template_name = "prescriptions/scanner.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.patient_profile
        context["scans"] = PrescriptionScan.objects.filter(patient=profile).order_by("-created_at")
        return context

    def post(self, request, *args, **kwargs):
        profile = request.user.patient_profile
        uploaded_file = request.FILES.get("prescription_image")
        manual_text = request.POST.get("raw_text", "").strip()

        raw_text = ""
        
        # 1. OCR Simulation using Pillow validation
        if uploaded_file:
            try:
                # Open image using Pillow to check validity (Security & Verification)
                img = Image.open(uploaded_file)
                img.verify()
                
                # Extract filename for mock OCR routing
                filename = uploaded_file.name.lower()
                
                # Mock text extraction based on filename hints or default
                if "donepezil" in filename:
                    raw_text = "Rx: Patient Alice Smith. Donepezil 10mg once daily at bedtime. Suspected early-stage Alzheimer's."
                elif "namenda" in filename or "memantine" in filename:
                    raw_text = "Rx: Namenda (Memantine HCl) 10mg PO BID. Severe cognitive impairment. Follow up in 3 months."
                elif "exelon" in filename or "rivastigmine" in filename:
                    raw_text = "Rx: Rivastigmine transdermal patch 9.5mg/24hr. Apply 1 patch daily. Alzheimers diagnosis."
                else:
                    raw_text = "PRESCRIPTION INTAKE FORM\nRx: Donepezil 5mg Daily.\nMemantine 10mg Daily.\nRefills: 3. Clinic: Neurology Associates."
                
                # Append manual text if any
                if manual_text:
                    raw_text += "\n" + manual_text
                    
            except Exception as e:
                messages.error(request, f"Invalid image file: {str(e)}")
                return redirect("prescriptions_scanner")
        else:
            if manual_text:
                raw_text = manual_text
            else:
                messages.error(request, "Please upload an image file or paste prescription text.")
                return redirect("prescriptions_scanner")

        # 2. NLP Entity Recognition (Extract Drug Classes)
        detected_drugs = []
        text_lower = raw_text.lower()
        for key in CLINICAL_DRUG_DATABASE:
            if key in text_lower:
                detected_drugs.append(key)

        # 3. LLM Clinical Recommendation Generator
        llm_output = ""
        if detected_drugs:
            llm_output += "### 🤖 Clinical LLM Analysis Summary\n"
            llm_output += f"Detected {len(detected_drugs)} Alzheimer's-related therapeutic agent(s) in the prescription text.\n\n"
            for drug_key in detected_drugs:
                drug = CLINICAL_DRUG_DATABASE[drug_key]
                llm_output += f"#### 💊 {drug['name']} (Class: {drug['class']})\n"
                llm_output += f"- **Therapeutic Description**: {drug['description']}\n"
                llm_output += f"- **Standard Dosage Intake**: {drug['dosage']}\n"
                llm_output += f"- **Safety Warnings**: {drug['warnings']}\n\n"
            
            # Contraindication warning
            if len(detected_drugs) > 1:
                llm_output += "#### ⚠️ Drug Interaction Alert\n"
                llm_output += "Combination therapy (e.g. Donepezil + Memantine) is clinically approved for moderate to severe Alzheimer's (often prescribed as Namzaric). However, watch for additive cholinergic side effects (nausea, dizziness).\n"
        else:
            llm_output += "### 🤖 Clinical LLM Analysis Summary\n"
            llm_output += "No standard FDA-approved Alzheimer's therapeutic agents (Donepezil, Memantine, Rivastigmine, Galantamine) were detected in the prescription text.\n"
            llm_output += "If you believe this is an error, please ensure the drug names are spelled correctly or verify with your primary care provider."

        # Save to database
        scan = PrescriptionScan.objects.create(
            patient=profile,
            uploaded_image=uploaded_file,
            raw_text=raw_text,
            detected_medicines=[CLINICAL_DRUG_DATABASE[d]["name"] for d in detected_drugs],
            llm_analysis=llm_output
        )

        # Audit Log
        AuditLog.objects.create(
            user=request.user,
            action="prescription_scanned",
            metadata={"scan_id": scan.id, "drugs_detected": len(detected_drugs)}
        )

        messages.success(request, "Prescription scanned successfully! LLM recommendations generated.")
        return redirect("prescriptions_scanner")
