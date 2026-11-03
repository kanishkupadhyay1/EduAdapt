"""Centralized Personalization Engine for EduAdapt.

Provides deterministic, student-adaptive instructional strategies derived from
REAL StudentProfile and Learning Twin states. Strictly non-agentic.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from eduadapt.interfaces.student_model import StudentProfile


# Documented mastery thresholds
MASTERY_THRESHOLD_BEGINNER_MAX = 0.40
MASTERY_THRESHOLD_INTERMEDIATE_MAX = 0.70


@dataclass
class InstructionalStrategy:
    """Explicit pedagogical dimensions for personalized teaching."""

    explanation_depth: str
    teaching_approach: str
    cognitive_difficulty: str
    code_complexity: str
    example_selection: str
    step_granularity: str
    scaffolding_level: str
    practice_complexity: str
    diagram_type: str
    diagram_recommendation: str
    feedback_style: str
    misconception_strategy: str
    roadmap_sequencing: str
    response_structure: str
    amount_of_explanation: str
    revision_strategy: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "explanation_depth": self.explanation_depth,
            "teaching_approach": self.teaching_approach,
            "cognitive_difficulty": self.cognitive_difficulty,
            "code_complexity": self.code_complexity,
            "example_selection": self.example_selection,
            "step_granularity": self.step_granularity,
            "scaffolding_level": self.scaffolding_level,
            "practice_complexity": self.practice_complexity,
            "diagram_type": self.diagram_type,
            "diagram_recommendation": self.diagram_recommendation,
            "feedback_style": self.feedback_style,
            "misconception_strategy": self.misconception_strategy,
            "roadmap_sequencing": self.roadmap_sequencing,
            "response_structure": self.response_structure,
            "amount_of_explanation": self.amount_of_explanation,
            "revision_strategy": self.revision_strategy,
        }


@dataclass
class PersonalizationContext:
    """Normalized context and pedagogical strategy for prompt generation."""

    student_id: str
    target_topic: str
    topic_mastery: float
    overall_mastery: float
    mastery_tier: str  # "Beginner", "Intermediate", "Advanced"
    learning_pace: str  # "slow", "moderate", "fast"
    preferred_learning_style: str
    recommended_difficulty: str
    predicted_mastery_level: str
    common_misconceptions: List[str] = field(default_factory=list)
    accuracy: Optional[float] = None
    attempt_count: Optional[float] = None
    average_time_seconds: Optional[float] = None
    pattern_name: str = "General Adaptive"
    strategy: Optional[InstructionalStrategy] = None
    personalization_summary: Dict[str, str] = field(default_factory=dict)

    def get_personalization_applied_bullets(self) -> List[str]:
        """Human-readable bullet points explaining what personalization was applied."""
        if not self.strategy:
            return ["Strategy: General PPS curriculum progression"]
        return [
            f"Explanation depth: {self.strategy.explanation_depth}",
            f"Teaching approach: {self.strategy.teaching_approach}",
            f"Scaffolding level: {self.strategy.scaffolding_level}",
            f"Code complexity: {self.strategy.code_complexity}",
            f"Diagram selection: {self.strategy.diagram_type}",
            f"Practice complexity: {self.strategy.practice_complexity}",
        ]


def select_diagram_type_for_topic(topic: str, mastery_tier: str) -> str:
    """Deterministically select appropriate PPS educational diagram based on topic."""
    norm = topic.strip().lower()
    if "pointer" in norm:
        return "pointer_memory_diagram"
    elif "loop" in norm or "while" in norm or "for" in norm:
        return "loop_execution_flowchart"
    elif "cond" in norm or "if" in norm or "switch" in norm:
        return "conditional_decision_diagram"
    elif "array" in norm:
        return "array_index_memory_diagram"
    elif "function" in norm or "recursion" in norm:
        return "function_call_stack_diagram"
    elif "string" in norm:
        return "string_null_terminator_diagram"
    elif "struct" in norm or "union" in norm:
        return "struct_memory_layout_diagram"
    elif "operator" in norm or "expression" in norm:
        return "expression_evaluation_tree"
    elif "variable" in norm or "data type" in norm:
        return "variable_storage_diagram"
    else:
        return "concept_flowchart"


def build_diagram_directive(diagram_type: str, topic: str, mastery_tier: str) -> str:
    """Produce precise Mermaid generation instructions for the LLM."""
    if diagram_type == "pointer_memory_diagram":
        return (
            "Generate a Mermaid diagram (flowchart LR or TD) illustrating memory layout for pointers. "
            "Show memory addresses (e.g. 0x1000, 0x2000), variable names, stored values, and arrows "
            "indicating pointer dereferencing (*ptr -> value). Use simple node IDs with alphanumeric characters."
        )
    elif diagram_type == "loop_execution_flowchart":
        return (
            "Generate a Mermaid flowchart (flowchart TD) illustrating loop execution flow. "
            "Include 4 distinct stages: Initialization -> Condition Check (Decision diamond) -> "
            "Loop Body (if True) -> Update / Increment step -> Loop back to Condition. "
            "Also show Exit branch (if False). Keep node labels concise and valid."
        )
    elif diagram_type == "conditional_decision_diagram":
        return (
            "Generate a Mermaid flowchart (flowchart TD) showing decision branching. "
            "Display Condition test diamond { condition? }, True branch path, False/Else branch path, "
            "and convergence at subsequent code. Use clear, unescaped node labels."
        )
    elif diagram_type == "array_index_memory_diagram":
        return (
            "Generate a Mermaid diagram (flowchart LR) showing array elements in contiguous memory. "
            "Display indices (0, 1, 2, ...) above or within elements, corresponding stored values, "
            "and 0-based boundary notation arr[0] to arr[N-1]."
        )
    elif diagram_type == "function_call_stack_diagram":
        return (
            "Generate a Mermaid flowchart (flowchart TD) showing function execution. "
            "Illustrate caller (main) -> parameter passing by value -> callee stack execution -> "
            "return value back to caller."
        )
    elif diagram_type == "string_null_terminator_diagram":
        return (
            "Generate a Mermaid diagram (flowchart LR) showing null-terminated string memory cells. "
            "Show each character cell followed by the mandatory '\\0' null terminator at the final index."
        )
    else:
        return (
            f"Generate a clear Mermaid flowchart (flowchart TD) outlining the core logical flow of {topic}. "
            "Keep node IDs alphanumeric and labels clear for a PPS C programming student."
        )


class PersonalizationEngine:
    """Centralized personalization engine for PPS educational content."""

    @staticmethod
    def derive_context(
        student_profile: StudentProfile,
        topic: str,
        learning_state: Optional[Dict[str, Any]] = None,
        performance_history: Optional[str] = None,
    ) -> PersonalizationContext:
        """Derive normalized personalization context from real student profile and state.

        Does not invent missing data. When a field is unavailable, uses explicit neutral defaults.
        Topic-specific mastery takes precedence over general mastery for the topic.
        """
        raw_state = learning_state or {}

        # 1. Topic-specific mastery vs overall mastery
        topic_mastery: float
        if topic in student_profile.mastery_levels:
            topic_mastery = float(student_profile.mastery_levels[topic])
        elif "mastery" in raw_state and raw_state["mastery"] is not None:
            topic_mastery = float(raw_state["mastery"])
        else:
            topic_mastery = 0.0

        # Overall mastery from Learning Twin or average of known topic masteries
        overall_mastery: float
        if "mastery" in raw_state and raw_state["mastery"] is not None:
            overall_mastery = float(raw_state["mastery"])
        elif student_profile.mastery_levels:
            overall_mastery = sum(student_profile.mastery_levels.values()) / len(student_profile.mastery_levels)
        else:
            overall_mastery = topic_mastery

        # 2. Strict documented mastery tier evaluation
        if topic_mastery < MASTERY_THRESHOLD_BEGINNER_MAX:
            mastery_tier = "Beginner"
        elif topic_mastery < MASTERY_THRESHOLD_INTERMEDIATE_MAX:
            mastery_tier = "Intermediate"
        else:
            mastery_tier = "Advanced"

        # 3. Learning pace normalization
        raw_pace = (
            raw_state.get("learning_pace")
            or student_profile.preferred_pace
            or "moderate"
        )
        pace_str = str(raw_pace).strip().lower()
        if "slow" in pace_str or pace_str == "easy":
            normalized_pace = "slow"
        elif "fast" in pace_str:
            normalized_pace = "fast"
        else:
            normalized_pace = "moderate"

        # 4. Learning style & difficulties
        learning_style = student_profile.learning_style or "balanced"
        recommended_difficulty = str(
            raw_state.get("recommended_difficulty") or "Medium"
        )
        predicted_mastery_level = str(
            raw_state.get("predicted_mastery_level") or mastery_tier
        )

        accuracy_val = (
            float(raw_state["accuracy"])
            if "accuracy" in raw_state and raw_state["accuracy"] is not None
            else None
        )
        attempts_val = (
            float(raw_state["attempts"])
            if "attempts" in raw_state and raw_state["attempts"] is not None
            else None
        )
        time_val = (
            float(raw_state["time_taken"])
            if "time_taken" in raw_state and raw_state["time_taken"] is not None
            else None
        )

        # 5. Identify dynamic instructional pattern across student states
        diagram_type = select_diagram_type_for_topic(topic, mastery_tier)
        diagram_directive = build_diagram_directive(diagram_type, topic, mastery_tier)

        strategy, pattern_name = PersonalizationEngine._compute_strategy(
            mastery_tier=mastery_tier,
            topic_mastery=topic_mastery,
            overall_mastery=overall_mastery,
            learning_pace=normalized_pace,
            diagram_type=diagram_type,
            diagram_directive=diagram_directive,
        )

        summary = {
            "mastery_tier": mastery_tier,
            "topic_mastery": f"{topic_mastery:.2f}",
            "learning_pace": normalized_pace,
            "pattern": pattern_name,
            "explanation_depth": strategy.explanation_depth,
            "scaffolding": strategy.scaffolding_level,
            "practice_complexity": strategy.practice_complexity,
            "diagram": diagram_type,
        }

        return PersonalizationContext(
            student_id=student_profile.student_id or "Not enough data available",
            target_topic=topic,
            topic_mastery=round(topic_mastery, 3),
            overall_mastery=round(overall_mastery, 3),
            mastery_tier=mastery_tier,
            learning_pace=normalized_pace,
            preferred_learning_style=learning_style,
            recommended_difficulty=recommended_difficulty,
            predicted_mastery_level=predicted_mastery_level,
            common_misconceptions=list(student_profile.common_misconceptions or []),
            accuracy=accuracy_val,
            attempt_count=attempts_val,
            average_time_seconds=time_val,
            pattern_name=pattern_name,
            strategy=strategy,
            personalization_summary=summary,
        )

    @staticmethod
    def _compute_strategy(
        mastery_tier: str,
        topic_mastery: float,
        overall_mastery: float,
        learning_pace: str,
        diagram_type: str,
        diagram_directive: str,
    ) -> tuple[InstructionalStrategy, str]:
        """Compute the 15 pedagogical dimensions deterministically."""

        # Pattern E: Strong overall performance (>= 0.70) but topic-specific weakness (< 0.40)
        if overall_mastery >= MASTERY_THRESHOLD_INTERMEDIATE_MAX and topic_mastery < MASTERY_THRESHOLD_BEGINNER_MAX:
            pattern_name = "Strong overall foundation with topic-specific gap"
            strategy = InstructionalStrategy(
                explanation_depth="targeted foundational (bridge from familiar C programming concepts)",
                teaching_approach="analogical bridge connecting known C concepts to this new topic",
                cognitive_difficulty="introductory to this specific topic, respecting existing programming maturity",
                code_complexity="clean minimal syntax highlighting the new mechanism without trivializing",
                example_selection="focused PPS examples isolating the specific difficult mechanism",
                step_granularity="granular steps for the new topic mechanism while assuming standard syntax familiarity",
                scaffolding_level="guided scaffolding focused strictly on the gap concept",
                practice_complexity="scaffolded diagnostic practice transitioning quickly to standard application",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="supportive, recognizing prior programming capability while clarifying this topic",
                misconception_strategy="explicit comparison showing how this topic differs from already-mastered concepts",
                roadmap_sequencing="targeted prerequisite bridge followed by rapid integration with advanced curriculum",
                response_structure="structured: Bridge from Known Concepts -> Mechanics -> Code -> Edge Cases",
                amount_of_explanation="moderate and focused, avoiding redundant basic programming lectures",
                revision_strategy="targeted verification checks on the newly introduced concept",
            )
            return strategy, pattern_name

        # Pattern A: Low mastery (< 0.40) / Slow pace
        if mastery_tier == "Beginner" and learning_pace == "slow":
            pattern_name = "Low mastery / slow pace (Deep foundational support)"
            strategy = InstructionalStrategy(
                explanation_depth="foundational, terminology defined before use with intuitive real-world analogies",
                teaching_approach="step-by-step concrete breakdown, introducing one concept at a time",
                cognitive_difficulty="introductory, low cognitive load, zero ambiguous jargon",
                code_complexity="simple, short C snippets (<15 lines) with comprehensive line-by-line comments",
                example_selection="everyday intuitive analogies followed by simple C code demonstration",
                step_granularity="small, highly granular sequential steps with intermediate trace values",
                scaffolding_level="high scaffolding, explicit walkthroughs, and guided hints before full solutions",
                practice_complexity="introductory single-concept exercises with starting templates and hint ladders",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="supportive, encouraging, breaking down errors into gentle corrective hints",
                misconception_strategy="proactive clarification of common beginner pitfalls before student encounters them",
                roadmap_sequencing="sequential foundational milestones with ample reinforcement checkpoints",
                response_structure="delineated: Concept Analogy -> Syntax Breakdown -> Annotated Code -> Walkthrough -> Guided Practice",
                amount_of_explanation="thorough and detailed, leaving no implicit assumptions unexplained",
                revision_strategy="frequent conceptual check-ins and repetitive reinforcement of core primitives",
            )
            return strategy, pattern_name

        # Pattern B: Low mastery (< 0.40) / Fast pace
        if mastery_tier == "Beginner" and learning_pace == "fast":
            pattern_name = "Low mastery / fast pace (Efficient gap resolution)"
            strategy = InstructionalStrategy(
                explanation_depth="foundational but concise, zeroing in directly on the core conceptual mechanics",
                teaching_approach="direct mechanism explanation with concise remedial examples to address gaps fast",
                cognitive_difficulty="introductory to core concepts without slow pacing or verbose narrative",
                code_complexity="concise C examples demonstrating correct syntax and immediate execution flow",
                example_selection="direct, practical PPS code examples targeting the specific difficulty",
                step_granularity="moderate-sized logical steps highlighting cause and effect directly",
                scaffolding_level="focused scaffolding, providing quick diagnostic checks rather than long hand-holding",
                practice_complexity="quick-fire conceptual checks and targeted code-reading problems",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="direct, actionable, explaining exactly why an error occurred and how to fix it",
                misconception_strategy="rapid contrast tables showing correct vs incorrect code patterns",
                roadmap_sequencing="compressed remedial path focusing on core hurdles to accelerate progression",
                response_structure="compact: Core Rule -> Direct Code Demonstration -> Pitfall Contrast -> Rapid Check",
                amount_of_explanation="concise, high signal-to-noise ratio, avoiding repetitive storytelling",
                revision_strategy="rapid conceptual checkpoints verifying root understanding before moving ahead",
            )
            return strategy, pattern_name

        # Pattern C: Intermediate mastery (0.40 - 0.70) / Moderate pace
        if mastery_tier == "Intermediate":
            pattern_name = "Intermediate mastery / moderate pace (Core reinforcement & progressive challenge)"
            strategy = InstructionalStrategy(
                explanation_depth="mechanistic, explaining how the C constructs work internally and in memory",
                teaching_approach="guided code walkthroughs connecting related PPS concepts (e.g. arrays & pointers)",
                cognitive_difficulty="moderate, combining multiple syntax elements into coherent programming patterns",
                code_complexity="moderately complex C programs (15-30 lines) with structured functions and logic",
                example_selection="standard PPS laboratory and textbook problems showing realistic usage",
                step_granularity="moderate steps highlighting control flow transitions and state transformations",
                scaffolding_level="partially guided, gradually fading scaffolding as explanation progresses",
                practice_complexity="moderate application problems, code-tracing exercises, and bug-hunting tasks",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="analytical and constructive, guiding the student to identify their own logic gaps",
                misconception_strategy="highlighting subtle edge cases and explaining common runtime misunderstandings",
                roadmap_sequencing="balanced progression connecting core fundamentals to intermediate PPS topics",
                response_structure="structured: Internal Mechanics -> PPS Code Example -> Execution Trace -> Practice Challenge",
                amount_of_explanation="balanced, combining clear conceptual rationale with technical code trace",
                revision_strategy="progressive challenge problems testing both syntax and execution reasoning",
            )
            return strategy, pattern_name

        # Pattern D: High mastery (>= 0.70) / Fast pace
        if mastery_tier == "Advanced" and learning_pace == "fast":
            pattern_name = "High mastery / fast pace (Advanced depth & independent problem-solving)"
            strategy = InstructionalStrategy(
                explanation_depth="deep technical depth, memory architecture, execution reasoning, and edge cases",
                teaching_approach="analytical, first-principles exploration of C semantics and compiler behavior",
                cognitive_difficulty="advanced, including boundary conditions, memory addresses, and efficiency considerations",
                code_complexity="idiomatic, robust C code demonstrating pointer arithmetic, modularity, and clean design",
                example_selection="challenging PPS application problems, multi-function implementations, and edge cases",
                step_granularity="high-level concise architectural steps, omitting elementary syntax explanations",
                scaffolding_level="minimal scaffolding, promoting autonomous problem solving and rigorous reasoning",
                practice_complexity="challenging application scenarios, edge-case debugging, and algorithmic problems",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="concise, rigorous, and technical, focusing on optimization, safety, and edge-case coverage",
                misconception_strategy="in-depth analysis of undefined behavior, memory leaks, and pointer aliasing",
                roadmap_sequencing="accelerated roadmap emphasizing advanced PPS applications and system-level concepts",
                response_structure="technical: Concept Architecture -> Memory / System Behavior -> Idiomatic C Implementation -> Advanced Challenge",
                amount_of_explanation="dense and technical, avoiding elementary introductions or redundant analogies",
                revision_strategy="complex multi-step challenge problems requiring independent synthesis",
            )
            return strategy, pattern_name

        # Advanced tier with moderate/slow pace
        pattern_name = "Advanced mastery (Conceptual depth & edge case mastery)"
        strategy = InstructionalStrategy(
            explanation_depth="thorough technical depth with rigorous explanation of memory and execution layout",
            teaching_approach="analytical, structured walk-through of advanced C language semantics",
            cognitive_difficulty="advanced, focusing on nuances, boundary limits, and robust design",
            code_complexity="idiomatic C code with clear modular design and safety guards",
            example_selection="in-depth PPS scenarios and real-world system programming patterns",
            step_granularity="focused steps through complex mechanics like pointer indirection and stack frames",
            scaffolding_level="low scaffolding, encouraging student derivation of solutions",
            practice_complexity="advanced PPS problems requiring precise memory and pointer understanding",
            diagram_type=diagram_type,
            diagram_recommendation=diagram_directive,
            feedback_style="rigorous and pedagogical, evaluating code robustness and correctness",
            misconception_strategy="detailed examination of subtle semantic traps and undefined behavior",
            roadmap_sequencing="advanced topic mastery with depth in PPS curriculum applications",
            response_structure="structured: Deep Mechanics -> Memory Model -> Robust C Code -> Edge Case Analysis",
            amount_of_explanation="comprehensive technical explanation without elementary filler",
            revision_strategy="synthesis problems testing comprehensive understanding",
        )
        return strategy, pattern_name
