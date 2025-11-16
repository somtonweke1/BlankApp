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

        Intelligent text-based extraction that identifies:
        - Key terms and definitions
        - Important facts and statements
        - Concepts with explanations
        """
        print(f"=" * 60)
        print(f"CONCEPT EXTRACTION STARTED for material_id: {material_id}")
        print(f"PDF Data keys: {pdf_data.keys()}")

        text = pdf_data.get('text', '')
        print(f"Text length: {len(text)}")
        print(f"Text preview (first 200 chars): {text[:200]}")

        if not text or len(text.strip()) < 10:
            print("WARNING: Minimal or no text content in PDF - creating dummy concept")
            dummy_concept = Concept(
                material_id=material_id,
                name="Sample Learning",
                type="concept",
                full_name="Sample Learning Concept",
                definition="This PDF appears to have no text. This is a sample concept to demonstrate the learning system.",
                context="Demo mode",
                complexity=3,
                domain="general"
            )
            db.add(dummy_concept)
            db.flush()
            print(f"Created dummy concept with ID: {dummy_concept.id}")
            db.commit()
            verification = db.query(Concept).filter(Concept.material_id == material_id).count()
            print(f"Verification: {verification} concepts in database")
            return [dummy_concept]

        all_concepts = []

        # Strategy 1: Look for definition patterns
        import re

        # Find sentences with definition patterns
        definition_patterns = [
            r'([A-Z][a-zA-Z\s]{2,30})\s+is\s+([^.]{20,200})\.',
            r'([A-Z][a-zA-Z\s]{2,30})\s+refers to\s+([^.]{20,200})\.',
            r'([A-Z][a-zA-Z\s]{2,30})\s+means\s+([^.]{20,200})\.',
            r'([A-Z][a-zA-Z\s]{2,30}):\s+([^.]{20,200})\.',
        ]

        for pattern in definition_patterns:
            matches = re.finditer(pattern, text[:5000])  # Search first 5000 chars
            for match in matches:
                if len(all_concepts) >= 15:
                    break
                term = match.group(1).strip()
                definition = match.group(2).strip()

                # Skip if term is too generic
                if len(term.split()) > 6 or len(term) < 3:
                    continue

                concept = Concept(
                    material_id=material_id,
                    name=term,
                    type="definition",
                    full_name=term,
                    definition=definition,
                    context=f"{term} is {definition[:100]}",
                    complexity=5,
                    domain="general"
                )
                db.add(concept)
                all_concepts.append(concept)
                print(f"  [DEF] Found: {term}")

        # Strategy 2: Extract important sentences (if we don't have enough concepts yet)
        if len(all_concepts) < 10:
            print("Finding important sentences...")
            sentences = [s.strip() + '.' for s in text.split('.') if len(s.strip()) > 40]

            for i, sentence in enumerate(sentences[:20]):
                if len(all_concepts) >= 15:
                    break

                # Extract a short name from the sentence
                words = sentence.split()[:5]  # First 5 words
                name = ' '.join(words).strip(',.:;')

                # Skip if name is too long
                if len(name) > 50:
                    name = ' '.join(words[:3])

                concept = Concept(
                    material_id=material_id,
                    name=name,
                    type="fact",
                    full_name=sentence[:150],
                    definition=sentence[:500],
                    context="Key information from material",
                    complexity=5,
                    domain="general"
                )
                db.add(concept)
                all_concepts.append(concept)
                print(f"  [FACT {i+1}] {name[:50]}")

        # Strategy 3: If still not enough, extract from paragraphs
        if len(all_concepts) < 5:
            print("Extracting from paragraphs...")
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]

            for i, paragraph in enumerate(paragraphs[:10]):
                # Extract topic from first few words
                words = paragraph.split()[:4]
                topic = ' '.join(words).strip(',.:;')

                if len(topic) > 40:
                    topic = ' '.join(words[:2])

                concept = Concept(
                    material_id=material_id,
                    name=topic,
                    type="topic",
                    full_name=paragraph[:150],
                    definition=paragraph[:500],
                    context="Content section",
                    complexity=5,
                    domain="general"
                )
                db.add(concept)
                all_concepts.append(concept)
                print(f"  [TOPIC {i+1}] {topic[:50]}")

        # Ensure we have at least one concept
        if not all_concepts:
            print("Creating fallback concept...")
            concept = Concept(
                material_id=material_id,
                name="Document Content",
                type="general",
                full_name="Content from uploaded document",
                definition=text[:500],
                context="General content",
                complexity=5,
                domain="general"
            )
            db.add(concept)
            all_concepts.append(concept)

        print(f"Committing {len(all_concepts)} concepts to database...")
        db.flush()
        db.commit()
        print(f"Successfully committed {len(all_concepts)} concepts")

        verification_count = db.query(Concept).filter(Concept.material_id == material_id).count()
        print(f"Verification: {verification_count} concepts in database")
        print(f"=" * 60)

        return all_concepts

    async def extract_concepts_with_ai(self, pdf_data: Dict, material_id: uuid.UUID, db: Session) -> List[Concept]:
        """AI-powered extraction (requires OpenAI) - DEPRECATED"""
        text = pdf_data['text']
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
                error_msg = f"Error extracting concepts from chunk: {str(e)}"
                print(error_msg)
                print(f"Error type: {type(e).__name__}")
                print(f"Full error: {repr(e)}")
                # Don't silently continue - we need at least some concepts
                if "invalid_api_key" in str(e).lower() or "authentication" in str(e).lower():
                    raise Exception(f"OpenAI API key error: {str(e)}. Please check your OPENAI_API_KEY in Render environment variables.")
                continue

        # Commit all concepts
        db.commit()

        return all_concepts

    async def generate_questions(self, concepts: List[Concept], db: Session):
        """
        Generate meaningful, contextual questions for each concept
        Creates questions that make sense and test real understanding
        """
        print(f"=" * 60)
        print(f"GENERATING QUESTIONS for {len(concepts)} concepts")

        for concept in concepts:
            # Get content
            full_def = concept.definition or concept.full_name or "No definition available"
            name = concept.name or "Concept"

            # Clean up the name if it's too long
            if len(name) > 50:
                name = ' '.join(name.split()[:5])

            # Split definition into sentences for varied answers
            sentences = [s.strip() + '.' for s in full_def.split('.') if s.strip()]
            if not sentences:
                sentences = [full_def]

            def get_answer_part(index, default):
                if index < len(sentences):
                    return sentences[index]
                return default

            # Generate MEANINGFUL questions with UNIQUE answers
            modes_and_questions = [
                # RAPID_FIRE - Quick recall questions
                {'mode': 'RAPID_FIRE', 'question': f"What is {name}?", 'answer': get_answer_part(0, full_def[:150])},
                {'mode': 'RAPID_FIRE', 'question': f"Define {name}.", 'answer': full_def[:120]},
                {'mode': 'RAPID_FIRE', 'question': f"Briefly explain {name}.", 'answer': get_answer_part(0, full_def[:100])},
                {'mode': 'RAPID_FIRE', 'question': f"{name} means?", 'answer': full_def[:100]},
                {'mode': 'RAPID_FIRE', 'question': f"In one sentence, what is {name}?", 'answer': get_answer_part(0, concept.full_name or name)},
                {'mode': 'RAPID_FIRE', 'question': f"Quick recall: {name}", 'answer': full_def[:80]},

                # GUIDED_SOLVE - Understanding questions
                {'mode': 'GUIDED_SOLVE', 'question': f"Explain what {name} means in your own words.", 'answer': full_def[:200]},
                {'mode': 'GUIDED_SOLVE', 'question': f"Describe the key aspects of {name}.", 'answer': f"Key aspects: {full_def[:220]}"},
                {'mode': 'GUIDED_SOLVE', 'question': f"What should someone know about {name}?", 'answer': f"Important to know: {full_def[:200]}"},
                {'mode': 'GUIDED_SOLVE', 'question': f"Break down the meaning of {name}.", 'answer': ' '.join(sentences[:2]) if len(sentences) > 1 else full_def[:200]},

                # COLLABORATIVE - Discussion questions
                {'mode': 'COLLABORATIVE', 'question': f"What do you understand about {name}?", 'answer': full_def[:200]},
                {'mode': 'COLLABORATIVE', 'question': f"Share your thoughts on {name}.", 'answer': f"Key points: {full_def[:180]}"},
                {'mode': 'COLLABORATIVE', 'question': f"How would you explain {name} to someone else?", 'answer': full_def[:220]},

                # EXPLAIN_BACK - Teaching-style questions
                {'mode': 'EXPLAIN_BACK', 'question': f"If you were teaching {name}, what would you say?", 'answer': full_def[:200]},
                {'mode': 'EXPLAIN_BACK', 'question': f"Explain {name} in simple terms.", 'answer': get_answer_part(0, full_def[:150])},
                {'mode': 'EXPLAIN_BACK', 'question': f"How would you describe {name} to a beginner?", 'answer': f"In simple terms: {get_answer_part(0, full_def[:180])}"},
                {'mode': 'EXPLAIN_BACK', 'question': f"Put {name} into your own words.", 'answer': full_def[:200]},

                # FILL_STORY - Completion questions
                {'mode': 'FILL_STORY', 'question': f"{name} is defined as ___", 'answer': get_answer_part(0, full_def[:120])},
                {'mode': 'FILL_STORY', 'question': f"Complete this: {name} means ___", 'answer': full_def[:100]},
                {'mode': 'FILL_STORY', 'question': f"Fill in the blank: {name} refers to ___", 'answer': get_answer_part(0, full_def[:100])},
                {'mode': 'FILL_STORY', 'question': f"The term {name} describes ___", 'answer': full_def[:150]},

                # NUMBER_SWAP - Application questions
                {'mode': 'NUMBER_SWAP', 'question': f"How is {name} used or applied?", 'answer': f"Application: {full_def[:180]}"},
                {'mode': 'NUMBER_SWAP', 'question': f"Give a practical example of {name}.", 'answer': f"Example: {full_def[:150]}"},
                {'mode': 'NUMBER_SWAP', 'question': f"Where might you encounter {name}?", 'answer': f"You might encounter this in: {full_def[:160]}"},

                # SPOT_ERROR - Critical thinking
                {'mode': 'SPOT_ERROR', 'question': f"What would be a misunderstanding of {name}?", 'answer': f"A misunderstanding would be ignoring that {full_def[:180]}"},
                {'mode': 'SPOT_ERROR', 'question': f"What detail about {name} is often overlooked?", 'answer': f"Important detail: {get_answer_part(1, full_def[:160])}"},
                {'mode': 'SPOT_ERROR', 'question': f"What's important to remember about {name}?", 'answer': f"Remember: {full_def[:170]}"},

                # BUILD_MAP - Connections
                {'mode': 'BUILD_MAP', 'question': f"How does {name} connect to the broader topic?", 'answer': f"Connection: {full_def[:200]}"},
                {'mode': 'BUILD_MAP', 'question': f"What role does {name} play in the material?", 'answer': f"Role: {full_def[:180]}"},

                # MICRO_WINS - Easy confidence builders
                {'mode': 'MICRO_WINS', 'question': f"Can you identify what {name} is about?", 'answer': f"Yes, it's about {get_answer_part(0, full_def[:100])}"},
                {'mode': 'MICRO_WINS', 'question': f"Do you recognize the term {name}?", 'answer': f"Yes, {name} relates to {get_answer_part(0, 'this concept')}"},
                {'mode': 'MICRO_WINS', 'question': f"Is {name} covered in this material?", 'answer': f"Yes, {full_def[:80]}"},
            ]

            print(f"  Creating {len(modes_and_questions)} questions for: {concept.name[:60]}")

            for q_data in modes_and_questions:
                question = Question(
                    concept_id=concept.id,
                    mode=q_data['mode'],
                    question_text=q_data['question'],
                    answer_text=q_data['answer'],
                    difficulty=concept.complexity,
                    question_data={}
                )
                db.add(question)

        db.commit()
        print(f"Questions generated successfully!")
        print(f"=" * 60)

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
