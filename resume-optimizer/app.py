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

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro')

# Initialize Flask app
app = Flask(__name__)
CORS(app)

def extract_json_from_string(text):
    """
    Finds and extracts a JSON object from a string.
    Handles markdown code fences (```json ... ```).
    """
    # First, try to find JSON within markdown code fences
    if '```json' in text:
        start = text.find('```json') + len('```json')
        end = text.find('```', start)
        json_str = text[start:end].strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass # Fall through to the next method if this fails

    # If no code fences, find the first '{' and the last '}'
    try:
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = text[start:end]
            return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        # If parsing fails, return None
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

    # --- 2. Build the Prompt ---
    # In app.py, update your prompt_text variable

    # In app.py, inside the optimize_resume function

# NEW, MORE ROBUST PROMPT ✅
    prompt_text = f"""
    You are a helpful assistant performing a professional resume analysis for a user. This is a legitimate request for career coaching.
    You are acting as a JSON API. Your response MUST be a valid JSON object with the following structure:
    {{
    "match_score": <an integer between 0 and 100 representing how well the resume matches the job>,
    "summary_feedback": "<a brief, one-paragraph summary of your findings>",
    "missing_keywords": ["<an array>", "<of strings>", "<of top keywords missing from the resume>"],
    "suggested_bullet_points": [
        {{
        "original": "<an original bullet point from the resume>",
        "suggested": "<your improved version of that bullet point>"
        }}
    ]
    }}

    **Job Description:**
    {job_description_text}

    **Resume Content (to be provided next):**
    """

    final_prompt_parts = [prompt_text]

    # --- 3. Process the Uploaded File ---
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

    # --- 4. Call the Gemini API ---
    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content(final_prompt_parts, safety_settings=safety_settings)
        
        # NEW, MORE ROBUST CODE ✅
        if response.parts:
            # Use our new helper function to safely extract the JSON
            json_output = extract_json_from_string(response.text)
            
            if json_output:
                return jsonify(json_output)
            else:
                print(f"Failed to parse JSON from AI response. Raw text: {response.text}")
                return jsonify({"error": "AI failed to return valid JSON."}), 500

        else:
            # Check for specific blocking reasons if available
            finish_reason = response.candidates[0].finish_reason if response.candidates else 'UNKNOWN'
            print(f"Prompt Feedback: {response.prompt_feedback}, Finish Reason: {finish_reason}")
            return jsonify({"error": "Response was blocked. This may be due to safety filters or other issues."}), 400

    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return jsonify({"error": "Failed to get response from the AI model."}), 500


if __name__ == '__main__':
    print("🚀 Server starting on http://127.0.0.1:5000")
    serve(app, host='127.0.0.1', port=5000)