# VisionStory AI in Unthinkable Cinema — provider adapter

Verified official guides:
- https://developers.visionstory.ai/guides/quick-start
- https://developers.visionstory.ai/guides/cli
- https://developers.visionstory.ai/reference/videos/create-video
- https://developers.visionstory.ai/reference/billing/get-credits

Implemented (code + mocked API tests): server-side provider REST client, discovery of models, avatars and voices, read-only credit check, explicitly approved talking-avatar generation from text OR recorded MP3/WAV audio using stable client_request_id, job polling by video_id. Audio accepts audio_url or inline_data base64 (8 MB max), denoise, optional voice conversion after audio-rights confirmation, plus emotion and chroma-key background. Base URL is https://openapi.visionstory.ai; authentication is X-API-Key. No deletion API exists in this integration. A real job is only submitted if a private server has a verified provider key, available credits, catalog matching IDs, and the authenticated caller explicitly approved the potentially paid generation.

Server uses VISIONSTORY_API_KEY from its private environment; do not put it in Flutter, GitHub or chat. Gateway has a separate API_KEY for access. A successful local or CI test does not mean an authenticated VisionStory account was used.

Gateway endpoints, all requiring Authorization Bearer gateway key:
- GET /api/cinema/visionstory/capabilities
- GET /api/cinema/visionstory/credits
- GET /api/cinema/visionstory/models
- GET /api/cinema/visionstory/models/ai-video (discovery only)
- GET /api/cinema/visionstory/models/image (discovery only)
- GET /api/cinema/visionstory/avatars
- GET /api/cinema/visionstory/avatars/public
- GET /api/cinema/visionstory/videos/recent
- GET /api/cinema/visionstory/voices
- POST /api/cinema/visionstory/talking-video
- GET /api/cinema/visionstory/talking-video/{video_id}

The paid render input requires avatar_id, model_id, client_request_id, aspect_ratio, resolution, approved_for_paid_generation=true, and exactly one of: (1) text with voice_id, (2) audio_script containing either an HTTPS audio_url or inline_data base64. Audio mode also requires confirmed_audio_rights=true. Optional fields include background_color, emotion, denoise and voice_change. Use only IDs from account-specific live discovery, and persist client_request_id and returned video_id before retries. Poll at 5-second intervals, stop on failed or after about 10 minutes; VisionStory keeps completed assets approximately 7 days. The output currently gives video_url but does NOT automatically download or save it in the mobile app.

## Setup on your own authorized machine

The official installer supports macOS, Linux and WSL; direct support for Android Termux is not documented. A Linux cloud dev environment is recommended. Inspect vendor script before running it:

    curl -fsSL https://developers.visionstory.ai/cli -o visionstory-install.sh
    bash visionstory-install.sh
    npx skills add visionstory-ai/skills --skill visionstory-api
    visionstory doctor

If doctor says the account key is missing, create it privately at https://developers.visionstory.ai/api-keys and run:

    visionstory login
    visionstory credits

Stop if credits fails. Then discover available resource IDs:

    visionstory models
    visionstory avatars --is-public
    visionstory voices

Only after account/credit verification and an explicit decision to use credits:

    visionstory create-video --avatar-id YOUR_REAL_AVATAR_ID --text "Witaj w Unthinkable AI." --voice-id YOUR_REAL_VOICE_ID --output result.mp4

For a saved job:
    visionstory status --video-id YOUR_VIDEO_ID

No media deletion is done by this adapter or setup process.

## Pending feature integration

- Provider asset uploads, custom portrait avatars, voice cloning with permission, TTS and STT, AI video with refs via Wan/Seedance/Kling, API cost estimates and media archive. The new video/image model endpoints discover catalogs; they do not yet submit generation jobs.
- Flutter UI connection to remote VisionStory catalogs, approval, job tracking and MP4 download.
- Durable provider job state and encrypted per-tenant secrets. The current single gateway API_KEY is NOT production tenant separation.

## Audit of the owner's three reference PDFs

A page-by-page requirements map is in docs/VISIONSTORY_PDF_AUDIT.md. Additional tests are in tests/test_visionstory_documents.py. This is backend work and its passing CI must not be represented as successful paid rendering, enabled provider account, or completed mobile UI.
