from sqlalchemy import text

from app.services.embedding_service import (
    generate_embedding
)

SIMILARITY_THRESHOLD = 0.60


def retrieve_relevant_memories(
    db,
    farmer_id: int,
    query: str,
    crop_name: str = None,
    limit: int = 5
):

    query_embedding = generate_embedding(
        query
    )

    if crop_name:

        sql = text("""
            SELECT
                id,
                memory_text,
                crop_name,
                event_type,

                1 - (
                    embedding <=> CAST(:embedding AS vector)
                ) AS similarity

            FROM farmer_memory_events

            WHERE farmer_id = :farmer_id
              AND crop_name = :crop_name
              AND embedding IS NOT NULL

            ORDER BY embedding <=> CAST(:embedding AS vector)

            LIMIT 20
        """)

        params = {
            "embedding": str(query_embedding),
            "farmer_id": farmer_id,
            "crop_name": crop_name
        }

    else:

        sql = text("""
            SELECT
                id,
                memory_text,
                crop_name,
                event_type,

                1 - (
                    embedding <=> CAST(:embedding AS vector)
                ) AS similarity

            FROM farmer_memory_events

            WHERE farmer_id = :farmer_id
              AND embedding IS NOT NULL

            ORDER BY embedding <=> CAST(:embedding AS vector)

            LIMIT 20
        """)

        params = {
            "embedding": str(query_embedding),
            "farmer_id": farmer_id
        }

    result = db.execute(
        sql,
        params
    )

    memories = [
        dict(row._mapping)
        for row in result
    ]

    filtered = []

    for memory in memories:

        similarity = memory.get(
            "similarity",
            0
        )

        if similarity >= SIMILARITY_THRESHOLD:

            filtered.append(memory)

    return filtered[:limit]