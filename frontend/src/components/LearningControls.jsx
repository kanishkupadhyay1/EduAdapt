import React from 'react';

const PPS_TOPICS = [
  'Pointers',
  'Variables and Data Types',
  'Operators and Expressions',
  'Conditionals',
  'Loops',
  'Nested Loops',
  'Arrays',
  'Functions',
  'Strings',
  'Python Basics',
  'Python Data Structures',
  'NumPy',
  'Pandas',
];

export default function LearningControls({
  selectedTopic,
  onTopicChange,
  topK,
  onTopKChange,
  onGenerate,
  isLoading,
}) {
  return (
    <section className="panel" aria-labelledby="controls-heading">
      <div className="panel-header">
        <h2 id="controls-heading" className="panel-title">Learning Session</h2>
        <span className="panel-badge badge-gray">Session Setup</span>
      </div>
      <div className="panel-body">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            onGenerate();
          }}
        >
          <div className="form-group">
            <label htmlFor="topic-select" className="form-label">
              Topic
            </label>
            <select
              id="topic-select"
              className="form-select"
              value={selectedTopic}
              onChange={(e) => onTopicChange(e.target.value)}
              disabled={isLoading}
            >
              {PPS_TOPICS.map((topic) => (
                <option key={topic} value={topic}>
                  {topic}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="topk-input" className="form-label">
              Top K Retrieval
            </label>
            <input
              id="topk-input"
              type="number"
              min="1"
              max="10"
              className="form-input"
              value={topK}
              onChange={(e) => onTopKChange(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Generating personalized learning session...' : 'Generate Learning Session'}
          </button>
        </form>
      </div>
    </section>
  );
}
