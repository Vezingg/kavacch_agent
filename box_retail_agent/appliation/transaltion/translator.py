"""
Translation logic for the Translation API.

Handles two directions:
  1. Romanized Hindi/Gujarati → English  (incoming user message)
  2. English → Native script Hindi/Gujarati  (outgoing response)

Uses openai/gpt-4.1 via litellm.
"""

import os

from litellm import completion

# ---------------------------------------------------------------------------
# OpenAI API key (set OPENAI_API_KEY as a Cloud Run / Docker environment variable)
# ---------------------------------------------------------------------------
_API_KEY = os.environ.get("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# LLM model used for all translation calls
# ---------------------------------------------------------------------------
_MODEL = "openai/gpt-4.1"



# ---------------------------------------------------------------------------
# Direction 1 : Romanized input → English
# ---------------------------------------------------------------------------

def _romanized_hindi_to_english(text: str) -> str:
    """
    Translates romanized Hindi (Hindi meaning written in English/Latin letters,
    e.g. 'mujhe red shoes chahiye') into proper English.
    """
    response = completion(
        model=_MODEL,
        api_key=_API_KEY,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator specializing in Hindi to English translation. "
                    "The user will send you text written in Hindi language using English/Latin letters "
                    "(romanized Hindi), for example: 'aap kaise hain', 'mujhe red shoes chahiye', "
                    "'kya yeh available hai'. "
                    "Your job is to translate the meaning accurately into proper, natural, fluent English. "
                    "Output only the English translation — no explanations, no notes, just the translated text."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )
    return response.choices[0].message.content.strip()


def _romanized_gujarati_to_english(text: str) -> str:
    """
    Translates Gujarati (either Gujarati script or romanized in English letters)
    into proper English.
    """
    response = completion(
        model=_MODEL,
        api_key=_API_KEY,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator specializing in Gujarati to English translation. "
                    "The user will send you text written in the Gujarati language. "
                    "The text may be in Gujarati script (e.g., 'તમે કેમ છો') or romanized using English "
                    "letters (e.g., 'tame kem cho'). "
                    "Your job is to translate the meaning accurately into proper, natural, fluent English. "
                    "Output only the English translation — no explanations, no notes, just the translated text."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )
    return response.choices[0].message.content.strip()


def translate_to_english(text: str, language: str) -> str:
    """
    Translate user input (romanized Hindi or Gujarati) into English.

    Args:
        text: The incoming message from the user.
        language: "hindi" or "gujarati"

    Returns:
        English translation of the text.

    Raises:
        ValueError: If language is not supported.
    """
    language = language.lower().strip()
    if language == "hindi":
        return _romanized_hindi_to_english(text)
    elif language == "gujarati":
        return _romanized_gujarati_to_english(text)
    else:
        raise ValueError(f"Unsupported language for input translation: {language!r}. Use 'hindi' or 'gujarati'.")


# ---------------------------------------------------------------------------
# Direction 2 : English → Native script (Devanagari Hindi / Gujarati script)
# ---------------------------------------------------------------------------

def _english_to_hindi_devanagari(text: str) -> str:
    """
    Translates English text into Hindi written in Devanagari script (हिंदी).
    Brand names, product names, prices ($), model numbers, sizes stay in English.
    All formatting (bullets, bold, dashes, line breaks) is preserved.
    """
    response = completion(
        model=_MODEL,
        api_key=_API_KEY,
        max_tokens=8192,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a translator that converts English text into Hindi written in Devanagari script. "
                    "Devanagari script is the native script used to write Hindi (e.g., नमस्ते, आप कैसे हैं). "
                    "Translate the full meaning into Hindi and write it using Devanagari characters — "
                    "do NOT use Roman/English letters for Hindi words. "
                    "Important rules:\n"
                    "1. Keep brand names, product names, model numbers, prices ($), sizes, and any ALL-CAPS "
                    "labels exactly as-is in English.\n"
                    "2. Translate only the natural language sentences and descriptions into Devanagari Hindi.\n"
                    "3. Preserve all original formatting: bullet points (•), bold markers (**), dashes (–), "
                    "and line breaks.\n"
                    "4. Use only Devanagari script for all Hindi words — never use Roman letters for Hindi.\n"
                    "Output only the converted text, no explanations."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError(
            f"Model returned an empty response for Hindi translation. Raw response: {response}"
        )
    return content.strip()


def _english_to_gujarati_script(text: str) -> str:
    """
    Translates English text into Gujarati written in Gujarati script (ગુજરાતી).
    Brand names, product names, prices ($), model numbers, sizes stay in English.
    All formatting (bullets, bold, dashes, line breaks) is preserved.
    """
    response = completion(
        model=_MODEL,
        api_key=_API_KEY,
        max_tokens=8192,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a translator that converts English text into Gujarati written in Gujarati script. "
                    "Gujarati script is the native script used to write Gujarati (e.g., નમસ્તે, તમે કેમ છો). "
                    "Translate the full meaning into Gujarati and write it using Gujarati characters — "
                    "do NOT use Roman/English letters for Gujarati words. "
                    "Important rules:\n"
                    "1. Keep brand names, product names, model numbers, prices ($), sizes, and any ALL-CAPS "
                    "labels exactly as-is in English.\n"
                    "2. Translate only the natural language sentences and descriptions into Gujarati script.\n"
                    "3. Preserve all original formatting: bullet points (•), bold markers (**), dashes (–), "
                    "and line breaks.\n"
                    "4. Use only Gujarati script for all Gujarati words — never use Roman letters for Gujarati.\n"
                    "Output only the converted text, no explanations."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise ValueError(
            f"Model returned an empty response for Gujarati translation. Raw response: {response}"
        )
    return content.strip()


def translate_from_english(text: str, language: str) -> str:
    """
    Translate an English response into the user's native script.

    Args:
        text: The English response from the fastworkflow agent.
        language: "hindi" or "gujarati"

    Returns:
        Response translated to Devanagari Hindi or Gujarati script.

    Raises:
        ValueError: If language is not supported.
    """
    language = language.lower().strip()
    if language == "hindi":
        return _english_to_hindi_devanagari(text)
    elif language == "gujarati":
        return _english_to_gujarati_script(text)
    else:
        raise ValueError(f"Unsupported language for output translation: {language!r}. Use 'hindi' or 'gujarati'.")
