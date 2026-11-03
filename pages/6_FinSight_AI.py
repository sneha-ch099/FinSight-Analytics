
import streamlit as st

from ai_assistant import get_gemini_response
from common import (
    apply_global_style,
    show_brand,
    show_hero,
    show_footer,
)

st.set_page_config(
    page_title="FinSight AI | Financial Assistant",
    page_icon="🤖",
    layout="wide",
)

apply_global_style()
show_brand()

show_hero(
    eyebrow="ARTIFICIAL INTELLIGENCE / FINANCIAL ANALYSIS",
    title="Meet your financial assistant.",
    highlighted_title="Ask. Analyse. Understand.",
    description=(
        "Explore financial concepts, understand Indian equity markets "
        "and get AI-powered financial explanations."
    ),
    chip="AI ASSISTANT • STOCK ANALYSIS • FINANCIAL INSIGHTS",
)

st.markdown(
    '<div class="section-heading">01 / AI Financial Assistant</div>',
    unsafe_allow_html=True,
)

st.info(
    "Ask questions about financial markets, stock performance, "
    "investment risk and financial concepts."
)

# Initialize chat history
if "finsight_chat_history" not in st.session_state:
    st.session_state.finsight_chat_history = []

# Display previous messages
for message in st.session_state.finsight_chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Suggested questions
st.markdown("#### Try asking")

suggestions = [
    "Explain what the Sharpe ratio means.",
    "How does diversification reduce portfolio risk?",
    "What is the difference between volatility and risk?",
]

columns = st.columns(3)

for i, question in enumerate(suggestions):
    with columns[i]:
        if st.button(question, use_container_width=True):
            st.session_state.pending_ai_question = question

# Chat input
user_prompt = st.chat_input(
    "Ask FinSight AI a financial question..."
)

if user_prompt:
    st.session_state.pending_ai_question = user_prompt

# Process question
if st.session_state.get("pending_ai_question"):

    prompt = st.session_state.pending_ai_question
    st.session_state.pending_ai_question = None

    # Save user message
    previous_history = st.session_state.finsight_chat_history.copy()

    st.session_state.finsight_chat_history.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("FinSight AI is thinking..."):

            answer = get_gemini_response(
                prompt,
                chat_history=previous_history
            )

        st.markdown(answer)

    st.session_state.finsight_chat_history.append(
        {"role": "assistant", "content": answer}
    )

    st.rerun()

# Clear conversation
if st.button("Clear conversation"):
    st.session_state.finsight_chat_history = []
    st.rerun()

st.markdown("---")

st.caption(
    "FinSight AI provides educational financial information. "
    "AI-generated responses may contain errors and should not "
    "be treated as investment advice."
)

show_footer()
