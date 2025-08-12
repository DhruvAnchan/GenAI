import React, { useState } from 'react';
import ResultsDisplay from './components/ResultsDisplay.jsx'; // Make sure this file exists
import './App.css'; // We will add styles here

function App() {
  // --- 1. State Management for the Form ---
  const [selectedFile, setSelectedFile] = useState(null);
  const [jobDescription, setJobDescription] = useState('');
  const [analysis, setAnalysis] = useState(null); // To hold the JSON results
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // --- 2. API Call Logic ---
  const handleSubmit = async () => {
    // Basic validation
    if (!selectedFile || !jobDescription) {
      setError('Please select a resume file and provide a job description.');
      return;
    }

    // Reset states before a new submission
    setLoading(true);
    setError('');
    setAnalysis(null);

    const formData = new FormData();
    formData.append('resume_file', selectedFile);
    formData.append('job_description', jobDescription);

    try {
      const response = await fetch('http://127.0.0.1:5000/optimize', {
        method: 'POST',
        body: formData,
      });

      // Handle server errors (e.g., 400, 500)
      if (!response.ok) {
        // Try to parse error JSON, otherwise use status text
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        throw new Error(errorData.error || `HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      setAnalysis(data); // Set the full JSON object to state

    } catch (err) {
      // Handle network errors or errors thrown from the block above
      setError(err.message);
      console.error('Submission error:', err);
    } finally {
      // This runs whether the request succeeded or failed
      setLoading(false);
    }
  };

  // --- 3. JSX for the Form and UI ---
  return (
    <main>
      <h1>AI Resume Optimizer 🚀</h1>
      <div className="form-container">
        <div className="input-group">
          <label htmlFor="resume-file">Your Resume File (.pdf, .docx, .png, .jpg)</label>
          <input 
            id="resume-file"
            type="file" 
            accept=".pdf,.docx,.jpg,.jpeg,.png"
            onChange={(e) => setSelectedFile(e.target.files[0])} 
          />
        </div>
        <div className="input-group">
          <label htmlFor="job-desc">Job Description</label>
          <textarea 
            id="job-desc"
            placeholder="Paste the job description here..."
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
          />
        </div>
        <button onClick={handleSubmit} disabled={loading}>
          {loading ? 'Analyzing...' : 'Optimize My Resume'}
        </button>
      </div>

      {/* Conditionally render the error message */}
      {error && <div className="error-message">{error}</div>}
      
      {/* Conditionally render a loading indicator */}
      {loading && <div className="loader">🔄 Analyzing... Please wait.</div>}

      {/* Pass the analysis results to the child component */}
      <ResultsDisplay analysis={analysis} />
    </main>
  );
}

export default App;