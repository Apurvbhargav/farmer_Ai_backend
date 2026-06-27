# Farmer AI Backend

An **Agentic AI-powered farming assistant backend** built to help farmers solve crop-related problems through intelligent multi-turn conversations.
The system uses an **agent-based workflow orchestrated by LangGraph** to analyze queries, gather missing context through follow-up questions, retrieve relevant memory, and generate personalized agricultural recommendations.

## What it Does

* Secure farmer registration and authentication
* Handles **multi-turn conversational workflows**
* Uses **AI agents** for query understanding, context retrieval, and recommendation generation
* Performs **context-aware reasoning** on farming problems
* Dynamically asks **follow-up questions** when information is incomplete
* Generates personalized crop recommendations using LLMs
* Stores farmer context and conversation memory for better future responses

## Tech Stack

* **Backend:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Authentication:** JWT, bcrypt
* **LLM / AI:** Google Gemini
* **Agent Orchestration:** LangGraph
* **Architecture:** Agentic AI Workflow
* **Vector Storage:** pgvector
* **Server:** Uvicorn
