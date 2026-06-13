# 2026-06-13 Review: Demo RAG UI, Trace Sources, and Retrieval Tuning

## Review Conclusion

Result: Pass

Allowed to commit: Yes

## Scope Reviewed

- Documents read: `docs/04-development-roadmap.md`, `docs/00-project-brief.md`, `docs/02-acceptance-criteria.md`, `docs/06-project-state.md`, `docs/05-agile-development-log.md`, `docs/08-next-demo-increments-plan.md`
- Diff / files reviewed: `src/frontend/src/App.tsx`, `src/frontend/src/api/client.ts`, `src/frontend/src/api/types.ts`, `src/frontend/src/styles.css`, `src/frontend/tests/student-loop.spec.ts`, `src/backend/app/services/knowledge_base_service.py`, `src/backend/app/services/tutor_service.py`, `src/backend/app/services/resource_service.py`, `tests/test_rag_retrieval.py`, `docs/llm-rag-tutor-manual-verification.md`, `README.md`
- Builder claimed: front-end Knowledge setup import UI, minimal knowledge search UI, Tutor/Resource trace source refs, keyword retrieval metadata and scoring tuning, LLM + RAG Tutor manual verification document
- Tests reported: targeted backend tests, frontend build, `scripts/verify.ps1`

## Findings

### Blocking

- None.

### Fix Before Merge

- None.

### Optional

- File: `src/frontend/src/App.tsx`
- Issue: Knowledge setup currently seeds an English BFS/DFS sample in the textarea.
- Impact: This is useful for demo speed and does not fabricate backend results, but it may make the UI look prefilled rather than user-driven.
- Minimal fix: In a later UX pass, add a small sample-load button and keep the default textarea empty if a cleaner judging flow is preferred.

## Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | Frontend only captures title/source_type/content/query and calls backend APIs; no chunking, scoring, LLM calls, or fabricated source refs in UI |
| Service/orchestrator boundary | Pass | Retrieval scoring remains in `KnowledgeBaseService`; Tutor/Resource services only append existing `source_refs` into Agent step summaries |
| Adapter/provider boundary | Pass | No new external provider or SDK was introduced; LLM + RAG remains documented as opt-in through existing `LLMProvider` |
| Hardcoded demo/mock risk | Pass | Smoke sample text is user-editable input; source refs displayed by frontend come from API responses |
| API contract stability | Pass | Existing Tutor, Resource, Agent run, and search response shapes remain compatible; only metadata fields were added |

## Competition Fit Check

- Current phase: Phase 2 / Phase 3 boundary
- Does this change advance the phase goal? Yes
- Does this change improve A3 requirements fit? Yes
- The increment makes real course material import visible in the demo, strengthens grounded Tutor/Resource evidence, and improves Agent trace explainability without forcing external services.

## Test Assessment

- Tests run by Builder: `python -m unittest tests.test_rag_retrieval tests.test_learning_loop_api tests.test_backend_contracts -v`, `npm run build`, `python -m unittest tests.test_rag_retrieval -v`
- Tests run by Reviewer, if any:
  - `python -m unittest tests.test_rag_retrieval tests.test_learning_loop_api tests.test_backend_contracts -v`: 13 tests passed
  - `npm run build`: passed
  - `git diff --check`: passed with Windows CRLF notices only
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`: passed, including 47 backend unit tests, wheel build, frontend build, and Playwright smoke
- Missing but necessary tests: None before merge. Real remote LLM provider behavior remains a manual opt-in verification because default CI/smoke must not require secrets or network.
- Is verification sufficient for this change? Yes

## Final Recommendation

建议提交本轮增量。它推进了真实 RAG 可演示入口、grounded source 展示和 Agent trace 可解释性，同时保持默认离线演示、API contract 和 service/provider 边界稳定。后续最小增量应优先做更清晰的导入空状态或真实 LLM + RAG Tutor 的人工验收记录，不需要为本轮合并阻塞。
