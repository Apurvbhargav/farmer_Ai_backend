FIELD_QUESTIONS = {

    "crop_stage":
        "What is the current growth stage of the crop?",

    "affected_area":
        "Is the issue affecting the whole field or only some area?",

    "fertilizer_type":
        "Which fertilizer or chemical was used?",

    "image_required":
        "Can you upload a clear image of the crop issue?",

    "irrigation_status":
        "When was the field last irrigated?",

    "disease_spread":
        "Is the issue spreading quickly in the field?",

    "spot_details":
        "What kind of spots or symptoms are visible on the crop?",

    "severity":
        "How severe is the problem right now?",

    "soil_condition":
        "What is the current soil condition?"
}


def generate_followup_questions(
    analysis: dict
):

    missing_fields = analysis.get(
        "missing_fields",
        []
    )

    confidence = analysis.get(
        "confidence",
        0
    )

    questions = []

    for field in missing_fields:

        question = FIELD_QUESTIONS.get(field)

        if question:
            questions.append(question)

    needs_followup = False

    if missing_fields:
        needs_followup = True

    elif confidence < 0.75:
        needs_followup = True

        questions.append(
            "Please explain the farming issue in more detail."
        )

    return {

        "needs_followup": needs_followup,

        "followup_questions": questions,

        "reason":
            "Additional agricultural context required"
            if needs_followup
            else
            "Enough context available"
    }