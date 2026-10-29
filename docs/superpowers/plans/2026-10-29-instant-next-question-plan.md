# Instant Next Question Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every campaign answer advance immediately and show all wrong-answer explanations together on the final level summary.

**Architecture:** Keep the existing Flask redirect-per-question flow, but ensure the campaign answer branch returns before any external dictionary enrichment. Store local explanation fields with each campaign result and render them from the existing `level_summary` session payload.

**Tech Stack:** Python, Flask, Jinja2, pytest

**Spec:** `docs/superpowers/specs/2026-10-29-instant-next-question-design.md`

## Global Constraints

- Do not add any fixed client-side delay before advancing.
- Correct and incorrect campaign answers both advance directly to the next question.
- Do not change scoring, question counts, or the database schema.
- External dictionary availability must not affect campaign question-to-question latency.

## Review Focus

- A wrong non-final campaign answer must redirect to the next battle page without calling the dictionary API.
- A correct non-final campaign answer must retain the same immediate redirect behavior.
- A final campaign answer must redirect to the level summary without calling the dictionary API.
- A run with no wrong answers must render the existing empty wrong-answer state cleanly.
- Wrong-answer summary data must preserve the selected answer, correct answer, prompt, and local explanation for each missed question.

---

### Task 1: Fast campaign answer path

**Files:**
- Modify: `tests/test_app_routes.py`
- Modify: `app.py:280-292`

**Interfaces:**
- Consumes: existing `grade_answer()`, `run_summary()`, and `session["campaign_run"]` behavior.
- Produces: campaign result items containing `correct`, `selected`, `answer`, `prompt`, `explanation`, and reward/timing fields without calling `lookup_word()`.

- [ ] **Step 1: Write the failing test**

Add `test_wrong_campaign_answer_advances_without_dictionary_lookup`. Prepare a campaign run with room remaining, monkeypatch `app.lookup_word` to raise, submit an incorrect option, and assert a `302` redirect to `/battle?...` plus one stored result whose `correct` is `False` and whose `explanation` matches the question's local explanation.

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `pytest tests/test_app_routes.py::test_wrong_campaign_answer_advances_without_dictionary_lookup -v`

Expected: FAIL because the stored campaign result does not yet include `explanation`.

- [ ] **Step 3: Store local explanation data in the campaign result**

In `app.answer()`, extend `item` with `explanation: q.get("explanation", "")`. Keep the campaign branch before `lookup_result_dictionary()` so both correct and incorrect campaign answers redirect immediately.

- [ ] **Step 4: Run campaign routing tests**

Run: `pytest tests/test_app_routes.py::test_wrong_campaign_answer_advances_without_dictionary_lookup tests/test_app_routes.py::test_final_campaign_answer_goes_to_summary_without_dictionary_lookup tests/test_app_routes.py::test_campaign_question_totals_match_preview_count_for_all_school_levels -v`

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app_routes.py
git commit -m "perf: keep campaign answers on fast path"
```

### Task 2: Detailed wrong-answer review on level summary

**Files:**
- Modify: `tests/test_app_routes.py`
- Modify: `templates/level_summary.html`
- Modify: `static/css/style.css`

**Interfaces:**
- Consumes: `summary.wrong`, where each item provides `prompt`, `selected`, `answer`, and `explanation`.
- Produces: a final summary section that renders each wrong answer with the user's choice, correct answer, and detailed local explanation.

- [ ] **Step 1: Write the failing summary rendering tests**

Add `test_level_summary_renders_detailed_wrong_answer_review` with one wrong result and assert the page contains the prompt, selected answer, correct answer, explanation, and the heading `錯題集中解析`. Add `test_level_summary_with_perfect_score_has_no_wrong_review_cards` and assert the heading remains present with a positive empty state while no review card is rendered.

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `pytest tests/test_app_routes.py::test_level_summary_renders_detailed_wrong_answer_review tests/test_app_routes.py::test_level_summary_with_perfect_score_has_no_wrong_review_cards -v`

Expected: FAIL because the current template only renders compact wrong-answer rows.

- [ ] **Step 3: Render detailed review cards**

In `templates/level_summary.html`, replace the compact wrong-answer list with a `錯題集中解析` section. For each wrong item, render `prompt`, `selected`, `answer`, and `explanation`; when empty, render `這一關全部答對，沒有需要複習的錯題。`.

- [ ] **Step 4: Style the review for desktop and mobile**

In `static/css/style.css`, add focused classes for the review list, selected/correct answer comparison, and explanation body. Reuse existing colors and breakpoint conventions; do not add animation delays.

- [ ] **Step 5: Run the focused summary tests**

Run: `pytest tests/test_app_routes.py::test_level_summary_renders_detailed_wrong_answer_review tests/test_app_routes.py::test_level_summary_with_perfect_score_has_no_wrong_review_cards -v`

Expected: both PASS.

- [ ] **Step 6: Run the complete suite**

Run: `pytest -q`

Expected: all tests PASS with no new warnings or errors.

- [ ] **Step 7: Commit**

```bash
git add templates/level_summary.html static/css/style.css tests/test_app_routes.py
git commit -m "feat: review wrong answers at level summary"
```
