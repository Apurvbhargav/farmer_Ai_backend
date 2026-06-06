import json
import logging

from app.services.llm_service import ask_llm

logger = logging.getLogger(__name__)


PROMPT_TEMPLATE = """
You are an advanced agricultural recommendation engine.

Your job is to generate practical farming recommendations using:

1. Current query analysis
2. Relevant farmer memories
3. Followup answers

Use retrieved memories only if relevant.

Never hallucinate.

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not explain outside JSON.

Output format:

{{
    "problem_summary": "",
    "recommendation": "",
    "priority": "",
    "reasoning": "",
    "needs_expert": false
}}

Priority values:

- low
- medium
- high

Set needs_expert=true only when:

- severe disease suspected
- severe pest attack suspected
- crop loss risk is high
- information is insufficient for safe recommendation

Analysis:
{analysis}

Retrieved Memories:
{memories}

Followup Answers:
{followup}
"""


def generate_recommendation(
    analysis: dict,
    memories: list,
    followup_answers: dict
):

    prompt = PROMPT_TEMPLATE.format(
        analysis=json.dumps(analysis),
        memories=json.dumps(memories),
        followup=json.dumps(followup_answers)
    )

    response = ask_llm(prompt)

    logger.info(
        f"Recommendation Response: {response}"
    )

    try:

        response = response.replace(
            "```json",
            ""
        )

        response = response.replace(
            "```",
            ""
        )

        start = response.find("{")
        end = response.rfind("}") + 1

        response = response[start:end]

        response = response.strip()

        return json.loads(response)

    except Exception as e:

        logger.error(
            f"Recommendation parsing failed: {e}"
        )

        logger.error(
            f"Response content: {response}"
        )

        return {

            "problem_summary":
                "Unable to generate recommendation",

            "recommendation":
                "Please try again later",

            "priority":
                "medium",

            "reasoning":
                "Recommendation generation failed",

            "needs_expert":
                False
        }