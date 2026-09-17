"""
Tordi's AI brain.

Tordi is presented to users as a dedicated petroleum-engineering /
general-engineering assistant. Under the hood it calls Google's Gemini API
with a system instruction that focuses it on that domain while still being
able to help with other engineering disciplines (civil, mechanical,
electrical, chemical, etc).
"""

import mimetypes

from django.conf import settings

TORDI_SYSTEM_PROMPT = """You are Tordi, an expert AI engineering assistant.

Your primary specialty is petroleum engineering: reservoir engineering,
drilling engineering, well completions, production engineering, formation
evaluation/petrophysics, flow assurance, EOR, PVT and fluid properties,
well testing, HSE in oil & gas, and related economics.

You are also a highly capable assistant across other engineering fields
(civil, mechanical, electrical, chemical, petroleum-adjacent geology, etc.)
and can help with calculations, explanations, unit conversions, code,
diagrams described in words, and study/exam preparation.

Style rules:
- Be precise, professional, and clear. Prefer worked examples and correct
  units (SI and field units where relevant to petroleum engineering).
- Show formulas before plugging in numbers when doing calculations.
- If a question is ambiguous or missing data, state the assumption you're
  making and proceed.
- If asked something clearly outside engineering/science, answer briefly
  and helpfully anyway - you do not need to refuse general questions.
- Never claim to be Gemini, Google, or any other model - you are Tordi.
"""


def _file_to_gemini_part(file_field):
    """Turn an uploaded Django image field into a Gemini `Part`."""
    from google.genai import types

    file_field.open("rb")
    try:
        data = file_field.read()
    finally:
        file_field.close()
    mime_type, _ = mimetypes.guess_type(file_field.name)
    mime_type = mime_type or "image/png"
    return types.Part.from_bytes(data=data, mime_type=mime_type)


def build_user_content(text, image_field=None):
    """Builds the list of Gemini `Part`s for a user turn (text + optional image)."""
    from google.genai import types

    parts = []
    if image_field:
        try:
            parts.append(_file_to_gemini_part(image_field))
        except Exception:
            pass
    parts.append(types.Part.from_text(text=text or "(empty message)"))
    return parts


def get_tordi_response(history):
    """
    history: list of dicts [{"role": "user"|"assistant", "content": <parts list or str>}]
    Returns Tordi's reply text.
    """
    if not settings.GEMINI_API_KEY:
        return (
            "Tordi isn't fully configured yet: no GEMINI_API_KEY was found. "
            "Add your API key to the .env file to activate answers."
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return "The 'google-genai' package is not installed. Run: pip install google-genai"

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    contents = []
    for turn in history:
        role = "model" if turn["role"] == "assistant" else "user"
        content = turn["content"]
        parts = [types.Part.from_text(text=content)] if isinstance(content, str) else content
        contents.append(types.Content(role=role, parts=parts))

    try:
        response = client.models.generate_content(
            model=settings.TORDI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=TORDI_SYSTEM_PROMPT,
                max_output_tokens=2000,
            ),
        )
        text = (response.text or "").strip()
        return text or "Tordi couldn't generate a reply. Please try again."
    except Exception as exc:  # noqa: BLE001
        return f"Tordi ran into an error reaching the AI model: {exc}"
