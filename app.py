import streamlit as st
import pandas as pd
import json
from flashcard_core import generate_flashcards_t5, extract_text_from_file, load_t5_model, parse_flashcards 

tokenizer, model = load_t5_model()

st.title("📚 LLM-Powered Flashcard Generator")

st.sidebar.header("Input Method")
input_method = st.sidebar.radio("Choose your input method:", ("Text Input", "File Upload"))

content = None

if input_method == "Text Input":
    st.header("Paste Your Content")
    text_input = st.text_area("Enter or paste your educational content here:", height=300)
    content = text_input.strip()
else:
    st.header("Upload Your File")
    uploaded_file = st.file_uploader("Choose a PDF or TXT file", type=["pdf", "txt"])
    if uploaded_file is not None:
        content = extract_text_from_file(uploaded_file, uploaded_file.type)
        if content:
            st.success("File uploaded and text extracted.")
        else:
            st.error("Could not extract text from the uploaded file.")


st.header("Subject Selection")
subject = st.selectbox("Select the subject of the content:",
                       ['General', 'Science', 'History', 'Math', 'Literature'])

st.header("Generate Flashcards")
if st.button("Generate Flashcards"):
    if model is None or tokenizer is None:
         st.error("The language model could not be loaded. Please check your installation.")
    elif not content or len(content) < 100:
        st.warning("Please provide enough content (minimum 100 characters) to generate flashcards.")
    else:
        with st.spinner("Generating flashcards..."):
            cards, error = generate_flashcards_t5(content, subject)

            if error:
                st.error(f"❌ {error}")
            elif not cards:
                 st.warning("⚠️ Could not generate valid flashcards from this content.")
                 st.info("This might be due to the text content or the model's limitations or if very few cards were generated.")
            else:
                st.success(f"✅ Generated {len(cards)} flashcards:")


                for i, card in enumerate(cards, 1):
                    with st.expander(f"{i}. Q: {card['question']}"):
                        st.write(f"**A:** {card['answer']}")

                st.subheader("Export Options")

                csv_file = pd.DataFrame(cards).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download as CSV",
                    data=csv_file,
                    file_name='flashcards.csv',
                    mime='text/csv',
                )
                json_string = json.dumps(cards, indent=4)
                st.download_button(
                    label="Download as JSON",
                    file_name='flashcards.json',
                    data=json_string,
                    mime='application/json',
                )