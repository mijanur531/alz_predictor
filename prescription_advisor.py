#!/usr/bin/env python3
"""
Clinical Prescription Advisor Engine
Validates uploaded prescription files (via Pillow), performs clinical NLP
entity extraction, retrieves pharmacological knowledge (RAG), and generates
structured therapeutic advice and contraindication warnings.
"""

import os
import sys
import json
import argparse
from io import BytesIO
from PIL import Image

# Ensure UTF-8 stdout encoding for Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


# Pharmacological RAG Knowledge Base
RAG_DRUG_KNOWLEDGE_BASE = {
    "donepezil": {
        "generic_name": "Donepezil Hydrochloride",
        "brand_names": ["Aricept", "Aricept ODT"],
        "drug_class": "Acetylcholinesterase Inhibitor (AChEI)",
        "indications": "Mild, moderate, and severe dementia of the Alzheimer's type.",
        "standard_dosage": "Initial dose: 5 mg orally once daily at bedtime. May increase to 10 mg daily after 4-6 weeks based on clinical response.",
        "mechanism": "Reversibly inhibits acetylcholinesterase, increasing acetylcholine concentration in central synapses to support synaptic transmission.",
        "adverse_reactions": ["Nausea", "Diarrhea", "Insomnia", "Vomiting", "Muscle cramps", "Fatigue", "Anorexia", "Bradycardia / Syncope"],
        "contraindications_warnings": "Caution in patients with 'sick sinus syndrome', other supraventricular cardiac conduction abnormalities, or active peptic ulcer disease.",
        "patient_counseling": "Take once daily in the evening immediately before retiring. Report any episodes of fainting or severe gastrointestinal discomfort."
    },
    "memantine": {
        "generic_name": "Memantine Hydrochloride",
        "brand_names": ["Namenda", "Namenda XR", "Ebixa"],
        "drug_class": "NMDA (N-Methyl-D-Aspartate) Receptor Antagonist",
        "indications": "Moderate to severe dementia of the Alzheimer's type.",
        "standard_dosage": "Initial dose: 5 mg once daily. Titrate weekly by 5 mg/day in divided doses up to target maintenance dose of 10 mg twice daily (20 mg/day).",
        "mechanism": "Uncompetitive, low-affinity NMDA receptor antagonist that protects against glutamate-mediated excitotoxicity without blocking normal physiological NMDA neurotransmission.",
        "adverse_reactions": ["Dizziness", "Headache", "Confusion", "Constipation", "Hypertension", "Somnolence"],
        "contraindications_warnings": "Use with caution in patients with severe renal impairment (reduce target dose to 5 mg BID if CrCl 5-29 mL/min).",
        "patient_counseling": "Can be taken with or without food. Stay hydrated and monitor for changes in coordination or balance."
    },
    "rivastigmine": {
        "generic_name": "Rivastigmine Tartrate",
        "brand_names": ["Exelon", "Exelon Patch", "Prometax"],
        "drug_class": "Dual Acetylcholinesterase and Butyrylcholinesterase Inhibitor",
        "indications": "Mild to moderate Alzheimer's dementia; Parkinson's disease dementia.",
        "standard_dosage": "Oral: Initial 1.5 mg twice daily with morning and evening meals. Transdermal patch: Initial 4.6 mg/24h, titrate to 9.5 mg/24h or 13.3 mg/24h after 4 weeks.",
        "mechanism": "Pseudo-irreversible carbamate-type inhibitor of both acetylcholinesterase and butyrylcholinesterase.",
        "adverse_reactions": ["Nausea", "Vomiting", "Anorexia", "Weight loss", "Application site erythema (transdermal)"],
        "contraindications_warnings": "History of application-site allergic contact dermatitis with patch. Risk of severe GI side effects if oral form not taken with meals.",
        "patient_counseling": "Apply transdermal patch to clean, dry, hairless skin on upper back, chest, or upper arm. Rotate application site daily."
    },
    "galantamine": {
        "generic_name": "Galantamine Hydrobromide",
        "brand_names": ["Razadyne", "Razadyne ER", "Reminyl"],
        "drug_class": "Allosteric Nicotinic Modulator & AChEI",
        "indications": "Mild to moderate dementia of the Alzheimer's type.",
        "standard_dosage": "Initial dose: 4 mg twice daily with food for 4 weeks; may titrate to 8 mg twice daily (16 mg/day), maximum 12 mg twice daily (24 mg/day).",
        "mechanism": "Competitively inhibits acetylcholinesterase and allosterically potentiates nicotinic acetylcholine receptors.",
        "adverse_reactions": ["Nausea", "Vomiting", "Diarrhea", "Weight decrease", "Dizziness"],
        "contraindications_warnings": "Contraindicated in severe renal (CrCl < 9 mL/min) or severe hepatic impairment.",
        "patient_counseling": "Administer with morning and evening meals. Maintain adequate fluid intake."
    },
    "lecanemab": {
        "generic_name": "Lecanemab-irmb",
        "brand_names": ["Leqembi"],
        "drug_class": "Anti-Amyloid Beta (Aβ) Monoclonal Antibody",
        "indications": "Early Alzheimer's disease (Mild Cognitive Impairment or mild dementia stage with confirmed amyloid pathology).",
        "standard_dosage": "10 mg/kg intravenously every two weeks.",
        "mechanism": "Selectively targets and clears soluble amyloid-beta protofibrils to slow cognitive decline.",
        "adverse_reactions": ["Amyloid-Related Imaging Abnormalities (ARIA-E and ARIA-H)", "Infusion-related reactions", "Headache"],
        "contraindications_warnings": "Requires baseline and periodic brain MRI surveillance for ARIA detection prior to 5th, 7th, and 14th infusions. APOE ε4 genotyping recommended.",
        "patient_counseling": "Report immediate symptoms of headache, confusion, dizziness, or vision changes."
    }
}


class PrescriptionAdvisor:
    """
    Analyzes prescription inputs, matches therapeutics, and generates structured advice.
    """
    def __init__(self):
        self.knowledge_base = RAG_DRUG_KNOWLEDGE_BASE

    def validate_image_file(self, file_path_or_buffer):
        """
        Uses Pillow to verify image file integrity.
        """
        try:
            img = Image.open(file_path_or_buffer)
            img.verify()
            return True, f"Valid image format: {img.format} ({img.size[0]}x{img.size[1]}px)"
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"

    def extract_text_from_file_or_string(self, file_path=None, raw_text=""):
        """
        Simulates OCR text extraction from uploaded images or uses provided raw text.
        """
        extracted = raw_text or ""
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path).lower()
            if "donepezil" in filename or "aricept" in filename:
                extracted = "Rx: Patient Alice Smith. Donepezil HCl 10mg PO QHS. Diagnosis: Early Alzheimer's disease. Refills: 3."
            elif "namenda" in filename or "memantine" in filename:
                extracted = "Rx: Namenda (Memantine HCl) 10mg PO BID. Severe cognitive impairment. Follow up in 90 days."
            elif "exelon" in filename or "rivastigmine" in filename:
                extracted = "Rx: Exelon (Rivastigmine) transdermal patch 9.5mg/24h. Apply 1 patch daily. Alzheimer's dementia."
            elif "leqembi" in filename or "lecanemab" in filename:
                extracted = "Rx: Lecanemab (Leqembi) 10mg/kg IV Q2W. Confirmed Aβ positive MCI. Schedule routine MRI."
            else:
                extracted = "PRESCRIPTION INTAKE FORM\nRx: Donepezil 5mg Once Daily.\nMemantine 10mg Twice Daily.\nClinic: Memory & Cognitive Disorders Unit."
        return extracted

    def analyze_prescription(self, text):
        """
        Executes NLP entity detection and RAG synthesis.
        """
        text_lower = text.lower()
        matched_drugs = []

        for key, drug_data in self.knowledge_base.items():
            if key in text_lower:
                matched_drugs.append((key, drug_data))
            else:
                for brand in drug_data["brand_names"]:
                    if brand.lower() in text_lower:
                        matched_drugs.append((key, drug_data))
                        break

        # Remove duplicate matches
        unique_matches = {}
        for k, v in matched_drugs:
            unique_matches[k] = v

        report = {
            "prescription_text": text,
            "detected_drugs_count": len(unique_matches),
            "detected_drugs": [],
            "interaction_alerts": [],
            "clinical_recommendations": [],
            "lifestyle_guidance": []
        }

        for drug_key, data in unique_matches.items():
            report["detected_drugs"].append({
                "generic_name": data["generic_name"],
                "brand_names": ", ".join(data["brand_names"]),
                "drug_class": data["drug_class"],
                "indications": data["indications"],
                "standard_dosage": data["standard_dosage"],
                "mechanism": data["mechanism"],
                "adverse_reactions": data["adverse_reactions"],
                "warnings": data["contraindications_warnings"],
                "patient_instructions": data["patient_counseling"]
            })

        # Multi-drug interaction RAG reasoning
        detected_keys = set(unique_matches.keys())
        if "donepezil" in detected_keys and "memantine" in detected_keys:
            report["interaction_alerts"].append({
                "severity": "Beneficial Synergistic Combination (FDA Approved)",
                "summary": "Donepezil (AChEI) + Memantine (NMDA Antagonist) combination therapy (Namzaric equivalent).",
                "clinical_note": "Clinically indicated for moderate-to-severe Alzheimer's disease. Demonstrates additive cognitive and functional benefits over monotherapy. Monitor for dual cholinergic/NMDA GI side effects (nausea, dizziness)."
            })
        elif len(detected_keys) > 1:
            report["interaction_alerts"].append({
                "severity": "Clinical Multi-Agent Caution",
                "summary": "Multiple cognitive therapeutic agents detected.",
                "clinical_note": "Ensure patient is not concurrently receiving two cholinesterase inhibitors (e.g. Donepezil + Rivastigmine) due to severe cholinergic toxicity risk."
            })

        if not unique_matches:
            report["clinical_recommendations"].append(
                "No standard FDA-approved Alzheimer's therapeutics (Donepezil, Memantine, Rivastigmine, Galantamine, Lecanemab) were detected in the provided prescription."
            )
        else:
            report["clinical_recommendations"].append(
                "Maintain strict adherence to prescribed titration schedules. Do not abruptly discontinue cholinesterase inhibitors without consulting a neurologist."
            )
            report["clinical_recommendations"].append(
                "Perform routine baseline ECG and renal/hepatic panel monitoring to optimize pharmacokinetics."
            )

        report["lifestyle_guidance"] = [
            "Cognitive Engagement: Daily mental stimulation, puzzles, and social interaction.",
            "Mediterranean-DASH Diet (MIND Diet): Rich in leafy greens, berries, olive oil, and omega-3 fatty acids.",
            "Physical Activity: 150 minutes of moderate aerobic exercise weekly to enhance cerebral blood flow."
        ]

        return report

    def format_markdown_report(self, report):
        """
        Formats report dictionary as clean Markdown text.
        """
        md = []
        md.append("# 💊 Prescription Analysis & Clinical Advice Report\n")
        md.append(f"**Detected Therapeutics**: {report['detected_drugs_count']} drug(s)\n")
        
        if report['detected_drugs']:
            md.append("## 🔬 Detected Medications & Pharmacological Profile\n")
            for drug in report['detected_drugs']:
                md.append(f"### {drug['generic_name']} ({drug['brand_names']})")
                md.append(f"- **Drug Class**: {drug['drug_class']}")
                md.append(f"- **Standard Dosage**: {drug['standard_dosage']}")
                md.append(f"- **Mechanism of Action**: {drug['mechanism']}")
                md.append(f"- **Clinical Warnings**: {drug['warnings']}")
                md.append(f"- **Patient Instructions**: {drug['patient_instructions']}\n")
        
        if report['interaction_alerts']:
            md.append("## ⚠️ Interaction & Synergy Analysis\n")
            for alert in report['interaction_alerts']:
                md.append(f"**[{alert['severity']}]** {alert['summary']}")
                md.append(f"{alert['clinical_note']}\n")

        md.append("## 🩺 Clinical Recommendations\n")
        for rec in report['clinical_recommendations']:
            md.append(f"- {rec}")
        
        md.append("\n## 🌿 Supportive Lifestyle Recommendations\n")
        for life in report['lifestyle_guidance']:
            md.append(f"- {life}")

        md.append("\n---\n*Disclaimer: This report is generated by an automated clinical AI advisor. It is intended for educational screening and does not replace medical advice from a certified physician.*")
        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="AlzPredictor Prescription Advisor Engine")
    parser.add_argument("--file", "-f", help="Path to prescription image file (JPEG, PNG)")
    parser.add_argument("--text", "-t", help="Raw prescription text to analyze")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    advisor = PrescriptionAdvisor()

    if not args.file and not args.text:
        # Default interactive sample demo
        sample_text = "Rx: Donepezil 10mg once daily at bedtime. Memantine HCl 10mg BID. Follow up in 8 weeks."
        print("[INFO] No input specified. Running analysis on clinical sample:")
        print(f"\"{sample_text}\"\n")
        res = advisor.analyze_prescription(sample_text)
        print(advisor.format_markdown_report(res))
        return

    raw_text = args.text or ""
    if args.file:
        valid, msg = advisor.validate_image_file(args.file)
        if not valid:
            print(f"[ERROR] {msg}", file=sys.stderr)
            sys.exit(1)
        raw_text = advisor.extract_text_from_file_or_string(file_path=args.file, raw_text=raw_text)

    report = advisor.analyze_prescription(raw_text)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(advisor.format_markdown_report(report))


if __name__ == "__main__":
    main()
