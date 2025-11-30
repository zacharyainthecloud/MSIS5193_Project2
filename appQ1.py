"""
Question 1: This implementation assumes that the user is running ollama with a llama 3.2:latest version. 

I implemented the streamlit session state to try and explore additional features of the streamlit framework.
"""
import streamlit as st
import ollama

from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup


st.title("Input to AI")


# text extract function for plain text, PDF, Word, and HTML
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

    # Error notification
    else:
        return "<<Unsupported file type>>"


# Initialize conversation history
if "history" not in st.session_state:
    st.session_state.history = []

# Text input
question = st.text_input("Enter your question:")

# File upload
uploaded_file = st.file_uploader(
    "Upload a document (txt, pdf, docx, html):",
    type=["txt", "pdf", "docx", "html", "htm"]
)

file_text = None

# Extract text from the uploaded file
if uploaded_file is not None:
    file_text = extract_text_from_uploaded_file(uploaded_file)

# Send button to connect content streamlit content to the LLM
if st.button("Send"):
    if question.strip():

        # --- What we SHOW to the user ---
        if uploaded_file is not None:
            display_message = (
                f"{question}\n\n"
                f"[Document uploaded: {uploaded_file.name} ingested successfully]"
            )
        else:
            display_message = question

        st.session_state.history.append(
            {"role": "user", "content": display_message}
        )

        if file_text:
            prompt_for_model = f"""
You are an assistant. Answer the user's question using the document text provided.

Question:
{question}

Document text:
{file_text}
"""
        else:
            prompt_for_model = question

        # LLM call (Ollama)
        response = ollama.chat(
            model="llama3.2:latest",
            messages=[{"role": "user", "content": prompt_for_model}]
        )

        reply = response["message"]["content"]

        # Display assistant response
        st.session_state.history.append(
            {"role": "assistant", "content": reply}
        )

# Write the conversation history to Streamlit frontend
st.write("### Conversation")
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**AI:** {msg['content']}")
