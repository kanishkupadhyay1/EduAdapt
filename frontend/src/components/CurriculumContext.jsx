import React from 'react';

export default function CurriculumContext({ curriculum }) {
  const chunks = curriculum?.retrieved_chunks || [];
  const count = curriculum?.retrieved_count || chunks.length;

  return (
    <section className="panel" aria-labelledby="curriculum-heading">
      <div className="panel-header">
        <h2 id="curriculum-heading" className="panel-title">Curriculum Context</h2>
        <span className="badge-blue">
          {count} Retrieved {count === 1 ? 'Chunk' : 'Chunks'}
        </span>
      </div>
      <div className="panel-body">
        {chunks.length === 0 ? (
          <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>
            No curriculum sources retrieved.
          </div>
        ) : (
          <div className="curriculum-list">
            {chunks.map((chunk, idx) => (
              <div key={idx} className="curriculum-item">
                <div className="curriculum-item-header">
                  <span>{chunk.unit_or_module || 'Unit 1'} - {chunk.topic || 'General'}</span>
                  {chunk.slide_or_page !== undefined && chunk.slide_or_page !== null && (
                    <span className="badge-gray">Slide {chunk.slide_or_page}</span>
                  )}
                </div>
                <div className="curriculum-item-source">
                  Source: {chunk.source || 'PPS Curriculum'}
                  {chunk.relevance_score !== undefined && chunk.relevance_score !== null && (
                    <span style={{ marginLeft: '10px' }}>
                      • Relevance: {chunk.relevance_score}
                    </span>
                  )}
                </div>
                {chunk.preview && (
                  <div className="curriculum-preview">
                    {chunk.preview}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
