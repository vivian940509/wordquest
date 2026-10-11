# Pronunciation Latency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make WordQuest pronunciation playback start or fall back within 2 seconds while preserving dictionary audio and Google TTS fallback.

**Architecture:** Keep the current same-origin audio proxy, but add a short server-side pronunciation budget, process-local success cache, and a faster client fallback timer. The server remains synchronous Flask code, with bounded external calls instead of long serial waits.

**Tech Stack:** Flask, requests, pytest, browser Audio API, Web Speech API.

**Spec:** `docs/superpowers/specs/2026-10-11-wordquest-project-design.md`

## Global Constraints

- Pressing a pronunciation button must start audio or switch to browser TTS within 2 seconds under normal browser support.
- The pronunciation proxy must use a short request budget and must not serially wait for multiple long third-party timeouts.
- Successful pronunciation audio should be cached server-side for repeated words during the process lifetime.
- Successful pronunciation responses should remain browser/CDN-cacheable with public cache headers.
- Existing route tests must keep passing.

## Review Focus

- Slow dictionary metadata lookup should not exceed the pronunciation budget.
- Slow dictionary audio host should not prevent Google TTS fallback from being attempted within budget.
- Repeated word playback should hit cache without external calls.
- Empty or invalid word should still return `400`.
- Frontend audio failure should fall back before 2 seconds.

---

### Task 1: Server Pronunciation Budget And Cache

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_routes.py`

**Interfaces:**
- Consumes: `lookup_word(word, timeout=...)` where supported.
- Produces: `/api/pronounce/audio?word=...` with bounded external call timeouts and process-local success cache.

- [ ] **Step 1: Write failing tests**

Add tests that verify:

```python
def test_pronounce_audio_uses_fast_timeouts(monkeypatch):
    ...
    assert max(observed_timeouts) <= 1.2

def test_pronounce_audio_serves_cached_success_without_external_calls(monkeypatch):
    ...
    assert second_response.data == first_response.data
    assert external_call_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `py -m pytest tests/test_app_routes.py::test_pronounce_audio_uses_fast_timeouts tests/test_app_routes.py::test_pronounce_audio_serves_cached_success_without_external_calls -q`

Expected: FAIL because current code uses 5/7 second timeouts and has no cache.

- [ ] **Step 3: Implement bounded pronunciation helpers in `app.py`**

Add constants for a sub-2-second proxy budget, short per-request caps, and a process-local success cache. Use the cache before external lookup. Pass a short timeout to `lookup_word` when possible. Bound dictionary audio and Google TTS calls by the remaining budget.

- [ ] **Step 4: Run focused tests**

Run: `py -m pytest tests/test_app_routes.py::test_pronounce_audio_uses_fast_timeouts tests/test_app_routes.py::test_pronounce_audio_serves_cached_success_without_external_calls -q`

Expected: PASS.

### Task 2: Client Fallback Timer

**Files:**
- Modify: `static/js/app.js`
- Modify: `tests/test_app_routes.py`

**Interfaces:**
- Consumes: existing `playSameOriginAudio(word)` and `playPronunciation(btn)` frontend functions.
- Produces: frontend same-origin audio fallback timer below 2 seconds.

- [ ] **Step 1: Write failing test**

Add a route/static test that reads `static/js/app.js` and asserts:

```python
assert "PRONUNCIATION_AUDIO_START_TIMEOUT_MS=1500" in js
assert "7000" not in pronunciation timeout block
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest tests/test_app_routes.py::test_frontend_pronunciation_falls_back_within_two_seconds -q`

Expected: FAIL because current frontend timeout is 7000ms.

- [ ] **Step 3: Implement frontend timeout constant**

Replace the hard-coded 7000ms audio timeout with a named `PRONUNCIATION_AUDIO_START_TIMEOUT_MS=1500` constant and reject playback when audio has not reached `readyState >= 2`.

- [ ] **Step 4: Run focused test**

Run: `py -m pytest tests/test_app_routes.py::test_frontend_pronunciation_falls_back_within_two_seconds -q`

Expected: PASS.

### Task 3: Full Verification

**Files:**
- Verify all touched files.

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: verified pronunciation latency change.

- [ ] **Step 1: Run full suite**

Run: `py -m pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Review diff**

Run: `git diff -- app.py static/js/app.js tests/test_app_routes.py docs/superpowers/specs/2026-10-11-wordquest-project-design.md docs/superpowers/plans/2026-10-11-pronunciation-latency-plan.md`

Expected: only project spec, pronunciation plan, pronunciation timeout/cache code, and regression tests changed.
