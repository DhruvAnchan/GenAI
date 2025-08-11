import os
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro')

# Initialize Flask app
app = Flask(__name__)
# Enable CORS to allow requests from the frontend
CORS(app)

# Define the API endpoint
@app.route('/optimize', methods=['POST'])
def optimize_resume():
    # Get the data from the request
    data = request.get_json()
    if not data or 'resume' not in data or 'job_description' not in data:
        return jsonify({"error": "Missing resume or job description"}), 400

    resume_text = data['resume']
    job_description_text = data['job_description']

    # This is the prompt we send to the AI
    prompt = f"""
    You are an expert career coach and resume writer.
    Your task is to help a user tailor their resume for a specific job.

    Analyze the following resume and job description.

    **Job Description:**
    {job_description_text}

    **User's Resume:**
    {resume_text}

    **Your Instructions:**
    1.  Identify the top 5 most critical keywords and skills from the job description.
    2.  Provide 3-4 specific, actionable suggestions for how the user can improve their resume to better match the job description.
    3.  Rewrite one or two bullet points from the resume to be more impactful and include some of the identified keywords.

    Provide the output in a clean, easy-to-read format. Use markdown for formatting.
    """

    try:
        # Define the safety settings to be less restrictive
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        # Call the Gemini API with the new safety settings
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        # This line might now cause an error if the response is still empty,
        # so we should check the response before accessing .text
        if response.parts:
            return jsonify({"suggestions": response.text})
        else:
            # If the response is empty even with relaxed settings, inform the user.
            # You can check response.prompt_feedback for more details.
            print(f"Prompt Feedback: {response.prompt_feedback}")
            return jsonify({"error": "The response was blocked by safety filters, even with adjusted settings."}), 400

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to get response from AI"}), 500

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5000)