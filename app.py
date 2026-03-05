import streamlit as st

st.set_page_config(page_title="What Is Vibe?", page_icon="??", layout="centered")

CHAT_LOG = [
    {"speaker": "Matt", "message": "Nice, what is vibe"},
    {
        "speaker": "You",
        "message": "When you do software development without writing code and just telling AI what you want in natural language",
    },
    {"speaker": "Matt", "message": "I mean is vibe the tool? Or is that a new term for the concept"},
    {"speaker": "You", "message": "it's a term"},
]


st.title("Vibe: Term, Not Tool")
st.caption("A tiny Streamlit app based only on your chat.")

st.markdown(
    """
**Definition from the chat:**
Vibe means doing software development by describing what you want in natural language,
instead of directly writing the code yourself.
"""
)

st.divider()

st.subheader("Original Chat")
for line in CHAT_LOG:
    role = "user" if line["speaker"].lower() == "matt" else "assistant"
    with st.chat_message(role):
        st.write(f"**{line['speaker']}:** {line['message']}")

st.divider()

st.subheader("Quick Clarifier")
question = st.radio(
    "In this context, what is 'vibe'?",
    ["A software tool", "A term/concept"],
    index=1,
)

if question == "A term/concept":
    st.success("Correct. In this chat, vibe is a term for the development style.")
else:
    st.error("Not in this chat. Here, vibe is not a tool.")

st.divider()

st.subheader("Your One-Liner")
style = st.text_input(
    "Describe what you want to build in plain language:",
    placeholder="Example: Build a to-do app with reminders and a clean dashboard.",
)

if style.strip():
    st.info(
        "Vibe version: You describe the product in natural language, and AI handles the code generation."
    )
    st.write("**Your prompt:**", style.strip())
