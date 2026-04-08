"""
Translation API — FastAPI application.

Acts as a language-aware middleware layer in front of the FastWorkflow FastAPI.

Flow:
  1. POST /select_language  → store language preference + auto-initialize fastworkflow session
  2. POST /chat             → translate input → call fastworkflow → translate output
  3. GET  /language/{id}   → check selected language for a channel

FastWorkflow FastAPI is expected at FASTWORKFLOW_API_URL (default: http://localhost:8000).
"""

import logging
import os
import traceback

import httpx
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .translator import translate_to_english, translate_from_english
from .session_store import store as session_store

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FASTWORKFLOW_API_URL = os.getenv("FASTWORKFLOW_API_URL", "http://localhost:8000")
SUPPORTED_LANGUAGES = {"hindi", "gujarati", "english"}

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
# No lifespan needed — start.sh guarantees FastWorkflow is ready before
# this process even starts (background FastWorkflow + curl health-check loop).
app = FastAPI(
    title="Translation API",
    description=(
        "Language-aware middleware for the Shopify Support Agent. "
        "Select a language (Hindi or Gujarati), then chat in romanized input — "
        "this API translates to/from English and forwards to the FastWorkflow agent."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class SelectLanguageRequest(BaseModel):
    channel_id: str = Field(..., description="Unique identifier for the user/channel")
    language: str = Field(
        ...,
        description="Language to use: 'hindi' or 'gujarati'",
        examples=["hindi", "gujarati"],
    )


class SelectLanguageResponse(BaseModel):
    status: str
    channel_id: str
    language: str
    message: str


class ChatRequest(BaseModel):
    channel_id: str = Field(..., description="Unique identifier for the user/channel")
    message: str = Field(
        ...,
        description=(
            "User message in romanized Hindi or Gujarati "
            "(e.g. 'mujhe red shoes chahiye' or 'mane red shoes joiye')"
        ),
    )


class ChatResponse(BaseModel):
    channel_id: str
    language: str
    original_message: str
    translated_input: str
    response: str


class LanguageResponse(BaseModel):
    channel_id: str
    language: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _initialize_fastworkflow_session(channel_id: str) -> tuple[str, str]:
    """
    Call POST /initialize on the FastWorkflow API to create a session.

    Returns:
        (access_token, refresh_token)

    Raises:
        HTTPException 502 if the FastWorkflow API is unreachable or returns an error.
    """
    url = f"{FASTWORKFLOW_API_URL}/initialize"
    payload = {"channel_id": channel_id}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
    except httpx.RequestError as exc:
        logger.error(f"Failed to reach FastWorkflow API at {url}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FastWorkflow API is unreachable: {exc}",
        )

    if resp.status_code != 200:
        logger.error(
            f"FastWorkflow /initialize returned {resp.status_code} for channel_id={channel_id}: {resp.text}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FastWorkflow /initialize failed with status {resp.status_code}: {resp.text}",
        )

    data = resp.json()
    access_token = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="FastWorkflow /initialize returned no access_token.",
        )

    return access_token, refresh_token


async def _call_invoke_agent(
    channel_id: str, english_query: str, access_token: str
) -> str:
    """
    Call POST /invoke_agent on the FastWorkflow API and return the response text.

    Uses timeout_seconds=300 because responses can be slow.

    Raises:
        HTTPException on failure.
    """
    url = f"{FASTWORKFLOW_API_URL}/invoke_agent"
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {"user_query": english_query, "timeout_seconds": 300}

    try:
        # httpx timeout must be >= timeout_seconds sent to fastworkflow + buffer
        async with httpx.AsyncClient(timeout=330.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        logger.error(f"Failed to reach FastWorkflow API at {url}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FastWorkflow API is unreachable: {exc}",
        )

    if resp.status_code == 401:
        # Token expired — surface as 401 so client can re-select language
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "FastWorkflow session token has expired. "
                "Please call /select_language again to reinitialize the session."
            ),
        )

    if resp.status_code != 200:
        logger.error(
            f"FastWorkflow /invoke_agent returned {resp.status_code} for channel_id={channel_id}: {resp.text}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FastWorkflow /invoke_agent failed with status {resp.status_code}: {resp.text}",
        )

    data = resp.json()

    # Extract the response text from CommandOutput
    # CommandOutput.command_responses is a list of CommandResponse objects
    command_responses = data.get("command_responses", [])
    if not command_responses:
        return ""

    # Concatenate all response texts
    parts = []
    for cr in command_responses:
        if isinstance(cr, dict) and cr.get("response"):
            parts.append(cr["response"])
    return "\n".join(parts).strip()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["health"])
async def root():
    """Health check / root endpoint."""
    return {
        "service": "Translation API",
        "status": "running",
        "supported_languages": sorted(SUPPORTED_LANGUAGES),
        "fastworkflow_api_url": FASTWORKFLOW_API_URL,
        "docs": "/docs",
    }


@app.post(
    "/select_language",
    response_model=SelectLanguageResponse,
    status_code=status.HTTP_200_OK,
    tags=["session"],
    summary="Select language and initialize session",
)
async def select_language(request: SelectLanguageRequest) -> SelectLanguageResponse:
    """
    Select a language for a channel and auto-initialize a FastWorkflow session.

    - Validates the language (must be 'hindi' or 'gujarati').
    - Calls POST /initialize on the FastWorkflow API to create a session.
    - Stores the JWT tokens and language preference in memory.

    Call this endpoint **before** sending any /chat messages.
    """
    lang = request.language.lower().strip()
    if lang not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported language: {request.language!r}. Supported: {sorted(SUPPORTED_LANGUAGES)}",
        )

    channel_id = request.channel_id
    logger.info(f"[select_language] channel_id={channel_id}, language={lang}")

    # Initialize fastworkflow session
    access_token, refresh_token = await _initialize_fastworkflow_session(channel_id)

    # Persist to session store
    session_store.set_session(
        channel_id=channel_id,
        language=lang,
        access_token=access_token,
        refresh_token=refresh_token,
    )

    logger.info(f"[select_language] Session initialized for channel_id={channel_id}, language={lang}")

    hint = (
        "You can now send messages in English via POST /chat."
        if lang == "english"
        else f"You can now send messages in romanized {lang.capitalize()} via POST /chat."
    )

    return SelectLanguageResponse(
        status="ok",
        channel_id=channel_id,
        language=lang,
        message=f"Language set to '{lang}'. {hint}",
    )


@app.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["chat"],
    summary="Send a message in romanized Hindi/Gujarati",
)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message in romanized Hindi or Gujarati and receive a response in the
    native script of the selected language.

    Flow:
      1. Look up language + JWT token for channel_id.
      2. Translate message → English (via LLM).
      3. Forward to FastWorkflow /invoke_agent (timeout_seconds=300).
      4. Translate English response → native Devanagari Hindi or Gujarati script.
      5. Return translated response.

    Requires /select_language to be called first.
    """
    channel_id = request.channel_id
    session = session_store.get_session(channel_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"No language selected for channel_id={channel_id!r}. "
                "Please call POST /select_language first."
            ),
        )

    language = session["language"]
    access_token = session["access_token"]
    original_message = request.message

    # Prefix every query with the customer's WhatsApp number so the checkout
    # command can extract it from context without asking the user.
    phone_context = f"[Customer's WhatsApp number: {channel_id}]\n"

    logger.info(f"[chat] channel_id={channel_id}, language={language}, message={original_message!r}")

    # -----------------------------------------------------------------------
    # English fast-path: no translation needed — pass straight to FastWorkflow
    # -----------------------------------------------------------------------
    if language == "english":
        try:
            english_response = await _call_invoke_agent(channel_id, phone_context + original_message, access_token)
            logger.info(f"[chat][english] FastWorkflow response: {english_response[:200]!r}...")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"[chat][english] FastWorkflow call failed for channel_id={channel_id}: {exc}")
            traceback.print_exc()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"FastWorkflow agent error: {exc}",
            )

        if not english_response:
            english_response = "I'm sorry, I didn't understand that. Could you please rephrase?"

        return ChatResponse(
            channel_id=channel_id,
            language=language,
            original_message=original_message,
            translated_input=original_message,  # no translation — same as input
            response=english_response,
        )

    # -----------------------------------------------------------------------
    # Hindi / Gujarati path: translate input → FastWorkflow → translate output
    # -----------------------------------------------------------------------

    # Step 1: Translate user input → English
    try:
        english_query = translate_to_english(original_message, language)
        logger.info(f"[chat] Translated input → English: {english_query!r}")
    except Exception as exc:
        logger.error(f"[chat] Input translation failed for channel_id={channel_id}: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate input to English: {exc}",
        )

    # Step 2: Forward to FastWorkflow
    try:
        english_response = await _call_invoke_agent(channel_id, phone_context + english_query, access_token)
        logger.info(f"[chat] English response from FastWorkflow: {english_response[:200]!r}...")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"[chat] FastWorkflow call failed for channel_id={channel_id}: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"FastWorkflow agent error: {exc}",
        )

    # If the agent returned nothing, send a sensible default
    if not english_response:
        english_response = "I'm sorry, I didn't understand that. Could you please rephrase?"

    # Step 3: Translate English response → native script
    try:
        native_response = translate_from_english(english_response, language)
        logger.info(f"[chat] Translated response → {language}: {native_response[:200]!r}...")
    except Exception as exc:
        logger.error(f"[chat] Output translation failed for channel_id={channel_id}: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to translate response to {language}: {exc}",
        )

    return ChatResponse(
        channel_id=channel_id,
        language=language,
        original_message=original_message,
        translated_input=english_query,
        response=native_response,
    )


@app.get(
    "/language/{channel_id}",
    response_model=LanguageResponse,
    status_code=status.HTTP_200_OK,
    tags=["session"],
    summary="Get selected language for a channel",
)
async def get_language(channel_id: str) -> LanguageResponse:
    """
    Return the currently selected language for a channel.

    Returns 404 if /select_language has not been called for this channel_id.
    """
    language = session_store.get_language(channel_id)
    if not language:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No language selected for channel_id={channel_id!r}.",
        )
    return LanguageResponse(channel_id=channel_id, language=language)
