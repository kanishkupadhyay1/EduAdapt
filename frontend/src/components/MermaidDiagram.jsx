import React, { useEffect, useRef, useState } from 'react';

const DEFAULT_TOPIC_DIAGRAMS = {
  Pointers: `flowchart TD
    Var["Integer Variable: num = 42\\n(Address: 0x1000)"] --> Cell["Memory Cell: [ 42 ]"]
    Ptr["Pointer Variable: int *ptr = 0x1000\\n(Address: 0x2000)"] -->|Stores Address &num| Var
    Deref["Dereference Operator: *ptr"] -->|Directly Accesses Value| Cell`,
  Strings: `flowchart LR
    subgraph StringArray ["Character Array: char str[] = 'C Programming'"]
        C0["'C'\\nIndex: 0"]
        C1["' '\\nIndex: 1"]
        C2["'P'\\nIndex: 2"]
        Dots["...\\nIndex: 3..12"]
        NullTerm["'\\0'\\nIndex: 13 (ASCII: 0)"]
    end
    C0 --> C1 --> C2 --> Dots --> NullTerm
    NullTerm -->|Signifies String Boundary| End["End of String Sentinel"]`,
  'Dynamic Memory Allocation': `flowchart TD
    subgraph StackSpace ["Stack Memory"]
        Ptr["Pointer Variable: int *arr = 0x5000\\n(Size: 8 Bytes)"]
    end
    subgraph HeapSpace ["Heap Memory (Dynamic Allocation)"]
        Block["malloc(5 * sizeof(int))\\nContinuous 20-Byte Block (0x5000)"]
        E0["arr[0] : 0"]
        E1["arr[1] : 0"]
        E4["arr[4] : 0"]
    end
    Ptr -->|Points to Heap Address| Block
    Block --- E0
    Block --- E1
    Block --- E4
    Free["Deallocation: free(arr)"] -->|Releases Heap Block to OS| HeapSpace`,
  Arrays: `flowchart LR
    subgraph Memory ["Contiguous Memory Block"]
        E0["arr[0] : 10\\nOffset: 0B"]
        E1["arr[1] : 20\\nOffset: +4B"]
        E2["arr[2] : 30\\nOffset: +8B"]
        E3["arr[3] : 40\\nOffset: +12B"]
    end
    Base["Base Pointer: arr (0x1000)"] --> E0`,
  Functions: `flowchart TD
    Caller["1. main() Caller Frame"] -->|Pass Parameters by Value/Ref| Stack["2. Push Call Stack Frame"]
    Stack -->|Allocate Local Scope| Exec["3. Function Execution & Logic"]
    Exec -->|Return Result| Ret["4. Return Value & Pop Stack Frame"]
    Ret --> Caller`,
  Loops: `flowchart TD
    Init["1. Initialization (int i = 0)"] --> Cond{"2. Condition Test (i < N)?"}
    Cond -->|True| Body["3. Execute Loop Body Statements"]
    Body --> Step["4. Step / Increment (i++)"]
    Step --> Cond
    Cond -->|False| Exit["5. Terminate Loop and Exit"]`,
  Structures: `flowchart TD
    subgraph StructLayout ["struct Student (Sequential Memory Alignment)"]
        F1["int id (4 bytes)"]
        F2["char name[20] (20 bytes)"]
        F3["float gpa (4 bytes)"]
    end
    Ptr["Pointer: struct Student *s"] -->|s->id (Arrow Operator)| F1`,
  Conditionals: `flowchart TD
    Start["Evaluate Condition Expression"] --> Branch{"Condition is Non-Zero (True)?"}
    Branch -->|True| PathT["Execute if Block Body"]
    Branch -->|False| PathF["Execute else / else-if Body"]
    PathT --> Merge["Continue Sequential Execution"]
    PathF --> Merge`,
};

function getFallbackDiagram(topic = '') {
  const t = String(topic).toLowerCase();
  if (t.includes('dynamic') || t.includes('malloc') || t.includes('dma') || t.includes('heap')) {
    return DEFAULT_TOPIC_DIAGRAMS['Dynamic Memory Allocation'];
  }
  if (t.includes('string')) return DEFAULT_TOPIC_DIAGRAMS.Strings;
  if (t.includes('array')) return DEFAULT_TOPIC_DIAGRAMS.Arrays;
  if (t.includes('struct')) return DEFAULT_TOPIC_DIAGRAMS.Structures;
  if (t.includes('func') || t.includes('recur')) return DEFAULT_TOPIC_DIAGRAMS.Functions;
  if (t.includes('loop') || t.includes('for') || t.includes('while')) return DEFAULT_TOPIC_DIAGRAMS.Loops;
  if (t.includes('cond') || t.includes('if') || t.includes('switch')) return DEFAULT_TOPIC_DIAGRAMS.Conditionals;
  return DEFAULT_TOPIC_DIAGRAMS.Pointers;
}

/**
 * Robust defensive sanitization for Mermaid diagram syntax.
 */
function sanitizeMermaid(rawCode) {
  if (!rawCode) return '';
  let code = String(rawCode);

  // 1. Unescape literal \n or \\n
  code = code.replace(/\\n/g, '\n');

  // 2. Remove markdown code fences
  code = code.replace(/```(?:mermaid|flowchart)?/gi, '').replace(/```/g, '');

  // 3. Normalize lines
  let lines = code.split('\n').map((l) => l.trim()).filter(Boolean);

  // 4. Filter out any leaked C code
  lines = lines.filter((l) => {
    const lower = l.toLowerCase();
    return (
      !lower.startsWith('#include') &&
      !lower.startsWith('int main') &&
      !lower.startsWith('printf(') &&
      !lower.startsWith('return 0') &&
      !lower.startsWith('scanf(') &&
      !lower.startsWith('int ') &&
      !lower.startsWith('char ') &&
      !lower.startsWith('void ')
    );
  });

  // 5. Ensure single flowchart/graph header and quote labels
  let hasHeader = false;
  const cleanedLines = [];

  for (let line of lines) {
    if (/^(flowchart|graph)\s+[A-Za-z0-9]+/i.test(line)) {
      if (!hasHeader) {
        cleanedLines.push('flowchart TD');
        hasHeader = true;
      }
      continue;
    }

    // Fix invalid flowchart arrows:
    // Convert --|> (class inheritance) to standard flowchart arrow -->
    let processed = line.replace(/--\|>/g, '-->');
    // Convert --o or --x to standard arrow -->
    processed = processed.replace(/--[ox]/g, '-->');

    // Fix arrow syntax like A --ptr-> B or A -->ptr B to A -->|ptr| B
    processed = processed.replace(/--\s*([A-Za-z0-9_ *&.\-]+?)\s*->/g, '-->|$1|');

    // Quote unquoted node labels with special symbols like * or & or -> inside brackets
    processed = processed.replace(/([A-Za-z0-9_]+)\[([^"\]\n]+)\]/g, (match, nodeId, inner) => {
      const cleanInner = inner.replace(/"/g, "'");
      return `${nodeId}["${cleanInner}"]`;
    });

    // Fix unbracketed multi-token target after arrows: e.g. "Character --> Memory Cell"
    processed = processed.replace(/(-->|---|==>|\-\.\->)\s*([A-Za-z0-9_ ]+)(?=$|\n)/g, (match, arrow, target) => {
      const trimmedTarget = target.trim();
      if (trimmedTarget.includes(' ') && !trimmedTarget.startsWith('[') && !trimmedTarget.startsWith('"')) {
        const safeId = trimmedTarget.replace(/[^\w]/g, '_');
        return `${arrow} ${safeId}["${trimmedTarget}"]`;
      }
      return match;
    });

    cleanedLines.push(processed);
  }

  if (!hasHeader) {
    cleanedLines.unshift('flowchart TD');
  }

  return cleanedLines.join('\n');
}

export default function MermaidDiagram({ code, title, explanation, topic }) {
  const containerRef = useRef(null);
  const [svgContent, setSvgContent] = useState('');
  const [activeCode, setActiveCode] = useState(code);
  const [renderError, setRenderError] = useState(null);
  const [showCode, setShowCode] = useState(false);
  const [loading, setLoading] = useState(true);

  const cleanCode = sanitizeMermaid(activeCode || code);

  useEffect(() => {
    setActiveCode(code);
  }, [code]);

  useEffect(() => {
    let isMounted = true;
    if (!cleanCode || !cleanCode.trim()) {
      setLoading(false);
      return;
    }

    const renderDiagram = async () => {
      try {
        setLoading(true);
        setRenderError(null);

        // Check if mermaid is already available on window
        let mermaidInstance = window.mermaid;

        if (!mermaidInstance) {
          try {
            // Attempt dynamic ESM import from CDN
            const module = await import(/* @vite-ignore */ 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs');
            mermaidInstance = module.default;
            window.mermaid = mermaidInstance;
          } catch (importErr) {
            // Offline fallback
            if (isMounted) {
              setRenderError('Interactive visual renderer in offline mode. Diagram architecture displayed below.');
              setLoading(false);
            }
            return;
          }
        }

        mermaidInstance.initialize({
          startOnLoad: false,
          theme: 'neutral',
          securityLevel: 'loose',
          fontFamily: 'Inter, system-ui, sans-serif',
        });

        const id = 'mermaid_' + Math.random().toString(36).substring(2, 9);
        const { svg } = await mermaidInstance.render(id, cleanCode);

        if (isMounted) {
          setSvgContent(svg);
          setLoading(false);
        }
      } catch (err) {
        // Attempt automatic recovery using topic-grounded valid architecture
        try {
          const fallback = getFallbackDiagram(topic || title);
          const fallbackClean = sanitizeMermaid(fallback);
          const fallbackId = 'mermaid_fb_' + Math.random().toString(36).substring(2, 9);
          if (window.mermaid) {
            const { svg } = await window.mermaid.render(fallbackId, fallbackClean);
            if (isMounted) {
              setSvgContent(svg);
              setActiveCode(fallbackClean);
              setLoading(false);
              return;
            }
          }
        } catch (fbErr) {
          // Ignored
        }

        if (isMounted) {
          setRenderError(err.message || 'Diagram syntax parsing error');
          setLoading(false);
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [cleanCode, topic, title]);

  if (!cleanCode || !cleanCode.trim()) return null;

  return (
    <div className="diagram-container">
      <div className="diagram-header">
        <div className="diagram-title-group">
          <span className="diagram-badge">Architecture Diagram</span>
          <span className="diagram-title">{title || 'Architectural Flow'}</span>
        </div>
        <button
          type="button"
          className="code-copy-btn"
          onClick={() => setShowCode(!showCode)}
          aria-label="Toggle diagram source code"
        >
          {showCode ? 'Hide Source' : 'View Source'}
        </button>
      </div>

      {explanation && (
        <div className="diagram-explanation">
          {explanation}
        </div>
      )}

      <div className="diagram-body">
        {loading && <div className="diagram-loading">Rendering diagram...</div>}

        {!loading && svgContent && !renderError && (
          <div
            ref={containerRef}
            className="diagram-svg-wrapper"
            dangerouslySetInnerHTML={{ __html: svgContent }}
          />
        )}

        {renderError && (
          <div className="diagram-fallback">
            <div className="diagram-fallback-notice">
              <strong>Diagram Architecture:</strong> {renderError}
            </div>
            <pre className="diagram-fallback-code">
              <code>{cleanCode}</code>
            </pre>
          </div>
        )}
      </div>

      {showCode && !renderError && (
        <div className="diagram-source-view">
          <pre className="diagram-fallback-code">
            <code>{cleanCode}</code>
          </pre>
        </div>
      )}
    </div>
  );
}
