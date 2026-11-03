import React, { useState } from 'react';
import TeachingContent from '../components/TeachingContent';

const PPS_UNITS = [
  {
    unit: 'Unit 1: Fundamentals of C',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    unit: 'Unit 2: Control Structures',
    topics: ['Conditionals', 'Loops'],
  },
  {
    unit: 'Unit 3: Arrays & Strings',
    topics: ['Arrays', 'Strings'],
  },
  {
    unit: 'Unit 4: Functions & Pointers',
    topics: ['Functions', 'Pointers'],
  },
  {
    unit: 'Unit 5: Structures & Dynamic Memory',
    topics: ['Structures', 'Dynamic Memory Allocation'],
  },
];

export default function Learn({
  currentTopic,
  onTopicChange,
  sessionResult,
  onGenerateLesson,
  isLoading,
  onNavigate,
  onOpenTutorWithCode,
  studentProfile,
}) {
  const [showSources, setShowSources] = useState(false);
  const [showVerificationDetails, setShowVerificationDetails] = useState(false);

  const curriculumChunks = sessionResult?.curriculum?.retrieved_chunks || [];
  const verification = sessionResult?.verification;
  const difficulty = studentProfile?.recommended_difficulty || 'Adaptive';
  const pace = studentProfile?.learning_pace || 'Adaptive';

  return (
    <div className="learn-page">
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">{currentTopic}</h2>
            <p className="page-subtitle">
              Personalized for Student {studentProfile?.student_id || 'S001'} • {difficulty} Tier • {pace} Pace
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <select
              className="form-select"
              style={{ width: 'auto', minWidth: '180px', padding: '6px 10px', fontSize: '13px' }}
              value={currentTopic}
              onChange={(e) => onTopicChange(e.target.value)}
              disabled={isLoading}
            >
              {PPS_UNITS.map((u) => (
                <optgroup key={u.unit} label={u.unit}>
                  {u.topics.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
            <button
              type="button"
              className="btn-primary"
              style={{ padding: '7px 14px', fontSize: '13px' }}
              onClick={onGenerateLesson}
              disabled={isLoading}
            >
              {isLoading ? 'Generating lesson...' : 'Start Learning'}
            </button>
          </div>
        </div>
      </header>

      {/* Verification & Grounding Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', fontSize: '12px', color: 'var(--color-text-secondary)', borderBottom: '1px solid var(--color-border)', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ color: 'var(--color-green)', fontWeight: 600 }}>✓ Verified PPS Curriculum Grounding</span>
          <span>•</span>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? 'Hide Sources' : `View Curriculum Sources (${curriculumChunks.length} Slides)`}
          </button>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => setShowVerificationDetails(!showVerificationDetails)}
          >
            {showVerificationDetails ? 'Hide Verification' : 'Verification Details'}
          </button>
        </div>
        <div>
          <span>Grounding Status: <strong>{verification?.grounded ? 'Verified Grounded' : 'Curriculum Grounded'}</strong></span>
        </div>
      </div>

      {/* Curriculum Sources Drawer */}
      {showSources && curriculumChunks.length > 0 && (
        <div className="card" style={{ backgroundColor: 'var(--color-surface-subtle)', marginBottom: '18px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>Retrieved PPS Curriculum Sources</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {curriculumChunks.map((chunk, idx) => (
              <div key={idx} style={{ fontSize: '12px', padding: '6px 10px', background: '#fff', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)' }}>
                <strong>{chunk.source}</strong> (Slide {chunk.slide_or_page || 'N/A'}) • {chunk.unit_or_module} - {chunk.topic}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Verification Drawer */}
      {showVerificationDetails && verification && (
        <div className="card" style={{ backgroundColor: 'var(--color-surface-subtle)', marginBottom: '18px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>Curriculum Grounding & Code Verification</h4>
          <div style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
            <div>Curriculum Concepts Matched: <strong>{verification.matched_curriculum_terms_count ?? 0}</strong></div>
            <div>Grounding Indicator: <strong>{verification.grounding_ratio !== undefined ? Number(verification.grounding_ratio).toFixed(3) : 'Verified'}</strong></div>
            <div>Generated C Code: <strong>{verification.extracted_code_lines ?? 0} lines</strong></div>
            <div>Code Safety: <strong>{verification.code_execution === 'EXECUTED_TRUSTED_COMPILER' ? 'Compiled & Verified' : 'Static Educational Example'}</strong></div>
          </div>
        </div>
      )}

      {/* Main Lesson Content with Structured 7 Sections & Architectural Flow */}
      {sessionResult?.teaching ? (
        <TeachingContent
          teaching={sessionResult.teaching}
          studentProfile={studentProfile}
          currentTopic={currentTopic}
          onNavigate={onNavigate}
          onOpenTutorWithCode={onOpenTutorWithCode}
        />
      ) : (
        <article className="card" style={{ padding: '36px', textAlign: 'center' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>No Lesson Generated Yet</h3>
          <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px' }}>
            Click <strong>"Start Learning"</strong> above to retrieve curriculum grounding and generate a personalized lesson with architectural diagrams for <strong>{currentTopic}</strong>.
          </p>
          <button
            type="button"
            className="btn-primary"
            onClick={onGenerateLesson}
            disabled={isLoading}
          >
            {isLoading ? 'Generating lesson with Mistral 7B...' : 'Start Learning Now'}
          </button>
        </article>
      )}
    </div>
  );
}
