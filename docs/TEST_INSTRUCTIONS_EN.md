# IARH test instructions

## Local test URL

- Web application: `http://localhost`
- API documentation: `http://localhost:8000/docs`
- Readiness: `http://localhost:8000/api/v1/health/ready`

## Judge account

Create a temporary account through **Create an account**. Do not publish a
real administrator password. For a private deployed demo, put a temporary
judge account and its expiry date in the Devpost private test instructions.

## Main journey

1. Register with a test email and a password of at least 12 characters.
2. Sign in.
3. Select **New simulation**, enter a target role and domain, and choose 3
   questions.
4. Create and start the interview.
5. Read the data-use notice, accept recording/evidence consent if you agree,
   and join the LiveKit room.
6. Submit a text answer for every question and finish the interview.
7. Open the interview report and verify the score, strengths, weaknesses and
   recommendations.
8. Open the progress view and repeat an interview to demonstrate the learning
   loop.

## AI proof

The deployed judge environment must have `VERTEX_AI_ENABLED=true` and a Google
Cloud service account with Vertex AI User permission. Capture a redacted Cloud
Logging entry for a successful evaluation and the corresponding Vertex AI usage
evidence. Never publish API keys or personal recordings.

## Account cleanup

Use the account deletion action or the documented `DELETE /api/v1/auth/me/data`
endpoint after testing. Test data must not be reused as evidence without the
user's explicit permission.
