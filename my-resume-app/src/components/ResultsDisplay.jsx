import React from 'react';

function ResultsDisplay({ analysis }) {
  // If there's no analysis object, render nothing.
  if (!analysis) {
    return null;
  }

  return (
    <div className="results-container">
      <h2>Analysis Results</h2>

      {/* --- 1. Match Score --- */}
      <div className="score-section card">
        <h3>Match Score</h3>
        {/* FIX: We drill down into 'skill_matching' to find the score */}
        <p className="score">
          {analysis.skill_matching?.score || 0}<span>%</span>
        </p>
      </div>

      {/* --- 2. Summary Feedback --- */}
      <div className="summary-section card">
        <h3>Summary Feedback</h3>
        {/* FIX: We check 'summary.feedback' */}
        <p>{analysis.summary?.feedback || "No feedback available."}</p>
      </div>

      {/* --- 3. Missing Keywords --- */}
      <div className="keywords-section card">
        <h3>Missing Keywords to Add</h3>
        <ul className="keywords-list">
          {/* FIX: We look inside 'skill_matching.missing_keywords' */}
          {analysis.skill_matching?.missing_keywords && analysis.skill_matching.missing_keywords.length > 0 ? (
            analysis.skill_matching.missing_keywords.map((keyword, index) => (
              <li key={index}>{keyword}</li>
            ))
          ) : (
            <li>No missing keywords detected.</li>
          )}
        </ul>
      </div>

      {/* --- 4. Suggested Bullet Points --- */}
      <div className="bullets-section card">
        <h3>Suggested Bullet Point Improvements</h3>
        {/* FIX: We look inside 'impact.suggested_bullet_points' */}
        {analysis.impact?.suggested_bullet_points && analysis.impact.suggested_bullet_points.length > 0 ? (
          analysis.impact.suggested_bullet_points.map((item, index) => (
            <div key={index} className="bullet-comparison" style={{ marginBottom: '1rem', padding: '10px', background: '#222', borderRadius: '5px' }}>
              <p style={{ color: '#ff6b6b', textDecoration: 'line-through' }}>
                <strong>Original:</strong> {item.original}
              </p>
              <p style={{ color: '#51cf66' }}>
                <strong>Suggested:</strong> {item.suggested}
              </p>
            </div>
          ))
        ) : (
          <p>No specific bullet improvements found.</p>
        )}
      </div>
    </div>
  );
}

export default ResultsDisplay;