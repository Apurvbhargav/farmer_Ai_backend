import json
import logging

from langchain_core.prompts import PromptTemplate

from app.services.llm_service import ask_llm
from app.services.retrieval_service import retrieve_relevant_memories

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = PromptTemplate.from_template(
    """
You are an advanced multilingual agricultural intelligence system designed for Indian farmers.

Your job is to understand farmer intent from highly unstructured natural language.

Farmers may speak in:

* Hindi
* English
* Hinglish
* Khadi Boli
* Haryanvi
* Western UP dialect
* Rural slang
* Broken sentences
* Misspelled crop/chemical names
* Voice-to-text converted text
* Extremely vague farming descriptions

You must intelligently infer meaning from context.

You are given:

1. Current farmer query
2. Farmer historical memory

Use farmer memory ONLY if relevant to the current query.

Examples:

* If farmer previously discussed wheat and now says "ab dawa daal du kya", infer context carefully.
* If memory is unrelated, ignore it.
* Never hallucinate facts not supported by query or memory.

Your goal is to extract structured agricultural intelligence.

---

STRICT OUTPUT RULES:

* Return ONLY valid JSON
* DO NOT explain anything
* DO NOT use markdown
* DO NOT use ```json
* DO NOT add comments
* DO NOT add extra text before or after JSON
* Missing unknown values should be null
* missing_fields must always be an array
* confidence must be between 0 and 1

---

Understand and extract:

1. event_type

Type of agricultural event.

Possible examples:

* irrigation
* fertilizer
* pesticide_spray
* weed_issue
* disease_observation
* pest_attack
* sowing
* harvesting
* soil_issue
* weather_concern
* symptom_observation
* recommendation_request
* growth_issue
* market_query
* unknown

---

2. crop

Extract crop name if mentioned or strongly implied.

Examples:

* wheat
* paddy
* sugarcane
* mustard
* cotton
* maize
* potato

If unclear:
null

---

3. action

Main farmer intent/action.

Examples:

* spray
* irrigation
* fertilizer_application
* diagnosis
* recommendation
* inspection
* pesticide_use
* weed_control
* disease_control

---

4. chemical

Extract:

* fertilizer
* pesticide
* fungicide
* insecticide
* local spoken chemical names

Examples:

* urea
* dap
* npk
* zinc
* potash
* monocrotophos

If not mentioned:
null

---

5. days_ago

Extract relative agricultural timing.

Examples:

* "2 din pehle"
* "kal"
* "pichhle hafte"
* "10 din ho gaye"

Convert into integer days if possible.

Examples:

* kal -> 1
* parso -> 2
* hafte bhar -> 7

If unclear:
null

---

6. missing_fields

Determine which critical fields are still needed for better recommendations.

Examples:

* affected_area
* leaf_color
* rainfall
* soil_type
* irrigation_status
* disease_spread
* pesticide_history
* crop_stage
* image_required

If enough information exists:
[]

---

7. confidence

Confidence score of extraction.

Guidelines:

* 0.9+ -> very clear query
* 0.7 -> mostly understandable
* 0.5 -> partially vague
* below 0.5 -> highly uncertain

---

8. should_store_memory

Return true if:

* information may help future farming decisions
* contains crop history
* irrigation history
* spray history
* disease history
* fertilizer usage
* weather impact
* recurring issue

Else false.

---

RESPONSE FORMAT:

{{
    "event_type": "",
    "crop": "",
    "action": "",
    "chemical": "",
    "days_ago": null,
    "missing_fields": [],
    "confidence": 0,
    "should_store_memory": false
}}

---

Farmer Memory:
{memory}

---

Farmer Query:
{query}
"""
)


DEFAULT_ANALYSIS = {
    "event_type": "unknown",
    "crop": None,
    "action": None,
    "chemical": None,
    "days_ago": None,
    "missing_fields": [],
    "confidence": 0,
    "should_store_memory": False
}


def extract_json(response: str) -> dict:
    if not response:
        raise ValueError("Empty LLM response")

    cleaned_response = response.replace("```json", "")
    cleaned_response = cleaned_response.replace("```", "")
    cleaned_response = cleaned_response.strip()

    start = cleaned_response.find("{")
    end = cleaned_response.rfind("}") + 1

    if start == -1 or end == 0:
        raise ValueError("No JSON object found in LLM response")

    json_text = cleaned_response[start:end]

    return json.loads(json_text)


def normalize_analysis(analysis: dict) -> dict:
    normalized = DEFAULT_ANALYSIS.copy()
    normalized.update(analysis)

    if not isinstance(normalized.get("missing_fields"), list):
        normalized["missing_fields"] = []

    try:
        normalized["confidence"] = float(normalized.get("confidence", 0))
    except (TypeError, ValueError):
        normalized["confidence"] = 0

    normalized["confidence"] = max(0, min(1, normalized["confidence"]))

    if not isinstance(normalized.get("should_store_memory"), bool):
        normalized["should_store_memory"] = False

    return normalized


def analyze_farmer_query(
    db,
    farmer_id: int,
    query: str
):
    memories = retrieve_relevant_memories(
        db=db,
        farmer_id=farmer_id,
        query=query,
        limit=5
    )

    memory_data = [
        item["memory_text"]
        for item in memories
    ]

    prompt = PROMPT_TEMPLATE.format(
        memory=json.dumps(memory_data, ensure_ascii=False),
        query=query
    )

    response = ask_llm(prompt)

    logger.info(f"Raw LLM Response: {response}")

    try:
        analysis = extract_json(response)
        analysis = normalize_analysis(analysis)

        logger.info(f"Parsed Analysis: {analysis}")

        return {
            "analysis": analysis,
            "retrieved_memories": memories
        }

    except Exception as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response content: {response}")

        fallback_analysis = DEFAULT_ANALYSIS.copy()
        fallback_analysis["missing_fields"] = [
            "Unable to parse LLM response"
        ]
        fallback_analysis["error"] = f"JSON parsing failed: {str(e)}"

        return {
            "analysis": fallback_analysis,
            "retrieved_memories": memories
        }