import React from 'react';

/**
 * Parses raw roadmap content into numbered stages.
 */
function parseRoadmapStages(rawText) {
  if (!rawText) return [];
  const lines = rawText.split('\n');
  const stages = [];
  const stageRegex = /^(?:(?:Stage|Step|Phase|\d+)[\s.:-]*\s*(\d+)?[.:\s-]*)?(.*)$/i;

  let counter = 1;
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;

    // Matches bullet points or numbered items
    const match = trimmed.match(/^(?:(?:\d+\.|\*|-|•)\s*)?(.*)$/);
    const content = match ? match[1].trim() : trimmed;
    if (content.length > 2) {
      stages.push({
        num: String(counter).padStart(2, '0'),
        text: content,
      });
      counter++;
    }
  }

  // Fallback to default realistic stages if LLM output was concise or raw
  if (stages.length === 0) {
    return [
      { num: '01', text: 'Basics' },
      { num: '02', text: 'Pointers' },
      { num: '03', text: 'Pointer Arithmetic' },
      { num: '04', text: 'Dynamic Allocation' },
      { num: '05', text: 'Structures' },
      { num: '06', text: 'Double Pointers' },
      { num: '07', text: 'Advanced Practice' },
      { num: '08', text: 'Project' },
      { num: '09', text: 'Final Review' },
    ];
  }

  return stages;
}

export default function Roadmap({ roadmap }) {
  const content = roadmap?.roadmap_content;
  const target = roadmap?.target_competency || 'Pointers Mastery in PPS';
  const current = roadmap?.current_mastery || 'High';

  const stages = parseRoadmapStages(content);

  return (
    <section className="panel" aria-labelledby="roadmap-heading">
      <div className="panel-header">
        <h2 id="roadmap-heading" className="panel-title">Personalized Roadmap</h2>
        <span className="badge-blue">{target}</span>
      </div>
      <div className="panel-body">
        <div style={{ marginBottom: '12px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
          Current Level: <strong>{current}</strong>
        </div>

        <div className="roadmap-list">
          {stages.map((stg, idx) => (
            <div key={idx} className="roadmap-item">
              <span className="roadmap-num">{stg.num}</span>
              <span className="roadmap-desc">{stg.text}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
