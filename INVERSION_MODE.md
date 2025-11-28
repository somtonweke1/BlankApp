# Dialectical Learning Mode (Paragraph Inversion)

## Overview

The Paragraph Inversion feature transforms passive reading into active engagement through dialectical thinking. Instead of traditional flashcards, it creates logical opposites for each paragraph and challenges you to find gaps, inconsistencies, and create innovative patches.

## How It Works

### 1. Upload Material
Upload any PDF document, just like normal.

### 2. Choose Dialectical Learning Mode
After upload, select "Dialectical Learning (Inversion Mode)" instead of the traditional question-based mode.

### 3. The Workflow

#### Step 1: Paragraph Inversion
- The system parses your PDF paragraph by paragraph
- Each paragraph is inverted using GPT-4 to create its logical opposite
- The inversion maintains the same structure and wording but flips the meaning

**Example:**
- **Original:** "Exercise improves mental health by releasing endorphins and reducing stress hormones."
- **Inverted:** "Exercise worsens mental health by suppressing endorphins and increasing stress hormones."

#### Step 2: Side-by-Side Comparison
- View a table with Original vs Inverted paragraphs
- The inverted column is highlighted to make comparison easy
- Track your progress: which paragraphs have gaps identified, which have patches created

#### Step 3: Identify Gaps
- Click "Identify Gaps" on any paragraph
- AI analyzes both the original and inverted versions
- Identifies logical inconsistencies, missing assumptions, edge cases, and contradictions
- Gaps are categorized by type:
  - **Assumption**: Unstated assumptions required for the claim
  - **Contradiction**: Internal logical contradictions
  - **Edge Case**: Scenarios not covered by the statement
  - **Dependency**: Prerequisites or conditions
  - **Causal Claim**: Mechanisms that need clarification

#### Step 4: Create Patches
- A "patch" is your innovation that reconciles the opposites
- It can be:
  - A **Principle**: A general rule that explains when each is true
  - A **Function**: A formula or process that addresses the gap
  - A **Rule**: A conditional statement
  - An **Exception**: Specific cases where the rule breaks
  - A **Condition**: Contextual factors that determine truth

- You provide:
  - Patch name (optional)
  - Patch type
  - Detailed description of how it resolves the tension
  - Creativity score (self-rated 1-10)

#### Step 5: Loop
Repeat for each paragraph in your material.

## The Learning Benefit

### Force Active Engagement
You can't passively read when you're hunting for logical gaps. Every paragraph becomes a puzzle to solve.

### Build Creativity
Creating patches requires you to think beyond the material - to invent principles that weren't explicitly stated.

### Achieve Deep Understanding
By examining both a claim and its opposite, you understand the **boundaries** of the concept, not just the concept itself.

### Improve Active Recall
The intensive processing required (read → invert → compare → identify gaps → create patch) creates strong memory traces.

### Make Boring Material Interesting
Turn dry, unrelated content into a gamified creative challenge.

## API Endpoints

### Process Material for Inversion
```
POST /api/inversion/process/{material_id}?user_id={user_id}
```
Creates inversions for all paragraphs in a material.

**Response:**
```json
{
  "material_id": "...",
  "total_paragraphs": 42,
  "inversions": [
    {
      "id": "...",
      "paragraph_number": 0,
      "page_number": 1,
      "original": "...",
      "inverted": "..."
    }
  ]
}
```

### Get All Inversions
```
GET /api/inversion/{material_id}/paragraphs?user_id={user_id}
```

### Identify Gaps
```
POST /api/inversion/identify-gaps
Body: { "inversion_id": "..." }
```

**Response:**
```json
{
  "inversion_id": "...",
  "gaps": [
    {
      "id": "...",
      "type": "assumption",
      "description": "The claim assumes...",
      "location": "original"
    }
  ]
}
```

### Create Patch
```
POST /api/inversion/create-patch?user_id={user_id}
Body: {
  "inversion_id": "...",
  "patch_name": "Context-Dependent Truth",
  "patch_description": "Exercise improves mental health when done moderately, but excessive exercise can worsen mental health through overtraining syndrome...",
  "patch_type": "principle",
  "creativity_score": 8,
  "addresses_gaps": ["gap_id_1", "gap_id_2"]
}
```

### Get Gaps for Inversion
```
GET /api/inversion/{inversion_id}/gaps
```

### Get Patches for Inversion
```
GET /api/inversion/{inversion_id}/patches
```

## Database Schema

### InversionParagraph
- `id`: UUID
- `material_id`: Reference to uploaded material
- `user_id`: Reference to user
- `paragraph_number`: Index in document
- `page_number`: Page in PDF
- `original_text`: The original paragraph
- `inverted_text`: The AI-generated opposite
- `gaps_identified`: Boolean flag
- `patch_created`: Boolean flag
- Relationships: `gaps`, `patches`

### Gap
- `id`: UUID
- `inversion_paragraph_id`: Parent inversion
- `gap_type`: Type of logical gap
- `description`: What the gap is
- `location`: "original", "inverted", or "both"
- `resolved`: Boolean

### Patch
- `id`: UUID
- `inversion_paragraph_id`: Parent inversion
- `user_id`: Creator
- `patch_name`: Optional name
- `patch_description`: The reconciliation
- `patch_type`: principle, function, rule, exception, condition
- `creativity_score`: 1-10 self-rating
- `addresses_gaps`: Array of gap IDs

## Frontend Components

### InversionMode.tsx
Entry point for the dialectical learning mode. Handles:
- Checking for existing inversions
- Triggering new inversion processing
- Rendering the InversionTable when ready

### InversionTable.tsx
Main UI component with:
- Stats dashboard (total paragraphs, gaps identified, patches created)
- Side-by-side table of original vs inverted
- Action buttons for gap identification and patch creation
- Gap modal showing identified logical gaps
- Patch modal with form for creating patches
- Display of existing patches

### App.tsx Integration
- Mode selection screen after upload
- Route to inversion mode
- State management for material info

## Usage Example

1. Upload "Introduction to Economics.pdf"
2. Choose "Dialectical Learning Mode"
3. System creates inversions (may take a moment with GPT-4)
4. You see: Paragraph 1 - "Supply increases when prices rise" vs "Supply decreases when prices rise"
5. Click "Identify Gaps"
   - Gap found: "Assumes rational actors with perfect information"
   - Gap found: "Doesn't account for production capacity constraints"
6. Click "Create Patch"
   - Name: "Law of Supply with Constraints"
   - Description: "Supply increases with price only when producers have capacity to increase production and expect the price change to be permanent. Short-term price spikes may not trigger supply increases if seen as temporary. Additionally, this assumes rational economic actors - in reality, behavioral factors may cause different responses."
   - Type: Principle
   - Creativity: 7/10
7. Repeat for all 47 paragraphs in the document

## Future Enhancements

- [ ] AI-suggested patches to inspire creativity
- [ ] Patch quality scoring based on gap coverage
- [ ] Community patches - share and vote on best patches
- [ ] Patch application - test your patch against edge cases
- [ ] Progress tracking - patches per hour, creativity trends
- [ ] Export patches as study guide
- [ ] Multi-paragraph patches that span concepts
