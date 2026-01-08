import React from 'react';

function ResultsDisplay({ analysis }) {
  // If there's no analysis object, render nothing.
  if (!analysis) {
    return null;
  }

  return (
    <div className="results-container">
      <h2>Analysis Results</h2>

      <div className="score-section card">
        <h3>Match Score</h3>
        <p className="score">{analysis.match_score}<span>%</span></p>
        {/* You could add a progress circle component here later */}
      </div>

      <div className="summary-section card">
        <h3>Summary Feedback</h3>
        <p>{analysis.summary_feedback}</p>
      </div>

      <div className="keywords-section card">
        <h3>Missing Keywords to Add</h3>
        <ul className="keywords-list">
          {analysis.missing_keywords && analysis.missing_keywords.map((keyword, index) => (
            <li key={index}>{keyword}</li>
          ))}
        </ul>
      </div>

      <div className="bullets-section card">
        <h3>Suggested Bullet Point Improvements</h3>
        {analysis.suggested_bullet_points && analysis.suggested_bullet_points.map((item, index) => (
          <div key={index} className="bullet-comparison">
            <p><strong>Original:</strong> {item.original}</p>
            <p><strong>Suggested:</strong> {item.suggested}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ResultsDisplay;