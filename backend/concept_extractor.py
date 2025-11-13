"""
AI-Powered Concept Extraction and Question Generation
Uses OpenAI API to extract testable concepts and generate multi-mode questions
"""
import openai
import os
import json
from typing import Dict, List
import uuid
from sqlalchemy.orm import Session

from models import Concept, Question


class ConceptExtractor:
    """Extract concepts and generate questions using AI"""

    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4"

    async def extract_concepts(self, pdf_data: Dict, material_id: uuid.UUID, db: Session) -> List[Concept]:
        """
        Extract testable concepts from PDF content

        For each concept, we extract:
        - name: Short identifier
        - type: 'definition', 'formula', 'theorem', 'process', 'fact'
        - full_name: Complete formal name
        - definition: Clear explanation
        - context: Where/how it's used
        - complexity: 1-10 scale
        - domain: Subject area
        - formulas: Mathematical representations
        - examples: Concrete examples
        - related_concepts: Dependencies and connections
        """
        text = pdf_data['text']

        # Split into chunks if text is too long
        chunks = self._chunk_text(text, max_tokens=6000)

        all_concepts = []

        for chunk in chunks:
            prompt = f"""You are an expert learning scientist. Analyze this educational content and extract ALL testable concepts.

For each concept, provide:
1. name: Short identifier (2-5 words)
2. type: One of: definition, formula, theorem, process, fact, principle
3. full_name: Complete formal name
4. definition: Clear, complete explanation
5. context: Where/how it's used
6. complexity: 1-10 (1=basic fact, 10=advanced synthesis)
7. domain: Subject area (e.g., "calculus", "biology", "history")
8. formulas: List of mathematical formulas (if applicable)
9. examples: List of concrete examples
10. related_concepts: List of concept names this depends on or relates to
11. dependencies: List of prerequisite concepts

Content:
{chunk}

Return a JSON array of concepts. Be comprehensive - extract EVERY testable piece of knowledge.

Example:
[
  {{
    "name": "Pythagorean Theorem",
    "type": "theorem",
    "full_name": "Pythagorean Theorem for Right Triangles",
    "definition": "In a right triangle, the square of the hypotenuse equals the sum of squares of the other two sides",
    "context": "Used to find unknown side lengths in right triangles, foundational for trigonometry and distance calculations",
    "complexity": 4,
    "domain": "geometry",
    "formulas": ["a² + b² = c²"],
    "examples": ["Triangle with sides 3, 4, 5", "Finding diagonal of rectangle"],
    "related_concepts": ["right triangle", "hypotenuse", "squares"],
    "dependencies": ["basic algebra", "square roots"]
  }}
]
"""

            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert at analyzing educational content and extracting testable concepts. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )

                content = response.choices[0].message.content.strip()

                # Extract JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                concepts_data = json.loads(content)

                # Create Concept objects
                for concept_data in concepts_data:
                    concept = Concept(
                        material_id=material_id,
                        name=concept_data.get('name'),
                        type=concept_data.get('type'),
                        full_name=concept_data.get('full_name'),
                        definition=concept_data.get('definition'),
                        context=concept_data.get('context'),
                        complexity=concept_data.get('complexity', 5),
                        domain=concept_data.get('domain'),
                        formulas=concept_data.get('formulas', []),
                        examples=concept_data.get('examples', []),
                        related_concepts=concept_data.get('related_concepts', []),
                        dependencies=concept_data.get('dependencies', [])
                    )
                    db.add(concept)
                    all_concepts.append(concept)

            except Exception as e:
                print(f"Error extracting concepts from chunk: {e}")
                continue

        # Commit all concepts
        db.commit()

        return all_concepts

    async def generate_questions(self, concepts: List[Concept], db: Session):
        """
        Generate questions for each concept across different modes

        Modes to generate:
        - RAPID_FIRE: Quick recall questions
        - FILL_STORY: Fill-in-the-blank in context
        - EXPLAIN_BACK: Explain concept in own words
        - NUMBER_SWAP: Apply formula with different numbers
        - SPOT_ERROR: Find mistake in example
        - BUILD_MAP: Show relationships between concepts
        """
        for concept in concepts:
            # Generate 2 questions per mode
            modes = [
                'RAPID_FIRE',
                'FILL_STORY',
                'EXPLAIN_BACK',
                'NUMBER_SWAP',
                'SPOT_ERROR',
                'BUILD_MAP'
            ]

            for mode in modes:
                try:
                    questions = await self._generate_mode_questions(concept, mode, count=2)

                    for q_data in questions:
                        question = Question(
                            concept_id=concept.id,
                            mode=mode,
                            question_text=q_data['question'],
                            answer_text=q_data['answer'],
                            difficulty=q_data.get('difficulty', 5),
                            question_data=q_data.get('data', {})
                        )
                        db.add(question)

                except Exception as e:
                    print(f"Error generating {mode} questions for {concept.name}: {e}")
                    continue

        db.commit()

    async def _generate_mode_questions(self, concept: Concept, mode: str, count: int = 2) -> List[Dict]:
        """Generate questions for specific mode"""

        prompt = self._get_mode_prompt(concept, mode, count)

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at creating effective learning questions. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            questions = json.loads(content)
            return questions

        except Exception as e:
            print(f"Error generating questions: {e}")
            return []

    def _get_mode_prompt(self, concept: Concept, mode: str, count: int) -> str:
        """Get prompt for specific question mode"""

        base_info = f"""Concept: {concept.name}
Type: {concept.type}
Definition: {concept.definition}
Context: {concept.context}
Formulas: {concept.formulas}
Examples: {concept.examples}
"""

        if mode == 'RAPID_FIRE':
            return f"""{base_info}

Generate {count} rapid-fire recall questions that can be answered in one word or short phrase.
These should test immediate recall of key facts.

Return JSON array:
[
  {{
    "question": "What is...",
    "answer": "short answer",
    "difficulty": 3,
    "data": {{"type": "rapid_fire"}}
  }}
]
"""

        elif mode == 'FILL_STORY':
            return f"""{base_info}

Generate {count} fill-in-the-blank questions embedded in a contextual sentence or story.
The blank should be the key concept or term.

Return JSON array:
[
  {{
    "question": "In a right triangle, the _____ is the longest side.",
    "answer": "hypotenuse",
    "difficulty": 4,
    "data": {{"type": "fill_blank", "context": "geometry"}}
  }}
]
"""

        elif mode == 'EXPLAIN_BACK':
            return f"""{base_info}

Generate {count} questions asking the student to explain the concept in their own words.
These test deep understanding, not memorization.

Return JSON array:
[
  {{
    "question": "Explain in your own words what the Pythagorean theorem tells us about right triangles.",
    "answer": "A model answer explaining the concept clearly",
    "difficulty": 6,
    "data": {{"type": "explain", "requires": "understanding"}}
  }}
]
"""

        elif mode == 'NUMBER_SWAP':
            return f"""{base_info}

Generate {count} questions that apply formulas or calculations with different numbers.
Test ability to use the concept, not just recall it.

Return JSON array:
[
  {{
    "question": "Find the hypotenuse of a right triangle with sides 5 and 12.",
    "answer": "13",
    "difficulty": 5,
    "data": {{"type": "calculation", "values": {{"a": 5, "b": 12}}}}
  }}
]
"""

        elif mode == 'SPOT_ERROR':
            return f"""{base_info}

Generate {count} questions with an intentional error that the student must identify.
This tests critical thinking and deep understanding.

Return JSON array:
[
  {{
    "question": "A student says: 'In a right triangle with sides 3 and 4, the hypotenuse is 5 because 3+4=7, and 7+5=12.' What's wrong with this reasoning?",
    "answer": "The student added sides instead of using the Pythagorean theorem (a² + b² = c²). The correct calculation is 3² + 4² = 9 + 16 = 25 = 5².",
    "difficulty": 7,
    "data": {{"type": "error_detection", "error_type": "wrong_operation"}}
  }}
]
"""

        elif mode == 'BUILD_MAP':
            return f"""{base_info}

Generate {count} questions asking student to show relationships between this concept and related concepts.
Tests ability to see the bigger picture.

Return JSON array:
[
  {{
    "question": "How does the Pythagorean theorem relate to: (a) distance formula, (b) trigonometry, (c) circles?",
    "answer": "Model answer showing connections",
    "difficulty": 8,
    "data": {{"type": "relationships", "related": ["distance formula", "trigonometry", "circles"]}}
  }}
]
"""

        return ""

    def _chunk_text(self, text: str, max_tokens: int = 6000) -> List[str]:
        """Split text into chunks that fit within token limit"""
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4

        if len(text) <= max_chars:
            return [text]

        chunks = []
        current_chunk = ""

        # Split by paragraphs
        paragraphs = text.split('\n\n')

        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = para + '\n\n'

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
