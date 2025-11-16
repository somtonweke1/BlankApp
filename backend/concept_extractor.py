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

        FALLBACK MODE: Simple text-based extraction (no AI needed)
        Splits text into paragraphs and creates concepts from each
        """
        print(f"=" * 60)
        print(f"CONCEPT EXTRACTION STARTED for material_id: {material_id}")
        print(f"PDF Data keys: {pdf_data.keys()}")

        text = pdf_data.get('text', '')
        print(f"Text length: {len(text)}")
        print(f"Text preview (first 200 chars): {text[:200]}")

        if not text or len(text.strip()) < 10:
            print("WARNING: Minimal or no text content in PDF - creating dummy concept")
            # Create a dummy concept so user can still test
            dummy_concept = Concept(
                material_id=material_id,
                name="Sample Concept",
                type="concept",
                full_name="This is a sample concept for testing",
                definition="The PDF you uploaded had no extractable text. This is a demo concept so you can still test the learning flow.",
                context="Demo",
                complexity=5,
                domain="general"
            )
            db.add(dummy_concept)
            db.flush()  # Ensure ID is generated
            print(f"Created dummy concept with ID: {dummy_concept.id}")
            db.commit()
            print("Dummy concept committed to database")

            # Verify it's in the database
            verification = db.query(Concept).filter(Concept.material_id == material_id).count()
            print(f"Verification: {verification} concepts in database for material_id {material_id}")

            return [dummy_concept]

        all_concepts = []

        # Try splitting by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 30]
        print(f"Found {len(paragraphs)} paragraphs (before limiting to 20)")

        if paragraphs:
            # Create concepts from paragraphs
            for i, paragraph in enumerate(paragraphs[:20]):  # Limit to 20 concepts
                # Extract first sentence as name
                sentences = [s.strip() for s in paragraph.split('.') if s.strip()]
                first_sentence = sentences[0] if sentences else paragraph[:50]

                concept = Concept(
                    material_id=material_id,
                    name=f"Concept {i+1}: {first_sentence[:40]}...",
                    type="concept",
                    full_name=first_sentence[:100],
                    definition=paragraph[:500],
                    context="From uploaded material",
                    complexity=min(i + 1, 10),
                    domain="general"
                )
                db.add(concept)
                all_concepts.append(concept)
                print(f"  [{i+1}] Added concept: {concept.name[:60]}")

        # If no paragraphs found, split by single newlines or sentences
        if not all_concepts:
            print("No paragraphs found, trying sentences...")
            # Try splitting by periods
            sentences = [s.strip() for s in text.split('.') if s.strip() and len(s.strip()) > 20]

            if not sentences:
                # Last resort: split by any whitespace chunks
                print("No sentences found, splitting by chunks...")
                words = text.split()
                chunk_size = 20
                sentences = [' '.join(words[i:i+chunk_size]) for i in range(0, min(len(words), 200), chunk_size)]

            for i, sentence in enumerate(sentences[:20]):
                concept = Concept(
                    material_id=material_id,
                    name=f"Topic {i+1}",
                    type="fact",
                    full_name=sentence[:100] if len(sentence) > 100 else sentence,
                    definition=sentence[:500] if len(sentence) > 500 else sentence,
                    context="From uploaded material",
                    complexity=5,
                    domain="general"
                )
                db.add(concept)
                all_concepts.append(concept)
                print(f"  [{i+1}] Added concept from sentence: {concept.name[:60]}")

        # Commit all concepts to database
        print(f"Committing {len(all_concepts)} concepts to database...")
        db.flush()  # Ensure IDs are generated
        db.commit()
        print(f"Successfully committed {len(all_concepts)} concepts")

        # Verify concepts are in database
        verification_count = db.query(Concept).filter(Concept.material_id == material_id).count()
        print(f"Verification: {verification_count} concepts in database for material_id {material_id}")
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
        Generate questions for each concept - SIMPLE MODE (no AI)
        Creates questions for ALL modes the engagement engine uses
        """
        print(f"=" * 60)
        print(f"GENERATING QUESTIONS for {len(concepts)} concepts")

        for concept in concepts:
            # Get definition text
            full_def = concept.definition or concept.full_name or "No definition available"
            name = concept.name or "Concept"

            # Split definition into sentences for varied answers
            sentences = [s.strip() + '.' for s in full_def.split('.') if s.strip()]
            if not sentences:
                sentences = [full_def]

            # Create varied answers based on definition parts
            def get_answer_part(index, default):
                if index < len(sentences):
                    return sentences[index]
                return default

            # Generate questions with UNIQUE answers for each
            modes_and_questions = [
                # RAPID_FIRE - Each question has specific answer
                {'mode': 'RAPID_FIRE', 'question': f"What is {name}?", 'answer': full_def[:150]},
                {'mode': 'RAPID_FIRE', 'question': f"Define {name}", 'answer': get_answer_part(0, full_def[:100])},
                {'mode': 'RAPID_FIRE', 'question': f"{name} is:", 'answer': get_answer_part(1, full_def[:100])},
                {'mode': 'RAPID_FIRE', 'question': f"Recall: {name}", 'answer': concept.full_name or full_def[:80]},
                {'mode': 'RAPID_FIRE', 'question': f"What does {name} mean?", 'answer': full_def[:120]},
                {'mode': 'RAPID_FIRE', 'question': f"Quick: {name}?", 'answer': get_answer_part(0, name)},

                # GUIDED_SOLVE - Progressive explanations
                {'mode': 'GUIDED_SOLVE', 'question': f"Explain {name} in your own words", 'answer': f"{name} is a concept that involves {full_def[:200]}"},
                {'mode': 'GUIDED_SOLVE', 'question': f"Describe what you know about {name}", 'answer': f"Key points about {name}: {full_def[:250]}"},
                {'mode': 'GUIDED_SOLVE', 'question': f"Walk me through {name}", 'answer': f"Understanding {name}: {full_def[:200]}"},
                {'mode': 'GUIDED_SOLVE', 'question': f"Break down {name}", 'answer': f"Let's break down {name}: {' '.join(sentences[:2]) if len(sentences) > 1 else full_def[:200]}"},

                # COLLABORATIVE - Discussion angles
                {'mode': 'COLLABORATIVE', 'question': f"Let's discuss {name}. What comes to mind?", 'answer': f"When thinking about {name}, consider: {full_def[:200]}"},
                {'mode': 'COLLABORATIVE', 'question': f"What do you think about {name}?", 'answer': f"{name} is important because {full_def[:180]}"},
                {'mode': 'COLLABORATIVE', 'question': f"Tell me what you understand about {name}", 'answer': f"My understanding of {name}: {full_def[:220]}"},

                # EXPLAIN_BACK - Different explanation styles
                {'mode': 'EXPLAIN_BACK', 'question': f"How would you describe {name}?", 'answer': f"I would describe {name} as {full_def[:180]}"},
                {'mode': 'EXPLAIN_BACK', 'question': f"In simple terms, what is {name}?", 'answer': f"Simply put, {name} is {get_answer_part(0, full_def[:150])}"},
                {'mode': 'EXPLAIN_BACK', 'question': f"Teach me about {name}", 'answer': f"Let me teach you about {name}: {full_def[:220]}"},
                {'mode': 'EXPLAIN_BACK', 'question': f"Explain {name} as if I'm new to this", 'answer': f"If you're new, {name} basically means {get_answer_part(0, full_def[:160])}"},

                # FILL_STORY - Different completion prompts
                {'mode': 'FILL_STORY', 'question': f"Complete: {name} is ___", 'answer': get_answer_part(0, full_def[:100])},
                {'mode': 'FILL_STORY', 'question': f"Fill in: {name} refers to ___", 'answer': get_answer_part(1, full_def[:120])},
                {'mode': 'FILL_STORY', 'question': f"{name} means ___", 'answer': full_def[:100]},
                {'mode': 'FILL_STORY', 'question': f"The definition of {name} is ___", 'answer': full_def[:150]},

                # NUMBER_SWAP - Application contexts
                {'mode': 'NUMBER_SWAP', 'question': f"Give an example of {name}", 'answer': f"An example of {name} would be: {full_def[:150]}"},
                {'mode': 'NUMBER_SWAP', 'question': f"How would you apply {name}?", 'answer': f"You can apply {name} by understanding that {full_def[:180]}"},
                {'mode': 'NUMBER_SWAP', 'question': f"Where do you see {name} used?", 'answer': f"{name} is used in contexts where {full_def[:160]}"},

                # SPOT_ERROR - Different error types
                {'mode': 'SPOT_ERROR', 'question': f"What's a common misconception about {name}?", 'answer': f"A common misconception is oversimplifying {name}. Actually, {full_def[:180]}"},
                {'mode': 'SPOT_ERROR', 'question': f"What's wrong with saying '{name} is simple'?", 'answer': f"This oversimplifies it. {name} actually involves {full_def[:160]}"},
                {'mode': 'SPOT_ERROR', 'question': f"Identify issues in understanding {name}", 'answer': f"Key issues: {name} requires understanding that {full_def[:170]}"},

                # BUILD_MAP - Relationship types
                {'mode': 'BUILD_MAP', 'question': f"How does {name} relate to other concepts?", 'answer': f"{name} relates to other concepts through {full_def[:200]}"},
                {'mode': 'BUILD_MAP', 'question': f"What connects to {name}?", 'answer': f"Connections to {name} include understanding {full_def[:180]}"},

                # MICRO_WINS - Easy confidence builders
                {'mode': 'MICRO_WINS', 'question': f"True or False: {name} is important", 'answer': "True - it's a key concept"},
                {'mode': 'MICRO_WINS', 'question': f"Have you heard of {name}?", 'answer': f"Yes, {name} is {get_answer_part(0, 'an important concept')}"},
                {'mode': 'MICRO_WINS', 'question': f"Can you recognize {name}?", 'answer': f"Yes, {name} can be recognized as {full_def[:100]}"},
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
