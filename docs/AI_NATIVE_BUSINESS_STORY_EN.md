# AI-native business story — submission draft

*Target length: 500–1,000 words. Replace every bracketed field with verified
facts before submitting. Do not claim revenue, users, jobs or production usage
that cannot be documented.*

## Company and origin

IARH is an AI Career Growth Coach built to make high-quality interview practice
more accessible. The project began when `[FOUNDER NAME / TEAM]` identified a
practical gap: many candidates can find generic interview advice, but cannot
afford repeated expert coaching or receive structured feedback after each
attempt. IARH turns an interview attempt into a repeatable learning loop: a
candidate selects a target role, answers realistic questions, receives evidence-
based feedback, and uses a progress record to decide what to practice next.

The project was created during the hackathon period beginning `[VERIFIED START
DATE]`. The team used generic frameworks and SDKs, which are disclosed in
`docs/THIRD_PARTY_LICENSES.md`; the product workflow, backend, user experience
and AI orchestration are the team's own work.

## How the business runs with AI every day

The core operating workflow is AI-native. When a candidate completes an
interview, the platform gathers the question, answer and, where authorized,
transcript. The backend calculates the measurable score boundaries and sends a
structured request to Gemini through Vertex AI. Gemini returns competency
feedback, observable evidence, strengths, weaknesses and concrete next steps.
The result is stored as a report so the candidate can compare future attempts.

AI performs the repeatable analysis that would otherwise require a recruiter or
coach to review every answer manually. It helps generate interview questions,
classify competency evidence, summarize performance and personalize the next
practice plan. The application does not allow the model to silently alter the
numeric score: the backend calculates and constrains scores, validates the
structured response and records the provider and model used for the report.

The team remains responsible for product strategy, evaluation criteria,
security, consent, quality review, customer support, financial decisions and
escalation of model failures. Human review is required for sensitive customer
issues and for interpreting evidence where the model is uncertain. This
division lets a small team operate a coaching service while preserving human
accountability.

## Economic opportunity and jobs

IARH is intended to create opportunities beyond the founding team by helping
job seekers improve their interview performance and by creating demand for
human specialists who can design competency frameworks, review difficult cases,
produce domain-specific question sets and support partner organizations. The
current verified opportunities are: `[LIST REAL ROLES, CONTRACTS, OR NONE]`.
The current number of people served is `[REAL USER COUNT]`, with an anonymized
profile described as `[REAL USER PROFILE]`.

As adoption grows, the business can support local coaches, employability
organizations, training providers and subject-matter experts who contribute
validated content and quality review. AI handles high-volume preparation and
first-pass feedback; people remain valuable for context, trust, accessibility,
partnerships and complex coaching. This is an augmentation model rather than a
claim that AI replaces every professional role.

## Category impact and sustainability

IARH belongs to the Education and Human Potential category because it converts
practice into measurable improvement. Its impact is not only a generated answer
or a chatbot conversation: every attempt creates a structured record, identifies
observable competencies and recommends the next action. `[INSERT VERIFIED
OUTCOME OR USER FEEDBACK]` demonstrates the current impact. The long-term model
is `[FREE / SUBSCRIPTION / B2B / OTHER — VERIFY]`, with costs including
`[HOSTING, AI, STORAGE, SUPPORT AND MARKETING COSTS]`.

The business evidence is recorded separately in
`docs/SUBMISSION_EVIDENCE_TEMPLATE_EN.md` and the income statement template.
All user data shared with judges must be consented, minimized and redacted.
The team will provide the Cloud Logging and Vertex AI evidence for a real
production evaluation rather than presenting configuration as proof of use.
