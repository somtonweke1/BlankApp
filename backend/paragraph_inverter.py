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
                        "content": """You are a logical gap detector. Given an original statement and its logical opposite, identify:
1. Logical inconsistencies or contradictions
2. Missing assumptions that would make either version coherent
3. Unstated dependencies or prerequisites
4. Areas where the opposition reveals flaws in reasoning
5. Edge cases not covered by either statement

Return each gap as a JSON object with:
- "type": category of gap (assumption, contradiction, edge_case, dependency, etc.)
- "description": clear description of the gap
- "location": which part of the statements it relates to

Return only valid JSON array."""
                    },
                    {
                        "role": "user",
                        "content": f"Original: {original}\n\nInverted: {inverted}\n\nIdentify logical gaps:"
                    }
                ],
                temperature=0.4,
                max_tokens=800
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
                    'description': f"The use of '{word}' suggests an absolute claim that may have exceptions",
                    'location': 'original'
                })

        # Check for causal claims without stated mechanism
        if ' by ' in original or ' because ' in original or ' due to ' in original:
            gaps.append({
                'type': 'causal_claim',
                'description': "Causal relationship stated - mechanism or evidence may need clarification",
                'location': 'original'
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
