import os
import io
import fitz  # PyMuPDF
import docx
import json
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import google.generativeai as genai
from waitress import serve
import firebase_admin
from firebase_admin import credentials, auth, firestore

# Initialize Firebase Admin
# Ensure serviceAccountKey.json is in your root folder (and in .gitignore!)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use a standard stable model (unless you specifically have access to 2.5)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__)
# Allow requests from your specific frontend URL (or * for dev)
CORS(app)

def extract_json_from_string(text):
    """Finds and extracts a JSON object from a string."""
    if '```json' in text:
        start = text.find('```json') + len('```json')
        end = text.find('```', start)
        json_str = text[start:end].strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass 

    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = text[start:end]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        return None
    return None

@app.route('/optimize', methods=['POST'])
def optimize_resume():
    # --- 1. Get Inputs ---
    if 'resume_file' not in request.files:
        return jsonify({"error": "No resume file part"}), 400
    
    resume_file = request.files['resume_file']
    job_description_text = request.form.get('job_description', '')

    if resume_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # --- 2. Auth Check (Optional) ---
    user_id = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1]
        try:
            decoded_token = auth.verify_id_token(token)
            user_id = decoded_token['uid']
        except Exception as e:
            print(f"Error verifying token: {e}")

    # --- 3. Prompt Engineering (FIXED for your UI) ---
    prompt_text = f"""
    You are an expert career coach acting as a JSON API.
    Analyze the provided resume content against the job description below.
    
    Your response MUST be a valid JSON object. The root object should have keys: "summary", "skill_matching", "clarity", and "impact".

    1. "summary": An object with "score" (0-100) and "feedback" (string).
    2. "skill_matching": An object with "score" (0-100), "feedback" (string), AND "missing_keywords" (an array of strings).
    3. "clarity": An object with "score" (0-100) and "feedback" (string).
    4. "impact": An object with "score" (0-100), "feedback" (string), AND "suggested_bullet_points" (an array of objects, each with "original" and "suggested" keys).

    **Job Description:**
    {job_description_text}

    **Resume Content (to be provided next):**
    """

    final_prompt_parts = [prompt_text]

    # --- 4. Process File ---
    try:
        if resume_file.mimetype == 'application/pdf':
            doc = fitz.open(stream=resume_file.read(), filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            final_prompt_parts.append(text)

        elif resume_file.mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            doc = docx.Document(io.BytesIO(resume_file.read()))
            text = "\n".join([para.text for para in doc.paragraphs])
            final_prompt_parts.append(text)

        elif resume_file.mimetype in ['image/jpeg', 'image/png']:
            img = Image.open(resume_file.stream)
            final_prompt_parts.append("Analyze the resume in the following image.")
            final_prompt_parts.append(img)
        
        else:
            return jsonify({"error": f"Unsupported file type: {resume_file.mimetype}"}), 400
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return jsonify({"error": "Could not extract content from the file."}), 500

    # --- 5. Call AI ---
    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content(final_prompt_parts, safety_settings=safety_settings)
        
        if response.parts:
            json_output = extract_json_from_string(response.text)
            
            # --- 6. Save to Database (FIXED Variable Name) ---
            if user_id and json_output:
                try:
                    # Create a new document in the user's history collection
                    doc_ref = db.collection('users').document(user_id).collection('history').document()
                    doc_ref.set({
                        'timestamp': firestore.SERVER_TIMESTAMP,
                        'job_description': job_description_text[:200] + "...", # FIXED: Used correct variable
                        'match_score': json_output.get('skill_matching', {}).get('score', 0),
                        'full_analysis': json_output
                    })
                    print(f"Saved analysis to history for user {user_id}")
                except Exception as e:
                    print(f"Failed to save to DB: {e}")

            if json_output:
                return jsonify(json_output)
            else:
                print(f"Failed to parse JSON. Raw text: {response.text}")
                return jsonify({"error": "AI failed to return valid JSON."}), 500

        else:
            finish_reason = response.candidates[0].finish_reason if response.candidates else 'UNKNOWN'
            print(f"Blocked. Reason: {finish_reason}")
            return jsonify({"error": "Response was blocked due to safety filters."}), 400

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": "Failed to get response from the AI model."}), 500

if __name__ == '__main__':
    print("🚀 Server starting...")
    # FIXED: host='0.0.0.0' makes it accessible externally (required for Render)
    serve(app, host='0.0.0.0', port=5000)