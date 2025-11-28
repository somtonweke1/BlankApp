"""
Patch Quality Scoring System
Evaluates user-created patches to ensure deep understanding
"""

import openai
import os
from typing import Dict, List
import json


class PatchScorer:
    """
    Scores patch quality and provides actionable feedback.
    Ensures users can't proceed with shallow understanding.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

        # Minimum score to consider mastery
        self.mastery_threshold = 7.0

    def score_patch(
        self,
        original: str,
        inverted: str,
        gaps: List[Dict],
        patch_description: str
    ) -> Dict:
        """
        Score a patch on quality (1-10) and provide detailed feedback.

        Args:
            original: Original paragraph
            inverted: Inverted paragraph
            gaps: List of identified gaps
            patch_description: User's patch description

        Returns:
            {
                'score': 8.5,
                'passed': True,
                'strengths': [...],
                'weaknesses': [...],
                'specific_feedback': "...",
                'next_steps': [...],
                'addresses_all_gaps': True
            }
        """
        if not self.api_key:
            return self._fallback_scoring(patch_description, gaps)

        try:
            # Build gaps summary
            gaps_summary = "\n".join([
                f"- {gap.get('type', 'unknown')}: {gap.get('description', '')}"
                for gap in gaps
            ])

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a strict but fair teacher evaluating student understanding.

Score the student's patch on a scale of 1-10 based on:

**Quality Criteria:**
1. **Addresses ALL gaps** (not just some) - Weight: 30%
2. **Explains HOW/WHY** the reconciliation works - Weight: 25%
3. **Provides specific conditions/contexts** (when true vs not true) - Weight: 20%
4. **Shows deep understanding** (beyond surface facts) - Weight: 15%
5. **Includes concrete examples or evidence** - Weight: 10%

**Scoring Guide:**
- 9-10: Exceptional. PhD-level synthesis. Could teach others.
- 7-8: Good. Addresses all gaps with clear reasoning.
- 5-6: Adequate. Addresses most gaps but superficial.
- 3-4: Poor. Misses key gaps or shows misunderstanding.
- 1-2: Failing. Copy-paste or irrelevant response.

**IMPORTANT:**
- Be encouraging but honest
- Give specific, actionable feedback
- Don't accept vague or generic patches
- Mastery requires score ≥7

Return ONLY valid JSON (no markdown):
{
  "score": 7.5,
  "passed": true,
  "strengths": ["Clear mechanism explanation", "Good examples"],
  "weaknesses": ["Didn't address edge case gap", "Missing conditions"],
  "specific_feedback": "You explained HOW it works well, but Gap #2 (edge cases) wasn't addressed. When does this NOT work?",
  "next_steps": ["Add: What are the exceptions?", "Specify: Under what conditions?"],
  "addresses_all_gaps": false,
  "confidence_check": "On a scale 1-10, how confident are you in this explanation?"
}"""
                    },
                    {
                        "role": "user",
                        "content": f"""**Original**: {original}

**Inverted**: {inverted}

**Identified Gaps**:
{gaps_summary}

**Student's Patch**:
{patch_description}

Evaluate this patch and return JSON with score and feedback."""
                    }
                ],
                temperature=0.3,
                max_tokens=800
            )

            result_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]

            result = json.loads(result_text)

            # Ensure all required fields exist
            result.setdefault('score', 5.0)
            result.setdefault('passed', result['score'] >= self.mastery_threshold)
            result.setdefault('strengths', [])
            result.setdefault('weaknesses', [])
            result.setdefault('specific_feedback', 'See strengths and weaknesses above.')
            result.setdefault('next_steps', [])
            result.setdefault('addresses_all_gaps', False)

            return result

        except Exception as e:
            print(f"Error scoring patch: {e}")
            return self._fallback_scoring(patch_description, gaps)

    def _fallback_scoring(self, patch_description: str, gaps: List[Dict]) -> Dict:
        """
        Simple heuristic-based scoring when API unavailable.
        """
        score = 5.0  # Start at middle
        strengths = []
        weaknesses = []

        # Check length (too short = probably shallow)
        word_count = len(patch_description.split())
        if word_count < 20:
            score -= 2
            weaknesses.append("Patch is very short - add more detail")
        elif word_count > 50:
            score += 1
            strengths.append("Detailed response")

        # Check if addresses gaps (simple keyword match)
        gaps_mentioned = 0
        for gap in gaps:
            gap_type = gap.get('type', '').lower()
            if gap_type in patch_description.lower():
                gaps_mentioned += 1

        if gaps_mentioned == len(gaps):
            score += 2
            strengths.append("Appears to address all gaps")
        elif gaps_mentioned > 0:
            score += 1
            weaknesses.append(f"Only addressed {gaps_mentioned}/{len(gaps)} gaps")
        else:
            score -= 1
            weaknesses.append("Doesn't clearly address identified gaps")

        # Check for depth indicators
        depth_indicators = ['because', 'when', 'if', 'however', 'depends on', 'context', 'condition']
        depth_count = sum(1 for indicator in depth_indicators if indicator in patch_description.lower())

        if depth_count >= 3:
            score += 1
            strengths.append("Shows contextual thinking")
        elif depth_count == 0:
            score -= 1
            weaknesses.append("Lacks nuance - add conditions/context")

        # Cap score at 10
        score = min(10.0, max(1.0, score))

        return {
            'score': round(score, 1),
            'passed': score >= self.mastery_threshold,
            'strengths': strengths if strengths else ["You attempted the patch"],
            'weaknesses': weaknesses if weaknesses else ["Add more depth and detail"],
            'specific_feedback': f"Score: {score}/10. {'PASSED' if score >= self.mastery_threshold else 'NEEDS REVISION'}. Focus on addressing ALL gaps with specific details.",
            'next_steps': [
                "Address each gap explicitly",
                "Explain HOW and WHY",
                "Add specific examples",
                "Include conditions/context"
            ],
            'addresses_all_gaps': gaps_mentioned == len(gaps)
        }

    def get_socratic_help(
        self,
        original: str,
        inverted: str,
        gaps: List[Dict],
        failed_patch: str,
        failure_reason: str
    ) -> Dict:
        """
        Provide Socratic guidance when user is stuck.

        Returns:
            {
                'questions': [...],
                'hints': [...],
                'encouragement': "..."
            }
        """
        if not self.api_key:
            return self._fallback_socratic_help(gaps)

        try:
            gaps_summary = "\n".join([
                f"- {gap.get('type', 'unknown')}: {gap.get('description', '')}"
                for gap in gaps
            ])

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Socratic tutor helping a student who is stuck.

Your goal: Guide them to discover the answer themselves through questions.

**Rules:**
- Never give direct answers
- Ask 3-4 thought-provoking questions
- Each question should reveal a different angle
- Be encouraging and supportive
- Questions should be specific to their gaps

**Format:**
Return JSON with:
{
  "questions": [
    "When you say X causes Y, what EXACTLY is the mechanism?",
    "Can you think of a situation where X exists but Y doesn't happen?",
    "What would need to be TRUE for both the original and inverted to make sense?"
  ],
  "hints": [
    "Think about the CONDITIONS under which this is true",
    "Consider EXCEPTIONS or EDGE CASES"
  ],
  "encouragement": "You're on the right track! Let's dig deeper into the mechanism..."
}"""
                    },
                    {
                        "role": "user",
                        "content": f"""The student is struggling with this paragraph:

**Original**: {original}
**Inverted**: {inverted}

**Gaps to Address**:
{gaps_summary}

**Their Attempt**: {failed_patch}

**Why It Failed**: {failure_reason}

Provide Socratic questions to guide them (return JSON only)."""
                    }
                ],
                temperature=0.7,
                max_tokens=600
            )

            result_text = response.choices[0].message.content.strip()

            # Remove markdown if present
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]

            return json.loads(result_text)

        except Exception as e:
            print(f"Error getting Socratic help: {e}")
            return self._fallback_socratic_help(gaps)

    def _fallback_socratic_help(self, gaps: List[Dict]) -> Dict:
        """Provide basic Socratic questions when API unavailable."""
        questions = [
            "What is the MECHANISM? How does X lead to Y?",
            "Under what CONDITIONS is this true? When is it NOT true?",
            "What ASSUMPTIONS are being made here?"
        ]

        # Add gap-specific questions
        for gap in gaps[:2]:  # First 2 gaps
            gap_type = gap.get('type', '')
            if 'causal' in gap_type.lower():
                questions.append("HOW exactly does the cause produce the effect?")
            elif 'assumption' in gap_type.lower():
                questions.append("What would need to be true for this to work?")
            elif 'context' in gap_type.lower():
                questions.append("In what situations does this apply vs not apply?")

        return {
            'questions': questions[:4],  # Max 4 questions
            'hints': [
                "Think about specific examples",
                "Consider edge cases and exceptions",
                "Explain the 'why' not just the 'what'"
            ],
            'encouragement': "You're getting there! These questions will help you think more deeply about the issue."
        }
