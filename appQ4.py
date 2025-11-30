"""
Question 4 API Version:

This version of the app uses a closed-source LLM (ChatGPT via the OpenAI API)
instead of a local open-source model via Ollama.

Model used: gpt-4o-mini (closed-source, accessed via API).

The app accepts a user question and an optional document
(plain text, PDF, Word, or HTML), extracts the text, and sends
both the question and the document content to the model as context.

An API key is entered via a text box in the Streamlit UI so that no
environment variables or secrets files are required. This also allows
deployment to Streamlit Cloud.
"""

import streamlit as st
from openai import OpenAI

from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup


st.title("Input to AI (gpt-4o-mini)")


# Helper: extract text from uploaded files
def extract_text_from_uploaded_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()

    # Plain text
    if filename.endswith(".txt"):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    # PDF
    elif filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text_chunks = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
        return "\n".join(text_chunks).strip()

    # Word
    elif filename.endswith(".docx"):
        doc = Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    # HTML
    elif filename.endswith(".html") or filename.endswith(".htm"):
        html_bytes = uploaded_file.read()
        html_text = html_bytes.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_text, "html.parser")
        return soup.get_text(separator="\n").strip()

    # Unsupported type
    else:
        return "<<Unsupported file type>>"


# Initialize conversation history
if "history" not in st.session_state:
    st.session_state.history = []

# API key input
api_key = st.text_input(
    "Enter your OpenAI API key:",
    type="password",
    help="Your key is used only in this session and is not stored permanently."
)

# Question input
question = st.text_input("Enter your question:")

# File upload
uploaded_file = st.file_uploader(
    "Upload a document (txt, pdf, docx, html):",
    type=["txt", "pdf", "docx", "html", "htm"]
)

file_text = None

# Extract text from uploaded file (if any)
if uploaded_file is not None:
    file_text = extract_text_from_uploaded_file(uploaded_file)

# Main action: send to GPT-4o-mini via API 
if st.button("Send"):
    if not api_key.strip():
        st.error("Please enter your OpenAI API key.")
    elif not question.strip():
        st.warning("Please enter a question.")
    else:
        if uploaded_file is not None and file_text:
            display_message = (
                f"{question}\n\n"
                f"[Document uploaded: {uploaded_file.name} ingested successfully]"
            )
        elif uploaded_file is not None and not file_text:
            display_message = (
                f"{question}\n\n"
                f"[Document uploaded: {uploaded_file.name} (no text extracted)]"
            )
        else:
            display_message = question

        st.session_state.history.append(
            {"role": "user", "content": display_message}
        )

        if file_text:
            prompt_for_model = f"""
You are given a question and the full text of a document.

Question:
{question}

Document text:
{file_text}
"""
        else:
            prompt_for_model = question

        try:
            client = OpenAI(api_key=api_key)

            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant. The user will provide "
                            "the full text of a document inside the message itself. "
                            "You CAN read and use that text. Do NOT say that you "
                            "cannot access attachments or PDFs. Instead, directly "
                            "answer the question using the document text provided."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt_for_model,
                    },
                ],
                temperature=0.2,
            )

            reply = completion.choices[0].message.content

        except Exception as e:
            reply = f"Error calling OpenAI API: {e}"

        st.session_state.history.append(
            {"role": "assistant", "content": reply}
        )

# Display conversation history
st.write("### Conversation")
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")
