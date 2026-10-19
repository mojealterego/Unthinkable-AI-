# VisionStory custom media, avatars, voices and image generation

Implemented as authenticated backend endpoints (not yet tested on a live VisionStory account):

- GET /api/cinema/visionstory/assets: kind, limit and cursor; provider asset IDs.
- POST /api/cinema/visionstory/assets/upload: approved third-party upload with consent, URL or bounded inline base64.
- POST /api/cinema/visionstory/avatars/create: subject consent plus owned image, returns avatar_id.
- POST /api/cinema/visionstory/avatars/framing: framing values for verified owned avatar, not public avatars.
- POST /api/cinema/visionstory/voices/clone: original voice with owner consent and explicit transfer permission.
- POST /api/cinema/visionstory/images/generate: live model options and exact credit cap; supports image references and editing by prompt. Provider returns image URL.

Server-only VISIONSTORY_API_KEY is required. No DELETE API or automatic paid retry is enabled. The current gateway allows 14 MB inline, a stricter limit than some vendor maximums. This is not proof of an activated account, actual media generation or multi-tenant security.

Source contracts: https://developers.visionstory.ai/reference/images/create-image ; https://developers.visionstory.ai/reference/assets/create-asset ; https://developers.visionstory.ai/reference/avatars/create-avatar ; https://developers.visionstory.ai/reference/avatars/update-avatar-framing ; https://developers.visionstory.ai/reference/voices/clone-voice

CI tests: tests/test_visionstory_media_tools.py, mock provider. Remaining work: Android file picker forms, result preview and durable project asset store, provider-account validation, full RBAC and bounded media retention.