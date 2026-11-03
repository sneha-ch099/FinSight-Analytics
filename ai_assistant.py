
import streamlit as st
from google import genai
from google.genai import types


def get_gemini_response(prompt, chat_history=None, context=""):
    """Generate financial responses with a limited request timeout."""

    api_key = st.secrets.get("GEMINI_API_KEY")

    if not api_key:
        return "Gemini API key is missing. Check secrets.toml."

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=15000)
        )

        instructions = """
        You are FinSight AI, a financial assistant specializing
        in Indian stock markets.

        Explain financial concepts in simple language.
        Help users understand stock performance, ratios,
        portfolio diversification and investment risk.

        Never invent financial figures or guarantee returns.
        Do not provide personalized investment advice.

        Always provide complete answers.
        Use clear headings and bullet points.
        Explain concepts with simple examples.
        Never stop in the middle of a sentence.
        Keep answers informative but concise.
        """

        history = ""

        if chat_history:
            for message in chat_history[-4:]:
                history += (
                    f"\n{message['role']}: "
                    f"{message['content']}\n"
                )

        contents = (
            instructions
            + "\nFinancial context: " + context
            + "\nConversation: " + history
            + "\nUser question: " + prompt
        )

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                max_output_tokens=1800,
                temperature=0.3
            )
        )

        if response.text:
            return response.text

        return "Gemini could not generate a complete response. Please try again."

    except Exception as error:
        return (
            "FinSight AI is temporarily unavailable. "
            "Please try again in a moment. "
            f"Details: {str(error)[:250]}"
        )
