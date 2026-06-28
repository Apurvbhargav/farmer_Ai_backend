import json
import logging

from langchain_core.prompts import PromptTemplate

from app.services.llm_service import ask_llm

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = PromptTemplate.from_template(
    """
You are an expert agricultural recommendation engine for Indian farmers.

Your job is to generate a practical, safe, farmer-friendly recommendation using ONLY the provided data.

You are given:

1. Current query analysis
2. Retrieved farmer memories
3. Followup answers, if available

Important behavior rules:

* Do NOT ask the farmer any question.
* Do NOT say "please provide more details".
* Do NOT request images.
* Do NOT request followup information.
* Give the best possible recommendation based on available data.
* If information is limited, clearly mention the limitation inside reasoning, but still give a useful recommendation.
* Use retrieved memories only when they are relevant.
* Ignore unrelated memories.
* Never invent crop history, chemical use, disease, pest, weather, or location details.
* Never recommend unsafe chemical usage.
* Avoid exact chemical dosage unless the provided data is enough.
* If pesticide, fungicide, or fertilizer use may be risky, recommend local expert/agriculture officer confirmation.
* Keep the recommendation practical for Indian farming conditions.
* Use simple language that a farmer can understand.
* If the farmer query appears to be in Hindi/Hinglish, answer in simple Hinglish/Hindi style.
* If the farmer query appears to be in English, answer in simple English.

Recommendation quality guidelines:

* Identify the likely problem or farming need.
* Give immediate next steps.
* Mention safe precautions.
* Mention what to observe next.
* Mention when expert help is needed.
* Prefer low-risk agronomic advice when confidence is low.
* Avoid overconfident diagnosis if symptoms are unclear.

Priority rules:

Use "high" when:

* severe disease or pest attack is likely
* crop loss risk is high
* rapid spread is mentioned
* chemical misuse risk is present
* recommendation affects crop safety significantly

Use "medium" when:

* issue needs action but not emergency
* data is incomplete but useful guidance is possible
* symptoms suggest possible disease, pest, nutrient, or water stress

Use "low" when:

* query is general
* risk is low
* recommendation is routine farming guidance

Expert help rules:

Set needs_expert=true when:

* severe disease suspected
* severe pest attack suspected
* crop loss risk is high
* chemical spray decision is uncertain
* available information is too weak for a safe chemical recommendation
* symptoms may have multiple causes

Set needs_expert=false when:

* advice is general, low-risk, or routine
* data is enough for safe non-chemical guidance

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not explain outside JSON.
Do not ask any question.

Output format:

{{
    "problem_summary": "",
    "recommendation": "",
    "priority": "",
    "reasoning": "",
    "needs_expert": false
}}

Field instructions:

problem_summary:
Short summary of the likely issue or need.

recommendation:
Clear practical advice. Do not ask questions. Give actionable steps based on available data.

priority:
One of: low, medium, high

reasoning:
Briefly explain why this recommendation was chosen based on analysis, memories, and followup answers. Mention uncertainty if data is incomplete.

needs_expert:
Boolean true or false.

---

Analysis:
{analysis}

---

Retrieved Memories:
{memories}

---

Followup Answers:
{followup}
"""
)


DEFAULT_RECOMMENDATION = {
    "problem_summary": "Unable to generate summary at this time",
    "recommendation": "Use safe general farming practices and consult a local agriculture expert before applying any chemical treatment.",
    "priority": "medium",
    "reasoning": "The recommendation could not be generated reliably from the available response.",
    "needs_expert": True
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


def normalize_recommendation(recommendation: dict) -> dict:
    normalized = DEFAULT_RECOMMENDATION.copy()
    normalized.update(recommendation)

    allowed_priorities = {"low", "medium", "high"}

    if normalized.get("priority") not in allowed_priorities:
        normalized["priority"] = "medium"

    if not isinstance(normalized.get("needs_expert"), bool):
        normalized["needs_expert"] = True

    for field in ["problem_summary", "recommendation", "reasoning"]:
        if not normalized.get(field):
            normalized[field] = DEFAULT_RECOMMENDATION[field]

    return normalized


def generate_recommendation(
    analysis: dict,
    memories: list,
    followup_answers: dict
):
    prompt = PROMPT_TEMPLATE.format(
        analysis=json.dumps(analysis, ensure_ascii=False),
        memories=json.dumps(memories, ensure_ascii=False),
        followup=json.dumps(followup_answers, ensure_ascii=False)
    )

    response = ask_llm(prompt)

    logger.info(f"Recommendation Response: {response}")

    try:
        recommendation = extract_json(response)
        recommendation = normalize_recommendation(recommendation)

        return recommendation

    except Exception as e:
        logger.error(f"Recommendation parsing failed: {e}")
        logger.error(f"Response content: {response}")

        return DEFAULT_RECOMMENDATION.copy()