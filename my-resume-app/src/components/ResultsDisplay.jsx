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
        {/* FIXED: Accessed nested skill_matching.score */}
        <p className="score">
          {analysis.skill_matching?.score || 0}<span>%</span>
        </p>
      </div>

      <div className="summary-section card">
        <h3>Summary Feedback</h3>
        {/* FIXED: Accessed nested summary.feedback */}
        <p>{analysis.summary?.feedback || "No feedback available."}</p>
      </div>

      <div className="keywords-section card">
        <h3>Missing Keywords to Add</h3>
        <ul className="keywords-list">
          {/* FIXED: Accessed nested skill_matching.missing_keywords */}
          {analysis.skill_matching?.missing_keywords && analysis.skill_matching.missing_keywords.length > 0 ? (
            analysis.skill_matching.missing_keywords.map((keyword, index) => (
              <li key={index}>{keyword}</li>
            ))
          ) : (
            <li>No missing keywords detected.</li>
          )}
        </ul>
      </div>

      <div className="bullets-section card">
        <h3>Suggested Bullet Point Improvements</h3>
        {/* FIXED: Accessed nested impact.suggested_bullet_points */}
        {analysis.impact?.suggested_bullet_points && analysis.impact.suggested_bullet_points.length > 0 ? (
          analysis.impact.suggested_bullet_points.map((item, index) => (
            <div key={index} className="bullet-comparison">
              <p className="text-red-500" style={{ color: 'red' }}><strong>Original:</strong> {item.original}</p>
              <p className="text-green-500" style={{ color: 'green' }}><strong>Suggested:</strong> {item.suggested}</p>
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