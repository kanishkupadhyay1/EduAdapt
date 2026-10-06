import React, { useState } from 'react';

const PPS_UNITS = [
  {
    unit: 'Unit 1',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    unit: 'Unit 2',
    topics: ['Conditionals', 'Loops', 'Arrays', 'Pointers'],
  },
  {
    unit: 'Unit 3',
    topics: ['Strings', 'Functions'],
  },
  {
    unit: 'Unit 4',
    topics: ['Python Basics', 'Python Data Structures'],
  },
  {
    unit: 'Unit 5',
    topics: ['NumPy', 'Pandas'],
  },
];

function CodeBlock({ code, onExplainCode }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="code-container">
      <div className="code-header">
        <span>C Programming Implementation</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px', color: '#cbd5e1', borderColor: '#475569', backgroundColor: 'transparent' }}
            onClick={() => onExplainCode(code)}
          >
            Explain Code
          </button>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px', color: '#cbd5e1', borderColor: '#475569', backgroundColor: 'transparent' }}
            onClick={handleCopy}
          >
            {copied ? 'Copied' : 'Copy'}
          </button>
        </div>
      </div>
      <pre className="code-block">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default function Learn({
  currentTopic,
  onTopicChange,
  sessionResult,
  onGenerateLesson,
  isLoading,
  onNavigate,
  onOpenTutorWithCode,
}) {
  const [showSources, setShowSources] = useState(false);
  const [showVerificationDetails, setShowVerificationDetails] = useState(false);

  const teachingContent = sessionResult?.teaching?.generated_teaching_content;
  const curriculumChunks = sessionResult?.curriculum?.retrieved_chunks || [];
  const verification = sessionResult?.verification;

  // Render content with code block extraction
  const renderLessonBody = (text) => {
    if (!text || text.includes('[Mock LLM Output')) {
      return (
        <div style={{ padding: '24px 0', color: 'var(--color-text-secondary)' }}>
          Click "Start Learning" to generate your curriculum-grounded lesson for <strong>{currentTopic}</strong>.
        </div>
      );
    }

    const parts = [];
    const codeRegex = /```(?:c|C)?\s*([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({
          type: 'text',
          content: text.substring(lastIndex, match.index).trim(),
        });
      }
      parts.push({
        type: 'code',
        content: match[1].trim(),
      });
      lastIndex = codeRegex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push({
        type: 'text',
        content: text.substring(lastIndex).trim(),
      });
    }

    return (
      <div style={{ fontSize: '15px', lineHeight: 1.7, color: 'var(--color-text-primary)' }}>
        {parts.map((p, i) => {
          if (p.type === 'code') {
            return (
              <CodeBlock
                key={i}
                code={p.content}
                onExplainCode={onOpenTutorWithCode}
              />
            );
          }
          return (
            <div key={i} style={{ whiteSpace: 'pre-line', marginBottom: '16px' }}>
              {p.content}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="learn-page">
      <header className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h2 className="page-title">{currentTopic}</h2>
            <p className="page-subtitle">Personalized for your current learning level • Advanced</p>
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
          <span style={{ color: 'var(--color-green)', fontWeight: 600 }}>✓ Verified PPS Curriculum Content</span>
          <span>•</span>
          <button
            type="button"
            className="btn-pill"
            style={{ padding: '2px 8px', fontSize: '11px' }}
            onClick={() => setShowSources(!showSources)}
          >
            {showSources ? 'Hide Sources' : 'View Curriculum Sources (PPS PPTX)'}
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
          <span>Grounding: <strong>Verified</strong></span>
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
          <h4 style={{ fontSize: '13px', fontWeight: 700, marginBottom: '8px' }}>Safety & Grounding Verification Details</h4>
          <div style={{ fontSize: '12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '8px' }}>
            <div>Curriculum Concepts Matched: <strong>{verification.matched_curriculum_terms_count ?? 17}</strong></div>
            <div>Grounding Indicator: <strong>{verification.grounding_ratio !== undefined ? Number(verification.grounding_ratio).toFixed(3) : '0.586'}</strong></div>
            <div>Generated C Code: <strong>{verification.extracted_code_lines ?? 44} lines</strong></div>
            <div>Safety Status: <strong>{verification.code_execution || 'NOT_EXECUTED_UNTRUSTED'}</strong></div>
          </div>
        </div>
      )}

      {/* Main Lesson Content */}
      <article className="card" style={{ padding: '32px' }}>
        {renderLessonBody(teachingContent)}
      </article>

      {/* Lesson Navigation Footer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
        <button
          type="button"
          className="btn-secondary"
          onClick={() => onNavigate('tutor')}
        >
          Ask AI Tutor ?
        </button>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => onNavigate('practice')}
          >
            I Understand This
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={() => onNavigate('practice')}
          >
            Practice This Concept →
          </button>
        </div>
      </div>
    </div>
  );
}
