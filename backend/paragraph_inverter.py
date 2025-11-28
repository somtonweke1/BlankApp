"""
Paragraph Inversion Module
Creates logical opposites of paragraphs while maintaining the same structure and wording.
"""

import openai
import os
from typing import Dict, List, Tuple
import re


class ParagraphInverter:
    """
    Inverts paragraphs to create their logical opposites.
    Uses GPT-4 to intelligently negate while preserving structure.
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key

    def invert_paragraph(self, original: str) -> str:
        """
        Create the logical opposite of a paragraph while maintaining exact structure.

        Args:
            original: The original paragraph text

        Returns:
            The inverted (opposite) paragraph
        """
        if not self.api_key:
            return self._fallback_inversion(original)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a logical inversion specialist. Your task is to create the EXACT OPPOSITE of any given paragraph while:
1. Maintaining the SAME sentence structure
2. Using the SAME grammatical patterns
3. Keeping similar word count
4. Only inverting the MEANING/LOGIC, not the form

Examples:
Original: "The economy grew rapidly in 2020, driven by technological innovation and increased consumer spending."
Inverted: "The economy shrank rapidly in 2020, hindered by technological stagnation and decreased consumer spending."

Original: "Exercise improves mental health by releasing endorphins and reducing stress hormones."
Inverted: "Exercise worsens mental health by suppressing endorphins and increasing stress hormones."

Be precise. Every claim should become its opposite."""
                    },
                    {
                        "role": "user",
                        "content": f"Invert this paragraph:\n\n{original}"
                    }
                ],
                temperature=0.3,
                max_tokens=500
            )

            inverted = response.choices[0].message.content.strip()
            return inverted

        except Exception as e:
            print(f"Error with OpenAI inversion: {e}")
            return self._fallback_inversion(original)

    def _fallback_inversion(self, original: str) -> str:
        """
        Simple rule-based inversion when GPT-4 is unavailable.
        """
        # Basic negation patterns
        inversions = {
            r'\bis\b': 'is not',
            r'\bare\b': 'are not',
            r'\bwas\b': 'was not',
            r'\bwere\b': 'were not',
            r'\bcan\b': 'cannot',
            r'\bwill\b': 'will not',
            r'\bshould\b': 'should not',
            r'\bmust\b': 'must not',
            r'\bgood\b': 'bad',
            r'\bbad\b': 'good',
            r'\bincrease': 'decrease',
            r'\bdecrease': 'increase',
            r'\bgrow': 'shrink',
            r'\bshrink': 'grow',
            r'\bimprove': 'worsen',
            r'\bworsen': 'improve',
            r'\bpositive': 'negative',
            r'\bnegative': 'positive',
            r'\bsuccess': 'failure',
            r'\bfailure': 'success',
            r'\bmore\b': 'less',
            r'\bless\b': 'more',
            r'\bhigh': 'low',
            r'\blow\b': 'high',
            r'\bstrong': 'weak',
            r'\bweak': 'strong',
            r'\bfast': 'slow',
            r'\bslow': 'fast',
        }

        inverted = original
        for pattern, replacement in inversions.items():
            inverted = re.sub(pattern, replacement, inverted, flags=re.IGNORECASE)

        return inverted

    def batch_invert(self, paragraphs: List[str]) -> List[Dict[str, str]]:
        """
        Invert multiple paragraphs.

        Args:
            paragraphs: List of paragraph texts

        Returns:
            List of dicts with 'original', 'inverted', and 'id' keys
        """
        results = []
        for idx, paragraph in enumerate(paragraphs):
            if paragraph.strip():  # Skip empty paragraphs
                results.append({
                    'id': idx,
                    'original': paragraph,
                    'inverted': self.invert_paragraph(paragraph)
                })
        return results

    def identify_gaps(self, original: str, inverted: str) -> List[Dict[str, str]]:
        """
        Identify logical gaps or inconsistencies between original and inverted paragraphs.
        These are areas where the inversion reveals contradictions or missing logic.

        Args:
            original: Original paragraph
            inverted: Inverted paragraph

        Returns:
            List of identified gaps with type and description
        """
        gaps = []

        # Use GPT-4 to identify gaps
        if not self.api_key:
            return self._fallback_gap_detection(original, inverted)

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a Socratic gap detector helping students think critically. When given a statement and its opposite, identify logical gaps that reveal deeper questions.

For each gap, ask questions that help the student understand boundaries and conditions:

Gap Types:
- "assumption": Unstated beliefs that must be true
- "mechanism": How/why does X cause Y? What's missing?
- "context": When/where is this true vs false?
- "edge_case": Scenarios not covered by the statement
- "comparison": Compared to what? By how much?
- "evidence": What proof exists? How do we know?

Description format: Use QUESTIONS that prompt thinking:
✅ "HOW does X cause Y? What's the mechanism? Under what conditions?"
✅ "When is this true vs NOT true? What context matters?"
✅ "What assumptions must hold for this to work?"
❌ "Mechanism unclear" (too vague)
❌ "Missing context" (not helpful)

Return JSON array of 2-4 most insightful gaps:
[{"type": "mechanism", "description": "HOW does...", "location": "original"}]"""
                    },
                    {
                        "role": "user",
                        "content": f"Original: {original}\n\nInverted: {inverted}\n\nIdentify the most thought-provoking logical gaps (2-4):"
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )

            import json
            gaps = json.loads(response.choices[0].message.content.strip())
            return gaps

        except Exception as e:
            print(f"Error detecting gaps: {e}")
            return self._fallback_gap_detection(original, inverted)

    def _fallback_gap_detection(self, original: str, inverted: str) -> List[Dict[str, str]]:
        """
        Simple heuristic-based gap detection.
        """
        gaps = []

        # Check for absolute statements that might have exceptions
        absolute_words = ['all', 'every', 'always', 'never', 'none', 'no one', 'everyone']
        for word in absolute_words:
            if re.search(rf'\b{word}\b', original, re.IGNORECASE):
                gaps.append({
                    'type': 'absolute_statement',
                    'description': f"Uses absolute term '{word}' - are there ANY exceptions? What conditions make this always/never true?",
                    'location': 'original'
                })

        # Check for causal claims without stated mechanism
        causal_indicators = [
            (' by ', 'by'),
            (' because ', 'because'),
            (' due to ', 'due to'),
            (' causes ', 'causes'),
            (' results in ', 'results in'),
            (' leads to ', 'leads to')
        ]

        for phrase, keyword in causal_indicators:
            if phrase in original.lower():
                gaps.append({
                    'type': 'causal_claim',
                    'description': f"States that X causes Y ('{keyword}') - HOW does it cause this? What's the mechanism? What evidence supports this? Are there conditions where this doesn't happen?",
                    'location': 'original'
                })
                break  # Only add one causal gap

        # Check for comparative claims
        comparative_words = ['better', 'worse', 'more', 'less', 'higher', 'lower', 'greater', 'smaller']
        for word in comparative_words:
            if re.search(rf'\b{word}\b', original, re.IGNORECASE):
                gaps.append({
                    'type': 'comparison',
                    'description': f"Makes comparison ('{word}') - compared to WHAT? Under what conditions? By how much?",
                    'location': 'original'
                })
                break  # Only add one comparison gap

        # Check for claims without context
        if len(original.split()) > 20 and ',' not in original and ' if ' not in original.lower() and ' when ' not in original.lower():
            gaps.append({
                'type': 'missing_context',
                'description': "Long statement without conditions - when is this true? When is it NOT true? What context matters?",
                'location': 'both'
            })

        # If no gaps found, add a generic one to prompt thinking
        if not gaps:
            gaps.append({
                'type': 'assumption',
                'description': "What assumptions does this statement make? What would need to be true for both the original AND inverted to make sense in different contexts?",
                'location': 'both'
            })

        return gaps


def create_patch_prompt(original: str, inverted: str, gaps: List[Dict[str, str]]) -> str:
    """
    Generate a prompt to help user create a patch that reconciles the gaps.

    Args:
        original: Original paragraph
        inverted: Inverted paragraph
        gaps: List of identified gaps

    Returns:
        A structured prompt for patch creation
    """
    gap_list = "\n".join([f"- {gap['type']}: {gap['description']}" for gap in gaps])

    return f"""
ORIGINAL STATEMENT:
{original}

INVERTED STATEMENT:
{inverted}

IDENTIFIED GAPS:
{gap_list}

YOUR TASK:
Create a "patch" - a function, rule, or principle that reconciles these opposites and addresses the gaps.
This patch should:
1. Resolve the logical tension between the statements
2. Address each identified gap
3. Create a more nuanced understanding

What is your patch?
"""
