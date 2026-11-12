# Chatbot query interface

The chatbot UI submits a JSON request to `POST /api/v1/chatbot/query/` and renders the response in `templates/components/chatbot.html` using `static/js/chatbot.js`.

## Request

```http
POST /api/v1/chatbot/query/
Content-Type: application/json
X-CSRFToken: <Django CSRF token>

{"message": "How can I book a neurologist?"}
```

`message` must be a non-empty string of at most 1,000 characters.

## Response fields

- `response`: generated reply from the local retrieval-and-response pipeline.
- `intent` and `entities`: detected query intent and terms.
- `retrieved_sources`: clinical knowledge topics and, when relevant, active specialists read from the current doctor directory.
- `actions`: internal links the UI can render as buttons; doctor booking links retain the selected doctor and department.
- `retrieved_at`: server timestamp for the live directory lookup.
- `disclaimer`: informational-use notice.

The API reads only active public doctor listings for live retrieval. It does not retrieve patient records or persist chatbot messages. Clinical knowledge content remains the local content in `core/rag_chatbot.py`; no external LLM or medical-data provider is configured.
