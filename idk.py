from app import translate_text, extract_skills

# Example input
text = "Soy un desarrollador de software con experiencia en Python, Java, y C++."
source_lang = "es"  # Spanish input

try:
    # Step 1: Translate the text
    detected_lang, translated_text = translate_text(text, source_lang)
    if detected_lang == "error":
        print(f"Error during translation: {translated_text}")
        exit()

    print(f"Detected Language: {detected_lang}")
    print(f"Translated Text: {translated_text}")

    # Step 2: Extract skills
    extracted_skills = extract_skills(translated_text)
    print(f"Extracted Skills: {extracted_skills}")

except Exception as e:
    print(f"An error occurred: {e}")