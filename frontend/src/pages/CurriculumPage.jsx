import React, { useState, useEffect } from 'react';
import { fetchCurriculumTopics, searchCurriculum } from '../api/learningApi';

const DEFAULT_UNITS = [
  {
    unit: 'Unit 1: Fundamentals of Computing & C',
    topics: ['Variables and Data Types', 'Operators and Expressions'],
  },
  {
    unit: 'Unit 2: Control Flow & Memory',
    topics: ['Conditionals', 'Loops', 'Arrays', 'Pointers'],
  },
  {
    unit: 'Unit 3: Modular Programming & Text Processing',
    topics: ['Strings', 'Functions'],
  },
  {
    unit: 'Unit 4: Modern Scripting with Python',
    topics: ['Python Basics', 'Python Data Structures'],
  },
  {
    unit: 'Unit 5: Scientific Computing & Data Analysis',
    topics: ['NumPy', 'Pandas'],
  },
];

export default function CurriculumPage({
  currentTopic,
  onSelectTopic,
  onNavigate,
}) {
  const [units, setUnits] = useState(DEFAULT_UNITS);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);

  useEffect(() => {
    fetchCurriculumTopics()
      .then((data) => {
        if (data && data.units && data.units.length > 0) {
          setUnits(data.units);
        }
      })
      .catch((err) => console.warn('Curriculum topics load warning:', err));
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim() || isSearching) return;

    setIsSearching(true);
    setSearchError(null);
    try {
      const data = await searchCurriculum(searchQuery, 4);
      setSearchResults(data.results || []);
    } catch (err) {
      setSearchError('Curriculum search failed: ' + (err.message || 'Check backend connection'));
    } finally {
      setIsSearching(false);
    }
  };

  const handleChooseTopic = (topic) => {
    if (onSelectTopic) {
      onSelectTopic(topic);
    }
    if (onNavigate) {
      onNavigate('learn');
    }
  };

  return (
    <div className="curriculum-page">
      <header className="page-header">
        <h2 className="page-title">PPS Course Curriculum & RAG Knowledge Base</h2>
        <p className="page-subtitle">
          Explore course units and query the grounded PPTX curriculum slides indexed by Member 2's RAG system.
        </p>
      </header>

      {/* RAG Search Engine */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 className="card-title">
          <span>Curriculum Semantic RAG Search</span>
          <span className="badge-blue">PPTX Grounded</span>
        </h3>
        <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '14px' }}>
          Search curriculum slides across all 5 units for exact definitions, syntax rules, and memory representations:
        </p>

        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            className="chat-input"
            placeholder="e.g. pointer dereferencing, memory address, array indexing..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={isSearching}
          />
          <button
            type="submit"
            className="btn-primary"
            style={{ width: 'auto', padding: '0 20px' }}
            disabled={isSearching || !searchQuery.trim()}
          >
            {isSearching ? 'Searching...' : 'Search Slides'}
          </button>
        </form>

        {searchError && (
          <div className="error-box" style={{ marginTop: '14px' }} role="alert">
            <h4>Notice</h4>
            <p>{searchError}</p>
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700 }}>Retrieved Curriculum Chunks:</h4>
            {searchResults.map((res, idx) => (
              <div
                key={idx}
                style={{
                  padding: '14px',
                  backgroundColor: 'var(--color-surface-subtle)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--color-blue)' }}>
                    {res.source || 'PPS Lecture PPTX'} • Slide {res.slide_or_page || 'N/A'}
                  </span>
                  <span className="badge-gray">{res.unit_or_module} • {res.topic}</span>
                </div>
                <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', lineHeight: 1.6, whiteSpace: 'pre-line' }}>
                  {res.content || res.text}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Units & Topics Grid */}
      <div className="card">
        <h3 className="card-title">Curriculum Units & Syllabus Structure</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {units.map((u, idx) => (
            <div key={idx} style={{ borderBottom: idx < units.length - 1 ? '1px solid var(--color-border)' : 'none', paddingBottom: '14px' }}>
              <div style={{ fontWeight: 700, fontSize: '15px', marginBottom: '10px', color: 'var(--color-text-primary)' }}>
                {u.unit}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {u.topics.map((t) => {
                  const isActive = t === currentTopic;
                  return (
                    <button
                      key={t}
                      type="button"
                      className={isActive ? 'btn-primary' : 'btn-secondary'}
                      style={{ fontSize: '13px', padding: '6px 14px' }}
                      onClick={() => handleChooseTopic(t)}
                    >
                      {t} {isActive ? '★ Active' : '→'}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
