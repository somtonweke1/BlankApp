"""
Engagement Engine - The Brain of Mastery Machine

Implements:
1. Mode-switching algorithm (priority cascade)
2. Mastery detection (5 criteria)
3. Anxiety detection and rescue
4. Real-time question selection and feedback
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
from datetime import datetime, timedelta
import random
import math

from models import (
    Concept, Question, UserConceptState, Response,
    Session as SessionModel, User
)


class EngagementEngine:
    """Core engine that drives adaptive learning"""

    # Mode definitions
    MODES = {
        # Foundation modes (building understanding)
        'WORKED_EXAMPLE': {'priority': 1, 'category': 'foundation'},
        'GUIDED_SOLVE': {'priority': 2, 'category': 'foundation'},
        'COLLABORATIVE': {'priority': 3, 'category': 'foundation'},

        # Active recall modes
        'RAPID_FIRE': {'priority': 4, 'category': 'active'},
        'FILL_STORY': {'priority': 5, 'category': 'active'},
        'NUMBER_SWAP': {'priority': 6, 'category': 'active'},

        # Deep understanding modes
        'EXPLAIN_BACK': {'priority': 7, 'category': 'deep'},
        'REVERSE_ENGINEER': {'priority': 8, 'category': 'deep'},
        'SPOT_ERROR': {'priority': 9, 'category': 'deep'},

        # Mastery validation modes
        'BUILD_MAP': {'priority': 10, 'category': 'mastery'},
        'MASTERY_VALIDATION': {'priority': 11, 'category': 'mastery'},
        'MICRO_WINS': {'priority': 0, 'category': 'rescue'}  # Rescue mode
    }

    # Mastery criteria thresholds
    MASTERY_THRESHOLDS = {
        'accuracy': 0.99,
        'consecutive_perfect': 10,
        'speed_ratio': 1.3,  # Response time <= 1.3x baseline
        'format_coverage': 0.8,  # 80% of formats tested and passed
        'predicted_recall': 0.95
    }

    def __init__(self, session_id: str, user_id: str, material_id: str, db: Session):
        self.session_id = uuid.UUID(session_id)
        self.user_id = uuid.UUID(user_id)
        self.material_id = uuid.UUID(material_id)
        self.db = db

        # Load concepts for this material
        print(f"=" * 60)
        print(f"ENGAGEMENT ENGINE INIT for material_id: {self.material_id}")
        self.concepts = self.db.query(Concept).filter(
            Concept.material_id == self.material_id
        ).all()
        self.total_concepts = len(self.concepts)
        print(f"Loaded {self.total_concepts} concepts from database")
        if self.total_concepts > 0:
            for i, concept in enumerate(self.concepts[:5], 1):
                print(f"  [{i}] {concept.name[:60]}")
            if self.total_concepts > 5:
                print(f"  ... and {self.total_concepts - 5} more")
        else:
            print("WARNING: No concepts found in database!")
        print(f"=" * 60)

        # Current state
        self.current_concept: Optional[Concept] = None
        self.current_mode: Optional[str] = None
        self.sequence_number = 0

        # Track asked questions to avoid repeats
        self.asked_question_ids = set()

        # Session stats
        self.session = self.db.query(SessionModel).filter(
            SessionModel.id == self.session_id
        ).first()

    async def get_next_question(self) -> Dict:
        """
        Main algorithm: Select next concept and mode

        Priority cascade:
        1. RESCUE: Any concept in anxiety/panic state → MICRO_WINS
        2. MASTERY VALIDATION: Concepts ready for validation → MASTERY_VALIDATION
        3. OPTIMAL CHALLENGE: Select concept at optimal difficulty
        4. MODE SELECTION: Choose mode based on concept state
        """
        # Check if we have any concepts at all
        if not self.concepts:
            return None  # No concepts extracted from material

        # Step 1: Check for concepts needing rescue
        rescue_concept = await self._find_rescue_concept()
        if rescue_concept:
            self.current_concept = rescue_concept
            self.current_mode = 'MICRO_WINS'
            return await self._build_question()

        # Step 2: Check for concepts ready for mastery validation
        validation_concept = await self._find_validation_concept()
        if validation_concept:
            self.current_concept = validation_concept
            self.current_mode = 'MASTERY_VALIDATION'
            return await self._build_question()

        # Step 3: Select concept at optimal challenge level
        self.current_concept = await self._select_optimal_concept()

        # Step 4: Select appropriate mode for this concept
        self.current_mode = await self._select_mode()

        # Build and return question
        return await self._build_question()

    async def process_answer(self, answer: str, response_time_ms: int, hesitation_ms: int) -> Dict:
        """
        Process student answer and update state

        Returns:
        {
            'correct': bool,
            'explanation': str,
            'mastered': bool,
            'concept_name': str,
            'mode_switched': bool,
            'new_mode': str,
            'switch_reason': str,
            'session_complete': bool,
            'stats': dict
        }
        """
        # Get question - try for specific mode first, then fallback
        question = self.db.query(Question).filter(
            Question.concept_id == self.current_concept.id,
            Question.mode == self.current_mode
        ).first()

        if not question:
            # Fallback to any question for this concept
            print(f"WARNING: No question found for mode '{self.current_mode}', using any available question")
            question = self.db.query(Question).filter(
                Question.concept_id == self.current_concept.id
            ).first()

        if not question:
            # This shouldn't happen, but handle gracefully
            print(f"CRITICAL: No questions found for concept {self.current_concept.id}")
            return {
                'correct': False,
                'explanation': "System error: Unable to verify answer. Please continue.",
                'mastered': False,
                'concept_name': self.current_concept.name,
                'mode_switched': False,
                'session_complete': False
            }

        # Evaluate answer
        is_correct, is_partial = await self._evaluate_answer(answer, question)

        # Record response
        response = Response(
            user_id=self.user_id,
            concept_id=self.current_concept.id,
            question_id=question.id,
            session_id=self.session_id,
            mode=self.current_mode,
            user_answer=answer,
            is_correct=is_correct,
            is_partial=is_partial,
            response_time_ms=response_time_ms,
            time_to_first_keystroke_ms=hesitation_ms,
            difficulty_at_time=question.difficulty,
            sequence_number=self.sequence_number
        )
        self.db.add(response)

        # Update concept state
        concept_state = self._get_or_create_concept_state(self.current_concept.id)
        await self._update_concept_state(concept_state, is_correct, response_time_ms, hesitation_ms)

        # Check mastery
        mastered = await self._check_mastery(concept_state)

        # Update session stats
        self.session.total_questions += 1
        if is_correct:
            self.session.total_correct += 1
        if mastered:
            self.session.concepts_mastered_this_session += 1

        self.db.commit()

        # Check session completion
        session_complete = await self._check_session_complete()

        result = {
            'correct': is_correct,
            'explanation': self._generate_explanation(is_correct, question),
            'mastered': mastered,
            'concept_name': self.current_concept.name,
            'mode_switched': False,
            'session_complete': session_complete
        }

        if session_complete:
            result['stats'] = await self._get_session_stats()

        self.sequence_number += 1

        return result

    async def process_skip(self) -> Dict:
        """Handle skip action - indicates anxiety or confusion"""
        response = Response(
            user_id=self.user_id,
            concept_id=self.current_concept.id,
            question_id=None,
            session_id=self.session_id,
            mode=self.current_mode,
            is_correct=False,
            skipped=True,
            response_time_ms=0,
            sequence_number=self.sequence_number
        )
        self.db.add(response)

        # Update concept state - mark as struggling
        concept_state = self._get_or_create_concept_state(self.current_concept.id)
        concept_state.state = 'struggling'
        concept_state.hesitation_count += 1

        self.db.commit()
        self.sequence_number += 1

        return {
            'type': 'skip_recorded',
            'message': 'No problem! Let\'s try something else.'
        }

    async def process_peek(self) -> Dict:
        """Handle peek action - show answer"""
        question = self.db.query(Question).filter(
            Question.concept_id == self.current_concept.id,
            Question.mode == self.current_mode
        ).first()

        if not question:
            # Fallback to any question for this concept
            question = self.db.query(Question).filter(
                Question.concept_id == self.current_concept.id
            ).first()

        if not question:
            return {
                'type': 'peek',
                'answer': self.current_concept.definition or "No definition available",
                'explanation': 'Here is the concept definition.'
            }

        response = Response(
            user_id=self.user_id,
            concept_id=self.current_concept.id,
            question_id=question.id,
            session_id=self.session_id,
            mode=self.current_mode,
            is_correct=False,
            peeked=True,
            response_time_ms=0,
            sequence_number=self.sequence_number
        )
        self.db.add(response)
        self.db.commit()
        self.sequence_number += 1

        return {
            'type': 'peek',
            'answer': question.answer_text,
            'explanation': 'Take your time to understand this. We\'ll test it again later.'
        }

    async def get_hint(self) -> Dict:
        """Provide hint for current question"""
        question = self.db.query(Question).filter(
            Question.concept_id == self.current_concept.id,
            Question.mode == self.current_mode
        ).first()

        if not question:
            # Fallback to any question for this concept
            question = self.db.query(Question).filter(
                Question.concept_id == self.current_concept.id
            ).first()

        if not question:
            return {
                'type': 'hint',
                'hint': f"This relates to {self.current_concept.name}"
            }

        # Generate hint (first part of answer or related concept)
        hint = self._generate_hint(question)

        return {
            'type': 'hint',
            'hint': hint
        }

    async def save_session_state(self):
        """Save session when disconnected"""
        if self.session:
            self.session.end_time = datetime.now()
            duration = (self.session.end_time - self.session.start_time).total_seconds() / 60
            self.session.duration_minutes = int(duration)
            self.db.commit()

    # ===== INTERNAL METHODS =====

    async def _find_rescue_concept(self) -> Optional[Concept]:
        """Find concept where student is struggling (needs rescue mode)"""
        # Look for concepts with high skip rate or long hesitation
        recent_responses = self.db.query(Response).filter(
            Response.session_id == self.session_id,
            Response.created_at >= datetime.now() - timedelta(minutes=5)
        ).all()

        if not recent_responses:
            return None

        # Calculate skip ratio and hesitation ratio
        skip_count = sum(1 for r in recent_responses if r.skipped)
        skip_ratio = skip_count / len(recent_responses) if recent_responses else 0

        # If skip ratio > 30%, enter rescue mode
        if skip_ratio > 0.3:
            # Find concept with most skips
            concept_skips = {}
            for r in recent_responses:
                if r.skipped:
                    concept_skips[r.concept_id] = concept_skips.get(r.concept_id, 0) + 1

            if concept_skips:
                struggling_concept_id = max(concept_skips, key=concept_skips.get)
                return self.db.query(Concept).filter(Concept.id == struggling_concept_id).first()

        return None

    async def _find_validation_concept(self) -> Optional[Concept]:
        """Find concept ready for mastery validation"""
        # Look for concepts that meet criteria 1-4 but not yet validated
        concept_states = self.db.query(UserConceptState).filter(
            UserConceptState.user_id == self.user_id,
            UserConceptState.concept_id.in_([c.id for c in self.concepts]),
            UserConceptState.state == 'learning',
            UserConceptState.accuracy >= self.MASTERY_THRESHOLDS['accuracy'],
            UserConceptState.consecutive_perfect >= self.MASTERY_THRESHOLDS['consecutive_perfect']
        ).all()

        if concept_states:
            # Pick one at random
            state = random.choice(concept_states)
            return self.db.query(Concept).filter(Concept.id == state.concept_id).first()

        return None

    async def _select_optimal_concept(self) -> Concept:
        """
        Select concept at optimal difficulty level

        Uses spaced repetition + interleaving:
        - Prioritize concepts not seen recently
        - Balance between learning and reviewing
        - Avoid mastered concepts unless review needed
        """
        # Get all concept states
        concept_states = {
            cs.concept_id: cs
            for cs in self.db.query(UserConceptState).filter(
                UserConceptState.user_id == self.user_id,
                UserConceptState.concept_id.in_([c.id for c in self.concepts])
            ).all()
        }

        # Score each concept
        scores = []
        for concept in self.concepts:
            state = concept_states.get(concept.id)

            if state and state.state == 'mastered':
                # Check if review needed
                if state.next_review_at and state.next_review_at <= datetime.now():
                    scores.append((concept, 50))  # Medium priority for review
                else:
                    continue  # Skip mastered concepts not due for review

            elif state and state.state == 'struggling':
                scores.append((concept, 100))  # High priority

            elif state and state.state == 'learning':
                # Medium priority, adjusted by time since last seen
                time_since = (datetime.now() - state.updated_at).total_seconds() / 60
                score = 60 + min(time_since, 30)  # Cap at 90
                scores.append((concept, score))

            else:
                # Untouched - high priority
                scores.append((concept, 90))

        if not scores:
            # All mastered and not due for review - session complete
            if self.concepts:
                return self.concepts[0]  # Return any
            return None  # No concepts available

        # Select weighted random
        scores.sort(key=lambda x: x[1], reverse=True)

        # Take top 5 and choose randomly
        top_concepts = scores[:5]
        return random.choice(top_concepts)[0]

    async def _select_mode(self) -> str:
        """
        Select appropriate mode based on concept state

        Mode progression:
        untouched → GUIDED_SOLVE
        struggling → COLLABORATIVE
        learning → RAPID_FIRE, FILL_STORY, NUMBER_SWAP (rotate)
        proficient → EXPLAIN_BACK, SPOT_ERROR
        ready_for_validation → MASTERY_VALIDATION
        """
        state = self._get_or_create_concept_state(self.current_concept.id)

        if state.state == 'untouched':
            return 'GUIDED_SOLVE'

        elif state.state == 'struggling':
            return 'COLLABORATIVE'

        elif state.state == 'learning':
            # Rotate through active modes
            if state.total_attempts % 3 == 0:
                return 'RAPID_FIRE'
            elif state.total_attempts % 3 == 1:
                return 'FILL_STORY'
            else:
                return 'NUMBER_SWAP'

        elif state.state == 'proficient':
            # Alternate deep modes
            if state.total_attempts % 2 == 0:
                return 'EXPLAIN_BACK'
            else:
                return 'SPOT_ERROR'

        else:  # mastered
            return 'BUILD_MAP'

    async def _build_question(self) -> Dict:
        """Build question data to send to client"""
        # Get random question for this concept+mode, excluding already asked
        question_query = self.db.query(Question).filter(
            Question.concept_id == self.current_concept.id,
            Question.mode == self.current_mode
        )

        # Exclude already asked questions
        if self.asked_question_ids:
            question_query = question_query.filter(
                ~Question.id.in_(self.asked_question_ids)
            )

        question = question_query.order_by(func.random()).first()

        # If no new questions available for this mode, try fallback
        if not question:
            # Check if we've exhausted all questions for this concept+mode
            total_for_mode = self.db.query(Question).filter(
                Question.concept_id == self.current_concept.id,
                Question.mode == self.current_mode
            ).count()

            if total_for_mode > 0:
                # We've asked all questions for this mode - reset tracking for this concept
                print(f"All questions asked for {self.current_concept.name} in {self.current_mode} mode. Resetting...")
                # Remove this concept's questions from tracking
                concept_question_ids = {
                    q.id for q in self.db.query(Question).filter(
                        Question.concept_id == self.current_concept.id
                    ).all()
                }
                self.asked_question_ids -= concept_question_ids

                # Try again
                question = self.db.query(Question).filter(
                    Question.concept_id == self.current_concept.id,
                    Question.mode == self.current_mode
                ).order_by(func.random()).first()

            # If still no question, try any mode for this concept
            if not question:
                print(f"WARNING: No question found for mode '{self.current_mode}', falling back to any question for concept {self.current_concept.id}")
                question = self.db.query(Question).filter(
                    Question.concept_id == self.current_concept.id,
                    ~Question.id.in_(self.asked_question_ids) if self.asked_question_ids else True
                ).order_by(func.random()).first()

        if not question:
            # No questions at all for this concept - critical error
            print(f"CRITICAL ERROR: No questions found for concept {self.current_concept.id} - {self.current_concept.name}")
            return None

        # Track this question as asked
        self.asked_question_ids.add(question.id)
        print(f"Selected question ID {question.id} (Total asked: {len(self.asked_question_ids)})")

        # Use the question's actual mode if we fell back
        actual_mode = question.mode

        return {
            'type': 'question',
            'mode': actual_mode,
            'concept_name': self.current_concept.name,
            'question': question.question_text,
            'difficulty': question.difficulty,
            'data': question.question_data or {}
        }

    async def _evaluate_answer(self, user_answer: str, question: Question) -> tuple:
        """Evaluate if answer is correct"""
        correct_answer = question.answer_text.lower().strip()
        user_answer = user_answer.lower().strip()

        # Exact match
        if user_answer == correct_answer:
            return (True, False)

        # Partial match (fuzzy)
        similarity = self._calculate_similarity(user_answer, correct_answer)

        if similarity > 0.9:
            return (True, False)
        elif similarity > 0.7:
            return (False, True)  # Partial credit
        else:
            return (False, False)

    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate string similarity (0-1)"""
        # Simple word overlap
        words1 = set(s1.split())
        words2 = set(s2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _get_or_create_concept_state(self, concept_id: uuid.UUID) -> UserConceptState:
        """Get or create concept state for user"""
        state = self.db.query(UserConceptState).filter(
            UserConceptState.user_id == self.user_id,
            UserConceptState.concept_id == concept_id
        ).first()

        if not state:
            state = UserConceptState(
                user_id=self.user_id,
                concept_id=concept_id,
                state='untouched'
            )
            self.db.add(state)
            self.db.commit()

        return state

    async def _update_concept_state(self, state: UserConceptState, is_correct: bool,
                                   response_time_ms: int, hesitation_ms: int):
        """Update all tracking metrics"""
        # Criterion 1: Accuracy
        state.total_attempts += 1
        if is_correct:
            state.correct_attempts += 1
        state.accuracy = state.correct_attempts / state.total_attempts

        # Criterion 2: Stability
        if is_correct:
            state.consecutive_perfect += 1
            state.max_streak = max(state.max_streak, state.consecutive_perfect)
        else:
            state.consecutive_perfect = 0

        # Criterion 3: Speed
        if state.avg_response_time_ms:
            state.avg_response_time_ms = int(
                (state.avg_response_time_ms * (state.total_attempts - 1) + response_time_ms) / state.total_attempts
            )
        else:
            state.avg_response_time_ms = response_time_ms
            state.baseline_response_time_ms = response_time_ms

        if hesitation_ms > 2000:  # 2+ second hesitation
            state.hesitation_count += 1

        # Criterion 4: Format Invariance
        if self.current_mode not in state.formats_tested:
            state.formats_tested = state.formats_tested + [self.current_mode]
            if is_correct:
                state.formats_passed = state.formats_passed + [self.current_mode]

        # Criterion 5: Predicted Recall
        state.last_tested_at = datetime.now()
        state.predicted_recall_probability = self._calculate_predicted_recall(state)

        # Update state category
        if state.accuracy < 0.5:
            state.state = 'struggling'
        elif state.accuracy >= 0.99 and state.consecutive_perfect >= 10:
            state.state = 'proficient'
        elif state.accuracy >= 0.7:
            state.state = 'learning'
        else:
            state.state = 'struggling'

        self.db.commit()

    def _calculate_predicted_recall(self, state: UserConceptState) -> float:
        """
        Calculate predicted recall probability using ACT-R memory decay

        R = ln(∑ t_i^(-d))
        P = 1 / (1 + e^(-R))
        """
        if state.total_attempts == 0:
            return 0.0

        # Get all correct responses for this concept
        responses = self.db.query(Response).filter(
            Response.user_id == self.user_id,
            Response.concept_id == state.concept_id,
            Response.is_correct == True
        ).order_by(Response.created_at).all()

        if not responses:
            return 0.0

        # Calculate activation
        decay_rate = 0.5  # d parameter
        now = datetime.now()
        activation_sum = 0

        for response in responses:
            time_since = (now - response.created_at).total_seconds() / 3600  # hours
            if time_since > 0:
                activation_sum += time_since ** (-decay_rate)

        if activation_sum == 0:
            return 0.0

        activation = math.log(activation_sum)

        # Convert to probability
        probability = 1 / (1 + math.exp(-activation))

        return probability

    async def _check_mastery(self, state: UserConceptState) -> bool:
        """Check if concept meets all 5 mastery criteria"""
        if state.state == 'mastered':
            return False  # Already mastered

        # Criterion 1: Accuracy >= 99%
        if state.accuracy < self.MASTERY_THRESHOLDS['accuracy']:
            return False

        # Criterion 2: 10 consecutive perfect
        if state.consecutive_perfect < self.MASTERY_THRESHOLDS['consecutive_perfect']:
            return False

        # Criterion 3: Speed/Fluency
        if state.baseline_response_time_ms and state.avg_response_time_ms:
            speed_ratio = state.avg_response_time_ms / state.baseline_response_time_ms
            if speed_ratio > self.MASTERY_THRESHOLDS['speed_ratio']:
                return False

        # Criterion 4: Format Invariance
        if len(state.formats_tested) > 0:
            format_pass_rate = len(state.formats_passed) / len(state.formats_tested)
            if format_pass_rate < self.MASTERY_THRESHOLDS['format_coverage']:
                return False

        # Criterion 5: Predicted Recall >= 95%
        if state.predicted_recall_probability < self.MASTERY_THRESHOLDS['predicted_recall']:
            return False

        # ALL CRITERIA MET - MASTERY ACHIEVED
        state.state = 'mastered'
        state.mastered_at = datetime.now()
        state.next_review_at = datetime.now() + timedelta(days=7)

        # Update user total
        user = self.db.query(User).filter(User.id == self.user_id).first()
        user.total_concepts_mastered += 1

        self.db.commit()

        return True

    async def _check_session_complete(self) -> bool:
        """Check if session goals met"""
        # Simple: All concepts mastered
        mastered_count = self.db.query(UserConceptState).filter(
            UserConceptState.user_id == self.user_id,
            UserConceptState.concept_id.in_([c.id for c in self.concepts]),
            UserConceptState.state == 'mastered'
        ).count()

        return mastered_count >= self.total_concepts

    async def _get_session_stats(self) -> Dict:
        """Get session statistics"""
        return {
            'duration_minutes': self.session.duration_minutes,
            'total_questions': self.session.total_questions,
            'total_correct': self.session.total_correct,
            'accuracy': self.session.total_correct / self.session.total_questions if self.session.total_questions > 0 else 0,
            'concepts_mastered': self.session.concepts_mastered_this_session,
            'total_concepts': self.total_concepts
        }

    def _generate_explanation(self, is_correct: bool, question: Question) -> str:
        """Generate feedback explanation"""
        if is_correct:
            return f"Correct! {self.current_concept.definition}"
        else:
            return f"Not quite. The answer is: {question.answer_text}. {self.current_concept.definition}"

    def _generate_hint(self, question: Question) -> str:
        """Generate hint"""
        answer = question.answer_text
        if len(answer) > 20:
            return answer[:20] + "..."
        else:
            return answer[0] + "_" * (len(answer) - 1)
