def build_memory_text(
    crop_name: str,
    event_type: str,
    details: dict,
    source_query: str = None
):

    parts = []

    if crop_name:

        parts.append(
            f"Farmer reported crop {crop_name}."
        )

    if event_type:

        parts.append(
            f"Agricultural event type is {event_type}."
        )

    for key, value in details.items():

        if value is not None:

            parts.append(
                f"{key} is {value}."
            )

    if source_query:

        parts.append(
            f"Original farmer statement: {source_query}"
        )

    return " ".join(parts)