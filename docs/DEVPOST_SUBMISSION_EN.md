# Devpost submission draft

## Title

IARH — AI Career Growth Coach

## Category

Education and Human Potential

## Short description

IARH turns interview practice into a measurable learning loop. A candidate
chooses a target role, practices in a LiveKit session, receives transcription
and explainable Gemini competency feedback, then follows a personalized plan
and tracks progress across attempts.

## How Gemini transforms the business process

Gemini/Vertex AI evaluates each answer against the interview question and
produces structured feedback, observable evidence, strengths, weaknesses and
recommendations. The backend calculates scores and only asks Gemini to explain
the evidence and generate coaching guidance. This replaces a manual recruiter
review with a repeatable, auditable coaching workflow.

## Google Cloud implementation

The production backend is deployed on Cloud Run. Vertex AI Gemini is called by
the backend using the Cloud Run service identity. PostgreSQL, Redis, object
storage, LiveKit and the worker are configured as managed or reachable
production services. The exact project, revision, model, region and logs are
provided in the evidence register.

## Demo

See the under-three-minute video and follow the English test instructions:
`docs/TEST_INSTRUCTIONS_EN.md`.

## Originality and open source

IARH was created by the submitting participant after the hackathon start date,
subject to the participant's supporting evidence. Generic frameworks and SDKs
are disclosed in `docs/THIRD_PARTY_LICENSES.md`; the application code and
product workflow are the participant's original work.
