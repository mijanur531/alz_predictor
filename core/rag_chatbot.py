"""Clinical RAG and NLP response engine for local knowledge and live specialists."""

import re
from urllib.parse import urlencode
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

    def doctor_chunks(self, doctors):
        chunks = []
        for doctor in doctors:
            booking_query = urlencode({
                "doctor": doctor.pk,
                "department": doctor.department,
            })
            chunks.append({
                "id": f"doctor_{doctor.pk}",
                "topic": f"{doctor.name} — {doctor.specialty}",
                "keywords": (
                    f"doctor specialist appointment book consultation "
                    f"{doctor.name} {doctor.specialty} {doctor.department}"
                ),
                "content": (
                    f"{doctor.name} is an active {doctor.specialty} specialist in "
                    f"{doctor.department}. Available days: {doctor.available_days}. "
                    f"Available hours: {doctor.available_hours}. "
                    f"Qualification: {doctor.qualification}."
                ),
                "booking_url": f"/appointments/booking/?{booking_query}",
                "doctor_name": doctor.name,
            })
        return chunks

    def retrieve(self, query, top_k=2, additional_chunks=None):
        """
        Retrieves top_k relevant knowledge chunks using cosine similarity.
        """
        chunks = self.chunks
        vectorizer = self.vectorizer
        matrix = self.tfidf_matrix
        if additional_chunks:
            chunks = [*self.chunks, *additional_chunks]
            corpus = [f"{c['topic']}. {c['keywords']}. {c['content']}" for c in chunks]
            vectorizer = TfidfVectorizer(stop_words='english')
            matrix = vectorizer.fit_transform(corpus)

        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, matrix)[0]
        
        ranked_indices = scores.argsort()[::-1]
        results = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0.05:  # Relevance threshold
                chunk = chunks[idx]
                result = {
                    "id": chunk["id"],
                    "topic": chunk["topic"],
                    "content": chunk["content"],
                    "similarity_score": round(float(scores[idx]), 3)
                }
                if "booking_url" in chunk:
                    result["booking_url"] = chunk["booking_url"]
                    result["doctor_name"] = chunk["doctor_name"]
                results.append(result)
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

    def process_query(self, user_message, patient_context=None, doctors=None):
        """
        Retrieves relevant knowledge and composes a response for the user query.
        """
        intent = self.nlp.extract_intent(user_message)
        entities = self.nlp.extract_entities(user_message)
        doctor_chunks = self.retriever.doctor_chunks(doctors or [])
        retrieved_chunks = self.retriever.retrieve(
            user_message,
            top_k=3,
            additional_chunks=doctor_chunks,
        )

        # Context assembly
        rag_context = "\n".join([f"[{c['topic']}]: {c['content']}" for c in retrieved_chunks])
        
        # Clinical response generation
        response_text = ""
        action_buttons = []

        if intent == "book_appointment":
            matching_doctors = [
                chunk for chunk in retrieved_chunks if "booking_url" in chunk
            ]
            if matching_doctors:
                response_text = "These active specialists are listed in the live directory:\n"
                response_text += "\n".join(
                    f"• {chunk['content']}" for chunk in matching_doctors
                )
                action_buttons = [
                    {
                        "label": f"Book {chunk['doctor_name']}",
                        "url": chunk["booking_url"],
                        "type": "primary",
                    }
                    for chunk in matching_doctors
                ]
            else:
                response_text = (
                    "There are no active specialists in the directory right now. "
                    "Please check the directory again later or contact the clinic."
                )
                action_buttons = []
            action_buttons.append({
                "label": "View Specialist Directory",
                "url": "/appointments/booking/",
                "type": "secondary",
            })

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
                {"label": "📅 Book Doctor", "url": "/appointments/booking/", "type": "outline"}
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
