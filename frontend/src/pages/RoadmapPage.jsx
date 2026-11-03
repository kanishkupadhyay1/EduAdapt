import React, { useState, useEffect } from 'react';
import { generateAdaptiveRoadmap } from '../api/learningApi';

function parseRoadmapStages(rawText) {
  if (!rawText) return [];
  const lines = rawText.split('\n');
  const stages = [];
  let counter = 1;

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const match = trimmed.match(/^(?:(?:\d+\.|\*|-|•)\s*)?(.*)$/);
    const content = match ? match[1].trim() : trimmed;
    if (content.length > 3) {
      stages.push({
        num: String(counter).padStart(2, '0'),
        text: content,
      });
      counter++;
    }
  }
  return stages;
}

export default function RoadmapPage({
  studentId = 'S001',
  studentProfile,
  currentTopic = 'Pointers',
  sessionResult,
  onNavigate,
}) {
  const [targetCompetency, setTargetCompetency] = useState(`Comprehensive PPS Mastery in ${currentTopic}`);
  const [roadmapData, setRoadmapData] = useState(sessionResult?.roadmap || null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (sessionResult?.roadmap && !roadmapData) {
      setRoadmapData(sessionResult.roadmap);
    }
  }, [sessionResult]);

  const handleGenerate = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await generateAdaptiveRoadmap(studentId, currentTopic, targetCompetency);
      setRoadmapData(data);
    } catch (err) {
      setError('Unable to generate roadmap. Please verify backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  const stages = parseRoadmapStages(roadmapData?.roadmap_content);
  const mastery = studentProfile?.mastery !== undefined
    ? `${Math.round(studentProfile.mastery * 100)}%`
    : 'Dynamic';
  const difficulty = studentProfile?.recommended_difficulty || 'Adaptive';

  return (
    <div className="roadmap-page">
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">Adaptive Learning Roadmap</h2>
            <p className="page-subtitle">
              Goal-oriented PPS milestone pathway sequenced for Student <strong>{studentId}</strong> ({difficulty} tier • {mastery} mastery).
            </p>
          </div>
          <button
            type="button"
            className="btn-primary"
            onClick={handleGenerate}
            disabled={isLoading}
          >
            {isLoading ? 'Sequencing roadmap with Mistral 7B...' : 'Regenerate Adaptive Roadmap ☵'}
          </button>
        </div>
      </header>

      {error && (
        <div className="error-box">
          <h4>Notice</h4>
          <p>{error}</p>
        </div>
      )}

      {/* Target Competency & Configuration */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3 className="card-title">Curriculum Target Specification</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Active Curriculum Topic
            </label>
            <input
              type="text"
              className="chat-input"
              value={currentTopic}
              disabled
              style={{ backgroundColor: 'var(--color-surface-subtle)' }}
            />
          </div>
          <div style={{ gridColumn: 'span 2' }}>
            <label style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', display: 'block', marginBottom: '6px' }}>
              Target PPS Competency
            </label>
            <input
              type="text"
              className="chat-input"
              value={targetCompetency}
              onChange={(e) => setTargetCompetency(e.target.value)}
              placeholder="e.g., Master dynamic memory allocation and pointer arithmetic in C"
              disabled={isLoading}
            />
          </div>
        </div>
      </div>

      {/* Roadmap Stages */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 className="card-title" style={{ margin: 0 }}>
            <span>Milestone Progression</span>
            <span className="badge-blue" style={{ marginLeft: '10px' }}>
              {roadmapData?.current_mastery ? `Current Mastery: ${roadmapData.current_mastery}` : `Student ${studentId}`}
            </span>
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
            Grounded in PPS Syllabus Units
          </span>
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary)' }}>
            Sequencing curriculum prerequisites and personalized milestone roadmap...
          </div>
        ) : stages.length > 0 ? (
          <div className="roadmap-list">
            {stages.map((stg, idx) => (
              <div key={idx} className="roadmap-item">
                <span className="roadmap-num">{stg.num}</span>
                <span className="roadmap-desc" style={{ fontSize: '14px', lineHeight: 1.5 }}>
                  {stg.text}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '36px', color: 'var(--color-text-secondary)' }}>
            <p style={{ marginBottom: '16px' }}>
              No custom roadmap has been generated yet for <strong>{currentTopic}</strong>.
            </p>
            <button
              type="button"
              className="btn-primary"
              onClick={handleGenerate}
            >
              Generate Personalized Roadmap
            </button>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onNavigate('learn')}
        >
          ← Back to Lesson
        </button>
        <button
          type="button"
          className="btn-primary"
          onClick={() => onNavigate('practice')}
        >
          Proceed to Practice →
        </button>
      </div>
    </div>
  );
}
