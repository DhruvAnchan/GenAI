import os
import io
import fitz  # PyMuPDF
import docx
import json
import logging  # <--- IMPORT THIS
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from waitress import serve
import firebase_admin
from firebase_admin import credentials, auth, firestore

# --- 0. Setup Logging (CRITICAL FIX) ---
# This ensures logs print to the console immediately without buffering
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

load_dotenv()

# --- 1. Configure Gemini ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-2.5-flash')

app = Flask(__name__)
CORS(app)

@app.route('/optimize', methods=['POST'])
def optimize_resume():
    logger.info("Received request to /optimize") # Log entry

    # --- 2. Input Validation ---
    if 'resume_file' not in request.files:
        logger.error("No resume file part")
        return jsonify({"error": "No resume file part"}), 400
    
    resume_file = request.files['resume_file']
    job_description_text = request.form.get('job_description', '')

    if resume_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # --- 3. Auth Check ---
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split("Bearer ")[1]
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
            logger.info(f"Authenticated user: {user_id}")
        except Exception as e:
            logger.warning(f"Auth Warning: {e}")

    # --- 4. Prepare Prompt ---
    prompt_text = f"""
    You are an expert career coach. Analyze the resume against the job description.
    
    Return a JSON object with this exact structure:
    {{
        "summary": {{ "score": 0-100, "feedback": "string" }},
        "skill_matching": {{ "score": 0-100, "feedback": "string", "missing_keywords": ["str"] }},
        "clarity": {{ "score": 0-100, "feedback": "string" }},
        "impact": {{ "score": 0-100, "feedback": "string", "suggested_bullet_points": [ {{ "original": "str", "suggested": "str" }} ] }}
    }}

    **Job Description:**
    {job_description_text}
    """

    final_prompt_parts = [prompt_text]

    # --- 5. Process Files ---
    try:
        if resume_file.mimetype == 'application/pdf':
            doc = fitz.open(stream=resume_file.read(), filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            final_prompt_parts.append(f"RESUME TEXT:\n{text}")

        elif 'wordprocessingml' in resume_file.mimetype:
            doc = docx.Document(io.BytesIO(resume_file.read()))
            text = "\n".join([para.text for para in doc.paragraphs])
            final_prompt_parts.append(f"RESUME TEXT:\n{text}")

        elif resume_file.mimetype in ['image/jpeg', 'image/png']:
            img = Image.open(resume_file.stream)
            final_prompt_parts.append("Analyze this resume image:")
            final_prompt_parts.append(img)
        
        else:
            logger.error(f"Unsupported file type: {resume_file.mimetype}")
            return jsonify({"error": "Unsupported file type"}), 400
    
    except Exception as e:
        logger.error(f"File Processing Error: {e}")
        return jsonify({"error": "Failed to read file"}), 500

    # --- 6. Call AI ---
    try:
        logger.info("Sending request to Gemini API...") # Checkpoint

        generation_config = {
            "response_mime_type": "application/json"
        }

        response = model.generate_content(
            final_prompt_parts,
            generation_config=generation_config
        )
        
        # Safety Check
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            logger.warning(f"Blocked. Reason: {response.prompt_feedback.block_reason}")
            return jsonify({"error": "AI blocked the request."}), 400

        # Log the raw text first (in case JSON parsing fails)
        # logger.info(f"Raw Model Response: {response.text}") 

        # Parse JSON
        json_output = json.loads(response.text)
        logger.info("Gemini Output Successfully Generated & Parsed")

        # --- 7. Save to DB ---
        if user_id:
            try:
                db.collection('users').document(user_id).collection('history').add({
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    'job_description': job_description_text[:200],
                    'match_score': json_output.get('skill_matching', {}).get('score', 0),
                    'full_analysis': json_output
                })
                logger.info(f"Saved to Firestore for user {user_id}")
            except Exception as e:
                logger.error(f"DB Save Error: {e}")

        return jsonify(json_output)

    except Exception as e:
        logger.error(f"Gemini API Error: {e}", exc_info=True) # exc_info gives full traceback
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Server starting on port 5000...")
    serve(app, host='0.0.0.0', port=5000)