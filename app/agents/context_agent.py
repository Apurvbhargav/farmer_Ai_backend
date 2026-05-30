import json
import logging

from app.services.llm_service import ask_llm

from app.services.memory_service import (
    get_recent_memory
)

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """
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

* kal → 1
* parso → 2
* hafte bhar → 7

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

* 0.9+ → very clear query
* 0.7 → mostly understandable
* 0.5 → partially vague
* below 0.5 → highly uncertain

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


def analyze_farmer_query(
    db,
    farmer_id: int,
    query: str
):

    memories = get_recent_memory(
        db=db,
        farmer_id=farmer_id,
        limit=10
    )

    memory_data = []

    for item in memories:

        memory_data.append({
            "event_type": item.event_type,
            "crop_name": item.crop_name,
            "details": item.details
        })

    prompt = PROMPT_TEMPLATE.format(
        memory=json.dumps(memory_data),
        query=query
    )

    response = ask_llm(prompt)

    logger.info(f"Raw LLM Response: {response}")

    try:

        # remove markdown wrappers
        response = response.replace("```json", "")
        response = response.replace("```", "")

        # extract json only
        start = response.find("{")
        end = response.rfind("}") + 1

        response = response[start:end]

        response = response.strip()

        logger.info(f"Cleaned LLM Response: {response}")

        return json.loads(response)

    except Exception as e:

        logger.error(
            f"Failed to parse LLM response as JSON: {e}"
        )

        logger.error(
            f"Response content: {response}"
        )

        return {
            "event_type": "",
            "crop": "",
            "action": "",
            "chemical": "",
            "days_ago": None,
            "missing_fields": [
                "Unable to parse LLM response"
            ],
            "confidence": 0,
            "should_store_memory": False,
            "error": f"JSON parsing failed: {str(e)}"
        }