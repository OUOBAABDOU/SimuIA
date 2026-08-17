# Build with Gemini XPRIZE submission package

## Recommended category

Education and Human Potential.

## One-line pitch

IARH is an AI Career Growth Coach that turns every interview attempt into a measurable learning loop with realistic practice, explainable Gemini feedback, and a personalized improvement plan.

## Required proof before submission

- Public demo URL running on Google Cloud.
- Gemini call executed in the deployed application, preferably through Vertex AI.
- Multiple authorized Gemini/Vertex AI configurations can be managed by an admin with encrypted credentials and automatic cooldown after transient quota errors.
- Public or judge-shared source repository with a license.
- Test account and step-by-step test instructions.
- Public demo video shorter than three minutes, in English.
- Real user count, user profiles, consented testimonials and usage evidence.
- Revenue, related revenue, expenses and marketing expenses for May, June, July and August 2026.
- English AI-native business story between 500 and 1,000 words, including daily
  AI operations, human/AI responsibilities, economic opportunities and category
  impact. Draft: `docs/AI_NATIVE_BUSINESS_STORY_EN.md`.
- Simplified income statement with zero values explicitly recorded where
  applicable. Template: `docs/INCOME_STATEMENT_TEMPLATE_EN.md`.
- Company identifier, if the participant is an organization.
- Cloud Logging/Gemini usage evidence and screenshots showing continuous operation.
- Written explanation of any pre-existing framework, SDK or source code.

## Demo flow

1. Select a target role and interview language.
2. Start an interview and give a spoken answer.
3. Show the transcript and observable evidence.
4. Show the Gemini-generated competency feedback.
5. Show the personalized practice plan.
6. Run a second attempt and show progress through `GET /api/v1/interviews/progress`.

## Compliance notes

Do not fabricate users, revenue, testimonials or operational logs. Inform users that anonymized evidence may be shared with the judges. Document licenses for LiveKit, Flutter, Whisper, MinIO, Google Cloud and all other third-party components. Verify that the project was created after 19 May 2026 or request clarification from Devpost if prior work may affect eligibility.
