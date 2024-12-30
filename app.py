import os
from dotenv import load_dotenv  # Add this line for .env file support
from google.cloud import translate_v2 as translate
from flask import Flask, request, jsonify, render_template
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langdetect import detect
import json

# Load environment variables from .env file
load_dotenv()
# Get the key file path from the environment variable
key_path = os.getenv("GOOGLE_API_KEY_PATH")
if not key_path:
    raise ValueError("GOOGLE_API_KEY_PATH not set in environment variables.")

# Initialize the Translate client
translate_client = translate.Client.from_service_account_json(r"C:\Users\Dell\Documents\blah\google-service-account.json")


# Initialize Flask app
app = Flask(name)

# Route for favicon to prevent 404 errors
@app.route("/favicon.ico")
def favicon():
    return "", 204  # Return a No Content response

# Route for the root URL (home page)
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")  # Render the HTML file

# Replace with your actual local path to model directory
model_path = "C:/Users/Kanmani/OneDrive/Documents/multilingual-skill-extraction/mbart-large-50"

# Load model and tokenizer
model = AutoModelForSeq2SeqLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)

# Define the target language for translation (English)
TARGET_LANG = "en_XX"  # Use 'en_XX' for mBART (not just 'en')

# Load the skills database from the JSON file
def load_skills_from_json(filename='skills.json'):
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
        return data["skills"]  # Make sure this matches the structure of your JSON
    except FileNotFoundError:
        print("Error: File not found.")
        return []  # Return an empty list if the file is not found

# Load the skills database from the JSON file
skills_db = load_skills_from_json()

# Mapping from detected language to mBART-supported codes
LANGUAGE_MAP = {
    "af": "af_ZA",  # Afrikaans
    "am": "am_ET",  # Amharic
    "ar": "ar_AR",  # Arabic
    "az": "az_AZ",  # Azerbaijani
    "bn": "bn_BD",  # Bengali
    "bs": "bs_BA",  # Bosnian
    "bg": "bg_BG",  # Bulgarian
    "ca": "ca_ES",  # Catalan
    "ceb": "ceb_PH",  # Cebuano
    "cs": "cs_CZ",  # Czech
    "da": "da_DK",  # Danish
    "de": "de_XX",  # German
    "el": "el_GR",  # Greek
    "en": "en_XX",  # English
    "es": "es_XX",  # Spanish
    "et": "et_EE",  # Estonian
    "fa": "fa_IR",  # Persian
    "fi": "fi_FI",  # Finnish
    "fr": "fr_XX",  # French
    "ga": "ga_IE",  # Irish
    "gl": "gl_ES",  # Galician
    "gu": "gu_IN",  # Gujarati
    "ha": "ha_NG",  # Hausa
    "hi": "hi_IN",  # Hindi
    "hr": "hr_HR",  # Croatian
    "hu": "hu_HU",  # Hungarian
    "hy": "hy_AM",  # Armenian
    "id": "id_ID",  # Indonesian
    "ig": "ig_NG",  # Igbo
    "it": "it_XX",  # Italian
    "ja": "ja_XX",  # Japanese
    "jv": "jv_ID",  # Javanese
    "ka": "ka_GE",  # Georgian
    "kk": "kk_KZ",  # Kazakh
    "km": "km_KH",  # Khmer
    "kn": "kn_IN",  # Kannada
    "ko": "ko_XX",  # Korean
    "lt": "lt_LT",  # Lithuanian
    "lv": "lv_LV",  # Latvian
    "mg": "mg_MG",  # Malagasy
    "ml": "ml_IN",  # Malayalam
    "mn": "mn_MN",  # Mongolian
    "mr": "mr_IN",  # Marathi
    "ms": "ms_MY",  # Malay
    "my": "my_MM",  # Burmese
    "ne": "ne_NP",  # Nepali
    "nl": "nl_NL",  # Dutch
    "no": "no_NO",  # Norwegian
    "pa": "pa_IN",  # Punjabi
    "pl": "pl_PL",  # Polish
    "pt": "pt_XX",  # Portuguese
    "ro": "ro_RO",  # Romanian
    "ru": "ru_XX",  # Russian
    "si": "si_LK",  # Sinhala
    "sk": "sk_SK",  # Slovak
    "sl": "sl_SI",  # Slovenian
    "so": "so_SO",  # Somali
    "sq": "sq_AL",  # Albanian
    "sr": "sr_RS",  # Serbian
    "su": "su_ID",  # Sundanese
    "sv": "sv_SE",  # Swedish
    "sw": "sw_KE",  # Swahili
    "ta": "ta_IN",  # Tamil
    "te": "te_IN",  # Telugu
    "th": "th_TH",  # Thai
    "tr": "tr_TR",  # Turkish
    "uk": "uk_UA",  # Ukrainian
    "ur": "ur_PK",  # Urdu
    "vi": "vi_VN",  # Vietnamese
    "yo": "yo_NG",  # Yoruba
    "zh": "zh_XX",  # Chinese
    "zu": "zu_ZA"   # Zulu
}


def translate_text(input_text, source_lang="auto"):
    try:
        # Detect language automatically or use provided source_lang
        if source_lang == "auto":
            detected = translate_client.detect_language(input_text)
            source_lang = detected["language"]

        # Translate text to English
        result = translate_client.translate(
            input_text,
            source_language=source_lang,
            target_language="en"
        )

        translated_text_en = result["translatedText"]
        return source_lang, translated_text_en
    except Exception as e:
        return "error", f"Error during translation: {e}"

#def normalize_skill_text(text):
    #"""
    #Normalize text to handle transliteration and regional terms for skill extraction.
    #"""
   # transliteration_map = {
        #"பைத்தான்": "Python",
        #"ஜாவா": "Java",
        #"டிவலப்பர்": "developer",
        #"மேஷின் லேர்னிங்": "machine learning"
        # Add more mappings as needed
    #}
    #for tamil_term, normalized_term in transliteration_map.items():
        #text = text.replace(tamil_term, normalized_term)
    #return text

def extract_skills(text):
    skills_found = []
    skills_list = [skill["skill"].lower() for skill in skills_db]  # Extract skill names and normalize to lowercase
    words = text.lower().split()

    for word in words:
        word = word.strip(".,!?()[]{}")  # Clean up punctuation
        if word in skills_list:  # Check against the list of skill names
            skills_found.append(word.capitalize())

    if not skills_found:
        skills_found.append("No skills found")

    return skills_found

@app.route('/process-text', methods=['POST'])
def process_text():
    try:
        # Parse the request data
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({"error": "Invalid input, 'text' field is required"}), 400
        
        text = data['text']
        source_lang = data.get('source_lang', 'auto')

        # Step 1: Detect and translate the text to English
        detected_language, translated_text = translate_text(text, source_lang)
        if detected_language == "error":
            return jsonify({"error": translated_text}), 500  # Translation error

        # Step 2: Extract skills from the translated text
        extracted_skills = extract_skills(translated_text)

        # Return response
        return jsonify({
            "detected_language": detected_language,
            "translated_text": translated_text,
            "extracted_skills": extracted_skills
        }), 200
    except Exception as e:
        # Log the exception
        print(f"Error processing request: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

if name == 'main':
    app.run(debug=True)