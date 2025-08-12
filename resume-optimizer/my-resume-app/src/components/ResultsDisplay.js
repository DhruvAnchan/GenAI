// Example ResultsDisplay.js component

function ResultsDisplay({ analysis }) {
  // 'analysis' is the JSON object received from your API
  if (!analysis) return null;

  return (
    <div className="results-container">
      <h2>Analysis Results</h2>

      <div className="score-section">
        <h3>Match Score: {analysis.match_score}%</h3>
        {/* You could use a library to render a progress circle here */}
      </div>

      <div className="summary-section">
        <h3>Summary</h3>
        <p>{analysis.summary_feedback}</p>
      </div>

      <div className="keywords-section">
        <h3>Missing Keywords</h3>
        <ul>
          {analysis.missing_keywords.map((keyword, index) => (
            <li key={index}>{keyword}</li>
          ))}
        </ul>
      </div>

      <div className="bullets-section">
        <h3>Suggested Improvements</h3>
        {analysis.suggested_bullet_points.map((item, index) => (
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