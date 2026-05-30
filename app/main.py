from fastapi import FastAPI

from app.api.routes.auth_routes import (
    router as auth_router
)
from app.api.routes.query_routes import (
    router as query_router
)

app = FastAPI()

app.include_router(auth_router)
app.include_router(query_router)


@app.get("/")
def root():

    return {
        "message": "Backend Running"
    }