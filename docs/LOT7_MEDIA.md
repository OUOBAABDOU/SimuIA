# Lot 7 — Audio/Video infrastructure

IARH uses LiveKit for realtime WebRTC and LiveKit Egress for server-side recording.

## Runtime components

- `livekit`: realtime SFU
- `livekit_egress`: room/track recording
- `minio`: private S3-compatible object storage
- `media_recordings`: PostgreSQL metadata and lifecycle

LiveKit Egress uploads MP4 recordings to the `iarh-media` bucket. The application stores only the object key and metadata in PostgreSQL.

## Security rules

- LiveKit API credentials are server-side only.
- Client join tokens are short-lived.
- Recording files are private.
- The frontend must receive a public LiveKit URL separately from the server-side LiveKit URL.
- Do not expose MinIO credentials to the frontend.
- Recording access must use authenticated backend endpoints or short-lived signed URLs.

## Production

Replace development secrets, put LiveKit behind TLS, configure TURN, and use a managed/object-storage deployment or hardened MinIO. LiveKit Egress requires additional CPU/memory for composite transcoding.
