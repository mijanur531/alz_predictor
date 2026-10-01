"""
Clinical RAG + NLP + LLM Chatbot Engine
Provides intelligent conversational assistance for Alzheimer's diagnostics,
pharmacological knowledge, department navigation, and appointment triage.
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# -----------------------------------------------------------------------------
# 1. RAG Clinical Knowledge Base Chunks
# -----------------------------------------------------------------------------
CLINICAL_KNOWLEDGE_CHUNKS = [
    {
        "id": "alz_overview",
        "topic": "Alzheimer's Disease Overview",
        "keywords": "alzheimer dementia cognitive memory neurodegenerative decline brain",
        "content": (
            "Alzheimer's disease is a progressive neurodegenerative disorder characterized by "
            "extracellular amyloid-beta plaque deposition and intracellular neurofibrillary tau tangles. "
            "It primarily affects episodic memory, executive function, visuospatial orientation, and language."
        )
    },
    {
        "id": "alz_stages",
        "topic": "Clinical Stages of Alzheimer's",
        "keywords": "stages mci mild moderate severe preclinical symptoms progression",
        "content": (
            "Stages of cognitive decline: "
            "1. Preclinical: Asymptomatic with positive biomarkers. "
            "2. Mild Cognitive Impairment (MCI): Subtle objective memory/executive deficits without loss of daily functional independence. "
            "3. Mild Dementia: Impaired instrumental activities of daily living (managing finances, navigation). "
            "4. Moderate Dementia: Assistance needed with dressing, bathing; increased disorientation. "
            "5. Severe Dementia: Complete dependence on caregivers; loss of verbal and motor abilities."
        )
    },
    {
        "id": "mmse_scoring",
        "topic": "Mini-Mental State Examination (MMSE) & MoCA",
        "keywords": "mmse score test moca cognitive assessment 30 points interpretation range",
        "content": (
            "The Mini-Mental State Examination (MMSE) is scored out of 30 points: "
            "- 24 to 30: Normal cognition. "
            "- 18 to 23: Mild Cognitive Impairment (MCI) to mild dementia. "
            "- 10 to 17: Moderate cognitive impairment. "
            "- 0 to 9: Severe cognitive impairment. "
            "Our platform's 3D VR spatial memory game maps game telemetry directly to the standard 30-point MMSE scale."
        )
    },
    {
        "id": "med_donepezil",
        "topic": "Donepezil (Aricept) Therapeutics",
        "keywords": "donepezil aricept achei cholinesterase dosage side effects nausea bedtime",
        "content": (
            "Donepezil (Aricept) is a reversible acetylcholinesterase inhibitor indicated for all stages of Alzheimer's. "
            "Initial dose is 5 mg once daily at bedtime, titratable to 10 mg daily after 4-6 weeks. "
            "Common side effects include nausea, diarrhea, insomnia, and bradycardia. Take with food if GI upset occurs."
        )
    },
    {
        "id": "med_memantine",
        "topic": "Memantine (Namenda) Therapeutics",
        "keywords": "memantine namenda nmda antagonist glutamate moderate severe excitotoxicity",
        "content": (
            "Memantine (Namenda) is an uncompetitive NMDA receptor antagonist indicated for moderate-to-severe Alzheimer's disease. "
            "Initial dose is 5 mg once daily, titrated weekly up to target 10 mg twice daily (20 mg/day). "
            "It protects neurons against glutamate-induced excitotoxicity and works synergistically when combined with Donepezil."
        )
    },
    {
        "id": "med_mabs",
        "topic": "Monoclonal Antibodies (Lecanemab / Leqembi)",
        "keywords": "lecanemab leqembi donanemab monoclonal antibody amyloid clearance iv infusion aria",
        "content": (
            "Lecanemab (Leqembi) is an FDA-approved humanized IgG1 monoclonal antibody targeting amyloid-beta protofibrils. "
            "Indicated for early Alzheimer's disease (MCI or mild dementia with confirmed amyloid pathology). "
            "Dosed at 10 mg/kg IV every 2 weeks. Requires brain MRI surveillance for Amyloid-Related Imaging Abnormalities (ARIA)."
        )
    },
    {
        "id": "vr_testing",
        "topic": "3D VR Cognitive & Spatial Memory Testing",
        "keywords": "vr task game 3d memory test navigation spatial maze shapes recall virtual reality",
        "content": (
            "Our platform includes a WebGL 3D cognitive challenge that tests spatial pathfinding and visual shape recall. "
            "The time taken and navigation errors are recorded and automatically mapped to an estimated MMSE cognitive score, "
            "which pre-populates your profile baseline for AI risk evaluation."
        )
    },
    {
        "id": "doctors_booking",
        "topic": "Doctor Appointments & Hospital Specialists",
        "keywords": "doctor appointment book specialist consultation neurology cardiology geriatrics clinic",
        "content": (
            "Our hospital team includes verified board-certified specialists: "
            "- Dr. Aris Thorne & Dr. Haseeb Hossain (Neurology & Cognitive Disorders) "
            "- Dr. Hamida Jannat (Cardiology & Vascular Health) "
            "- Dr. Sarah Mitchell (Geriatrics & Memory Care). "
            "You can book consultations online through our 1-Click Appointment Booking modal on the portal."
        )
    },
    {
        "id": "lifestyle_prevention",
        "topic": "Supportive Lifestyle & Prevention",
        "keywords": "prevention diet lifestyle exercise mind sleep nutrition omega 3 risk reduction",
        "content": (
            "Evidence-based lifestyle interventions to slow cognitive decline: "
            "1. MIND Diet: Leafy greens, berries, nuts, olive oil, and fish. "
            "2. Aerobic Exercise: At least 150 minutes per week. "
            "3. Cognitive Stimulation: Learning new skills, dual-tasking, social connection. "
            "4. Sleep Quality: 7-8 hours nightly to facilitate glymphatic brain clearance of amyloid metabolites."
        )
    }
]


# -----------------------------------------------------------------------------
# 2. RAG Retriever (TF-IDF Vector Space)
# -----------------------------------------------------------------------------
class RAGKnowledgeRetriever:
    def __init__(self, chunks=CLINICAL_KNOWLEDGE_CHUNKS):
        self.chunks = chunks
        self.corpus = [f"{c['topic']}. {c['keywords']}. {c['content']}" for c in chunks]
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus)

    def retrieve(self, query, top_k=2):
        """
        Retrieves top_k relevant knowledge chunks using cosine similarity.
        """
        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        ranked_indices = scores.argsort()[::-1]
        results = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0.05:  # Relevance threshold
                chunk = self.chunks[idx]
                results.append({
                    "id": chunk["id"],
                    "topic": chunk["topic"],
                    "content": chunk["content"],
                    "similarity_score": round(float(scores[idx]), 3)
                })
        return results


# -----------------------------------------------------------------------------
# 3. Clinical NLP Entity & Intent Classifier
# -----------------------------------------------------------------------------
class ClinicalNLPProcessor:
    INTENT_PATTERNS = {
        "book_appointment": r"(book|schedule|appointment|consult|doctor|meet|visit|intake)",
        "vr_task": r"(vr|game|3d|maze|memory test|play|spatial|challenge)",
        "prescription": r"(prescription|drug|medicine|pill|medication|donepezil|memantine|aricept|dosage|scan)",
        "prediction_risk": r"(predict|risk|test|evaluate|probability|normal|mci|dementia|assessment)",
        "mmse_inquiry": r"(mmse|score|moca|points|scale|cognitive score)",
        "symptoms": r"(symptom|memory loss|forgetting|forgetful|confusion|stages|signs)"
    }

    def extract_intent(self, text):
        for intent, pattern in self.INTENT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                return intent
        return "general_clinical_inquiry"

    def extract_entities(self, text):
        entities = []
        text_lower = text.lower()
        if "donepezil" in text_lower or "aricept" in text_lower:
            entities.append("Donepezil (AChEI)")
        if "memantine" in text_lower or "namenda" in text_lower:
            entities.append("Memantine (NMDA Antagonist)")
        if "lecanemab" in text_lower or "leqembi" in text_lower:
            entities.append("Lecanemab (Anti-Amyloid mAb)")
        if "neurology" in text_lower or "neurologist" in text_lower:
            entities.append("Neurology Department")
        if "mmse" in text_lower:
            entities.append("MMSE Assessment")
        return entities


# -----------------------------------------------------------------------------
# 4. Clinical LLM Reasoner & Generator
# -----------------------------------------------------------------------------
class ClinicalLLMChatbot:
    def __init__(self):
        self.retriever = RAGKnowledgeRetriever()
        self.nlp = ClinicalNLPProcessor()

    def process_query(self, user_message, patient_context=None):
        """
        Processes user query through NLP -> RAG -> LLM pipeline.
        """
        intent = self.nlp.extract_intent(user_message)
        entities = self.nlp.extract_entities(user_message)
        retrieved_chunks = self.retriever.retrieve(user_message, top_k=2)

        # Context assembly
        rag_context = "\n".join([f"[{c['topic']}]: {c['content']}" for c in retrieved_chunks])
        
        # Clinical response generation
        response_text = ""
        action_buttons = []

        if intent == "book_appointment":
            response_text = (
                "I would be glad to help you schedule a consultation with our medical team. "
                "Our neurology department features board-certified specialists including Dr. Aris Thorne and Dr. Haseeb Hossain. "
                "You can select your preferred specialist, date, and time slot directly on our booking portal."
            )
            action_buttons = [
                {"label": "📅 Book Appointment Now", "url": "/appointments/book/", "type": "primary"},
                {"label": "👨‍⚕️ View Specialist Directory", "url": "/#doctors-section", "type": "secondary"}
            ]

        elif intent == "vr_task":
            response_text = (
                "Our interactive 3D VR cognitive challenge is designed to evaluate your spatial navigation and object memory recall. "
                "Once you complete the short game, your performance score is automatically mapped to standard MMSE units (0-30) "
                "and populated into your patient diagnostic profile."
            )
            action_buttons = [
                {"label": "🎮 Start 3D VR Memory Game", "url": "/dashboard/vr-test/", "type": "primary"},
                {"label": "📊 Go to Patient Hub", "url": "/dashboard/", "type": "secondary"}
            ]

        elif intent == "prescription":
            response_text = (
                "Our Prescription Scanner uses computer vision image validation, NLP therapeutic extraction, and pharmacological knowledge "
                "to analyze Alzheimer's medications like Donepezil and Memantine, identify drug interactions, and provide clinical dosage guidelines."
            )
            if retrieved_chunks:
                response_text += f"\n\n**Clinical Knowledge Citation**:\n{retrieved_chunks[0]['content']}"
            action_buttons = [
                {"label": "💊 Upload & Scan Prescription", "url": "/prescriptions/scanner/", "type": "primary"}
            ]

        elif intent == "prediction_risk":
            response_text = (
                "Our AI multi-factor diagnostic model evaluates key risk indicators including age, BMI, cognitive MMSE score, "
                "family history, smoking, and physical activity to predict Alzheimer's risk (Normal, MCI, or Dementia) with statistical confidence."
            )
            action_buttons = [
                {"label": "🧠 Run AI Risk Evaluation", "url": "/dashboard/", "type": "primary"},
                {"label": "🎮 Take VR Memory Test First", "url": "/dashboard/vr-test/", "type": "secondary"}
            ]

        else:
            # General clinical inquiry with RAG synthesis
            if retrieved_chunks:
                response_text = (
                    f"Based on our clinical knowledge base regarding **{retrieved_chunks[0]['topic']}**:\n\n"
                    f"{retrieved_chunks[0]['content']}\n\n"
                )
                if len(retrieved_chunks) > 1:
                    response_text += f"**Additional Context ({retrieved_chunks[1]['topic']})**:\n{retrieved_chunks[1]['content']}\n\n"
                response_text += "Would you like to take a 3D cognitive screening test or schedule an appointment with a neurologist?"
            else:
                response_text = (
                    "Hello! I am Dr. Nuvica, your AI Clinical Health Assistant. I can assist you with:\n"
                    "• Explaining Alzheimer's stages, symptoms, and MMSE scores\n"
                    "• Prescription analysis and medication dosage guidance\n"
                    "• Starting our 3D VR spatial memory challenge\n"
                    "• Scheduling consultations with verified medical specialists\n\n"
                    "How may I help you today?"
                )
            
            action_buttons = [
                {"label": "🧠 Run Risk Check", "url": "/dashboard/", "type": "primary"},
                {"label": "🎮 Play 3D VR Test", "url": "/dashboard/vr-test/", "type": "secondary"},
                {"label": "📅 Book Doctor", "url": "/appointments/book/", "type": "outline"}
            ]

        return {
            "query": user_message,
            "intent": intent,
            "entities": entities,
            "retrieved_sources": [c["topic"] for c in retrieved_chunks],
            "response": response_text,
            "actions": action_buttons,
            "disclaimer": "AI Medical Assistant is for informational and triage guidance only. Consult a physician for official medical diagnosis."
        }


# Global instance
clinical_chatbot = ClinicalLLMChatbot()
