import React, { useState } from 'react';

/**
 * Parses text into sections of explanations and C code blocks.
 * Extracts ```c ... ``` or ``` ... ``` blocks cleanly.
 */
function parseTeachingSections(rawContent) {
  if (!rawContent) return [];
  const parts = [];
  const codeBlockRegex = /```(?:c|C)?\s*([\s\S]*?)```/g;
  let lastIndex = 0;
  let match;

  while ((match = codeBlockRegex.exec(rawContent)) !== null) {
    if (match.index > lastIndex) {
      parts.push({
        type: 'text',
        content: rawContent.substring(lastIndex, match.index).trim(),
      });
    }
    parts.push({
      type: 'code',
      content: match[1].trim(),
    });
    lastIndex = codeBlockRegex.lastIndex;
  }

  if (lastIndex < rawContent.length) {
    parts.push({
      type: 'text',
      content: rawContent.substring(lastIndex).trim(),
    });
  }

  return parts;
}

function CodeSnippet({ code }) {
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
        <span>C Code Example</span>
        <button
          type="button"
          className="code-copy-btn"
          onClick={handleCopy}
          aria-label="Copy C code to clipboard"
        >
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="code-block">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default function TeachingContent({ teaching, studentProfile, currentTopic }) {
  const content = teaching?.generated_teaching_content || 'No teaching content generated.';
  const topic = currentTopic || 'Pointers';
  const difficulty = studentProfile?.recommended_difficulty || 'Advanced';
  const pace = studentProfile?.learning_pace || 'Fast';

  const sections = parseTeachingSections(content);

  return (
    <section className="panel" aria-labelledby="teaching-heading">
      <div className="panel-header">
        <h2 id="teaching-heading" className="panel-title">Personalized Teaching</h2>
        <span className="badge-blue">GenAI Curriculum Grounded</span>
      </div>
      <div className="panel-body">
        <div style={{ marginBottom: '14px', borderBottom: '1px solid var(--color-border)', paddingBottom: '10px' }}>
          <table className="kv-table">
            <tbody>
              <tr>
                <td className="kv-label">Topic</td>
                <td className="kv-value">{topic}</td>
              </tr>
              <tr>
                <td className="kv-label">Difficulty</td>
                <td className="kv-value">{difficulty}</td>
              </tr>
              <tr>
                <td className="kv-label">Learning Pace</td>
                <td className="kv-value">{pace}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="teaching-body">
          {sections.map((sec, idx) => {
            if (sec.type === 'code') {
              return <CodeSnippet key={idx} code={sec.content} />;
            }
            return (
              <div key={idx} style={{ marginBottom: '12px' }}>
                {sec.content}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
