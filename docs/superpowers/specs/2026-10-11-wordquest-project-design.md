# WordQuest Project Design Spec

**Date:** 2026-10-11

## Purpose

WordQuest is a browser-based English vocabulary learning game for Chinese-speaking learners. It turns vocabulary review into short quest rounds, lets learners preview meaning and pronunciation before practice, and records progress through stages, mistakes, vocabulary mastery, daily missions, achievements, shop items, and friend challenges.

## Users

- Learners who want short, repeatable English vocabulary practice.
- Mobile users who may use Android browsers, embedded WebViews, or slow networks.
- Returning users who expect progress, wrong words, equipment, achievements, and account state to persist.

## Product Scope

### Core Learning Flow

1. The learner enters the map or study page.
2. A stage preview shows Chinese meaning, English word, context, memory hint, example sentence, and pronunciation.
3. The learner starts a five-question battle or custom practice run.
4. The app records answer correctness, elapsed time, vocabulary progress, mistakes, rewards, and stage completion.
5. The result page gives answer analysis, dictionary/local explanation, pronunciation playback, and optional AI teacher explanation.

### Game Modes

- **Campaign stage:** five questions, stage progress, stars, score, and unlock flow.
- **Practice:** wrong words, weak words, unmastered words, chapter-specific words, quick 10, challenge 30, and infinite mode.
- **Review:** due vocabulary from spaced practice.
- **Friend challenge:** challenge code, leaderboard, combo tracking.
- **Speech challenge:** browser speech recognition estimates similarity to target text.

### Pronunciation Playback

Pronunciation playback must be reliable on desktop and mobile.

- The visible button is `data-speak-word`.
- The browser first tries same-origin audio from `/api/pronounce/audio?word=...`.
- The server proxies dictionary audio when available.
- The server falls back to Google Translate TTS audio when dictionary audio is missing or invalid.
- The browser falls back to Web Speech API when same-origin audio cannot start quickly.
- The user must not wait on slow third-party services before hearing a fallback.

## Performance Requirements

- Pressing a pronunciation button must start audio or switch to browser TTS within 2 seconds under normal browser support.
- The pronunciation proxy must use a short request budget and must not serially wait for multiple long third-party timeouts.
- Successful pronunciation audio should be cached server-side for repeated words during the process lifetime.
- Successful pronunciation responses should remain browser/CDN-cacheable with public cache headers.
- Slow or unavailable dictionary services must not block battle answer submission, result pages, or pronunciation fallback.

## Data Responsibilities

- `word_data.py` owns built-in curriculum, hints, missions, shop items, and achievements.
- `battle_engine.py` owns question generation, answer grading, speech similarity, and wrong-answer analysis.
- `database.py` owns persistence for profile, vocabulary, history, missions, achievements, shop, challenges, and analytics.
- `dictionary_api.py` owns dictionary lookup against dictionaryapi.dev.
- `app.py` owns Flask routes, session flow, authentication integrations, pronunciation proxying, and rendering.
- `static/js/app.js` owns client interactions: countdown, speech recognition, pronunciation playback, lesson carousel, expandable copy, nav, and AI teacher requests.

## Error Handling

- Dictionary failures return local learning hints when possible.
- Pronunciation proxy failures return a clear non-200 JSON response, allowing the browser to switch to Web Speech API.
- Speech recognition failures leave the learner on the same page with retry feedback.
- Login and Supabase failures flash user-readable messages.

## Testing Requirements

- Flask route tests cover rendering, battle flow, pronunciation API behavior, and regression cases.
- Pronunciation tests must cover dictionary audio fallback, Google TTS fallback, cache hit behavior, and timeout budget values.
- Frontend timing constants for pronunciation fallback should be kept small and discoverable in `static/js/app.js`.

## Current Pronunciation Latency Problem

The current implementation waits in a serial chain:

- `lookup_word()` defaults to a 5 second dictionary API timeout.
- Dictionary audio fetch waits up to 5 seconds.
- Google TTS fetch waits up to 7 seconds.
- The browser waits up to 7 seconds before falling back to Web Speech API.

This can make a learner wait far longer than 2 seconds after pressing "聽發音".

## Acceptance Criteria

- Existing tests continue to pass.
- New pronunciation tests prove the audio proxy uses fast timeout values.
- New pronunciation tests prove a successful word is served from process cache on the next request.
- Frontend fallback timeout is reduced from 7 seconds to below 2 seconds.
- Documentation states the project behavior and the pronunciation latency SLA.
