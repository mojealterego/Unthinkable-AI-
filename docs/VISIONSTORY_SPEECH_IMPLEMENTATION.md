# VisionStory Speech Studio — implemented backend contracts

References: https://developers.visionstory.ai/guides/audio-understanding ,
https://developers.visionstory.ai/reference/audio/transcribe-audio ,
https://developers.visionstory.ai/reference/audio/align-audio ,
https://developers.visionstory.ai/reference/speech/create-speech .

All calls require gateway \`Authorization: Bearer API_KEY\`, private server-side \`VISIONSTORY_API_KEY\`, a valid positive credit balance, caller approval and rights to the media / voice. The provider is the billing system of record. A positive balance is NOT an exact cost quote.

- \`POST /api/cinema/visionstory/speech/transcribe\` — body \`audio\` with exactly one MediaRef source (\`asset_id\`, public HTTPS \`url\`, or \`inline_data\`), \`srt\` and \`diarize\` independent bools, \`confirmed_audio_rights=true\`, \`approved_for_paid_generation=true\`. JSON result includes text, language, words, optional SRT, cost and duration. Audio size is limited by the shared gateway MediaRef guard. The provider supports up to 30 minutes, though the gateway restricts file size.
- \`POST /api/cinema/visionstory/speech/align\` — same media and approvals, plus exact spoken \`text\`; returns word timing and billed credits.
- \`POST /api/cinema/visionstory/speech/tts\` — text, voice_id, optional BCP-47 locale and speech_rate with confirmed_voice_rights and paid approval; returns \`audio/mpeg\` MP3 bytes with \`X-Cost-Credit\`, \`X-Usage-Characters\`, \`X-Audio-Duration-Sec\` headers. Provider price in documentation: 2 credits per started 1000 characters (only on success). The response is binary, not JSON.
- These synchronous provider requests are NOT automatically retried after timeout; they may be charged even if client connection fails.

CLI/Termux and owner account live verification are not performed by the backend unit tests. The new Speech Studio Flutter view and TTS download are separate tasks.
