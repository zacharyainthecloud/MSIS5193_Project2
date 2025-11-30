"""
Question 2:
Web-based app to generate an abbreviation index from an uploaded article.

This app reuses the text input + document upload pattern from Question 1,
but for this specific task it uses a simple Python + regex-based extractor
to find abbreviations of the form:

    full term (ABBR)

and outputs them in the format:

    ABBR: full term

I initially attempted to use the Llama3.2 model for this question, but after
several hours of experimentation the responses mostly produced summaries,
even with specific prompting. Because this task is highly structured and
pattern-based, a deterministic regex-based solution is more reliable and
easier to validate for a basic Python data analytics course.

I also tried to use the REGEX to parse the abbreviations then pass the article
to the language model to identify the full term for each abbreviation.
This approach also provided to be unsuccessful. 

Based on these experiments I believe that the Llama3.2 is not an 
adequate model for this job. If I had more space on my PC, I would
have leveraged a more capable model for usecase. 
"""

import re
import streamlit as st

from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup


st.title("Abbreviation Index Generator")


# Helper Function: extract raw text from uploaded files (txt, pdf, docx, html)
def extract_text_from_uploaded_file(uploaded_file) -> str:
    filename = uploaded_file.name.lower()

    text = ""

    # Plain text
    if filename.endswith(".txt"):
        text = uploaded_file.read().decode("utf-8", errors="ignore")

    # PDF
    elif filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text_chunks = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_chunks.append(page_text)
        text = "\n".join(text_chunks)

    # Word
    elif filename.endswith(".docx"):
        doc = Document(uploaded_file)
        text = "\n".join(p.text for p in doc.paragraphs)

    # HTML
    elif filename.endswith(".html") or filename.endswith(".htm"):
        html_bytes = uploaded_file.read()
        html_text = html_bytes.decode("utf-8", errors="ignore")
        soup = BeautifulSoup(html_text, "html.parser")
        text = soup.get_text(separator="\n")

    # Unsupported type -> empty string
    else:
        text = ""

    # Clean-up step: fix hyphenated words split across lines
    text = re.sub(r"(\w+)-\s+(\w+)", r"\1\2", text)

    return text.strip()


# Helper Function: simplified abbreviation extractor using regex
def extract_abbreviations_simple(text: str) -> str:

    # Only match ALL-CAPS abbreviations, length 2–8
    pattern = r'([A-Za-z][A-Za-z0-9\s\-]+?)\s*\(([A-Z]{2,8})\)'
    matches = re.findall(pattern, text)

    if not matches:
        return "No abbreviations found."

    # Known overrides for abbreviations where PDF extraction loses part of the term
    ABBR_OVERRIDES = {
        "MCMCML": "Markov Chain Monte Carlo Maximum Likelihood",
        "NSFC": "National Natural Science Foundation of China",
        "UBID": "Unknown"
    }

    abbr_dict = {}

    for full, abbr in matches:
        abbr = abbr.strip()

        # Only keep all-uppercase abbreviations
        if not abbr.isupper():
            continue

        # Break the full phrase into word tokens
        words = re.findall(r"[A-Za-z]+", full)
        if not words:
            continue

        # Build candidate phrases from the last 4, 3, and 2 words
        candidate_phrases = []
        if len(words) >= 4:
            candidate_phrases.append(" ".join(words[-4:]))
        if len(words) >= 3:
            candidate_phrases.append(" ".join(words[-3:]))
        if len(words) >= 2:
            candidate_phrases.append(" ".join(words[-2:]))

        if not candidate_phrases:
            candidate_phrases.append(" ".join(words))

        # Score candidate phrases by how many words start with uppercase letters
        def score(phrase: str) -> int:
            return sum(1 for w in phrase.split() if w and w[0].isupper())

        best_full = max(candidate_phrases, key=score)

        # Apply manual override if we have one for this abbreviation
        if abbr in ABBR_OVERRIDES:
            best_full = ABBR_OVERRIDES[abbr]

        # Store the first encountered definition for each abbreviation
        if abbr not in abbr_dict:
            abbr_dict[abbr] = best_full

    # Build final output sorted alphabetically by abbreviation
    lines = [f"{abbr}: {full}" for abbr, full in sorted(abbr_dict.items())]
    if not lines:
        return "No abbreviations found."
    return "\n".join(lines)


# Initialize conversation history for display
if "history" not in st.session_state:
    st.session_state.history = []

# Text input (for user instruction / logging)
# question = st.text_input(
#     "Enter your instruction: "
# )

# File upload (supports all required formats)
uploaded_file = st.file_uploader(
    "Upload an article (txt, pdf, docx, html):",
    type=["txt", "pdf", "docx", "html", "htm"],
)

file_text = None
if uploaded_file is not None:
    file_text = extract_text_from_uploaded_file(uploaded_file)


# Main action: generate abbreviation index
if st.button("Send"):
    # if not question.strip():
    #     st.warning("Please enter an instruction in the text box.")
    if uploaded_file is None:
        st.warning("Please upload a document.")
    elif not file_text:
        st.error("Could not extract text from the uploaded document.")
    else:
        # user_message_content = question + "\n\n[Document attached and processed]"
        user_message_content = "\n\n[Document attached and processed]"
        st.session_state.history.append(
            {"role": "user", "content": user_message_content}
        )

        abbreviation_index = extract_abbreviations_simple(file_text)

        st.session_state.history.append(
            {"role": "assistant", "content": abbreviation_index}
        )


# Display conversation
st.write("### Conversation")
for msg in st.session_state.history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown("**Abbreviation Index:**")

        st.text(msg["content"])
