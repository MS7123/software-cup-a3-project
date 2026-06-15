# 2026-06-15 Review: RAG Retrieval Coverage

## Review Conclusion

Result: Pass

Allowed to commit: Yes

## Scope Reviewed

- Documents read: `docs/09-rag-retrieval-coverage-plan.md`, `docs/05-agile-development-log.md`, `README.md`
- Diff / files reviewed: `src/backend/app/services/knowledge_base_service.py`, `src/backend/app/services/tutor_service.py`, `src/backend/app/services/resource_service.py`, `src/backend/app/agents/tutor_agents.py`, `src/backend/app/agents/tutor_prompts.py`, `src/frontend/src/App.tsx`, `src/frontend/src/styles.css`, `src/frontend/tests/student-loop.spec.ts`, `tests/test_rag_retrieval.py`, `tests/test_llm_provider_tutor.py`
- Builder claimed: anchor-aware retrieval coverage for BFS/DFS compare questions, Tutor/Resource retrieval `top_k=5`, search UI matched terms and excerpt display, LLM no-context fallback guard
- Tests reported: targeted backend tests, frontend build, `scripts/verify.ps1`

## Findings

### Blocking

- None.

### Fix Before Merge

- None.

### Optional

- File: `src/backend/app/services/knowledge_base_service.py`
- Issue: `content_fingerprint` currently uses the first 180 normalized characters for duplicate removal.
- Impact: This is acceptable for the current repeated-document demo risk, but two long chunks with the same prefix and different later details could be over-deduplicated.
- Minimal fix: Later replace it with a stable hash over the full normalized chunk content.

## Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | Frontend only renders backend `metadata`, `score`, `source_ref`, and excerpt; no scoring or retrieval ordering in UI |
| Service/orchestrator boundary | Pass | Anchor detection, query expansion, dedupe, and coverage ranking are contained in `KnowledgeBaseService` |
| Adapter/provider boundary | Pass | No new external provider, embedding SDK, vector database, or LLM SDK path was introduced |
| Hardcoded demo/mock risk | Pass | Code uses generic BFS/DFS anchor aliases and does not hardcode an answer or source_ref |
| API contract stability | Pass | Existing request/response schemas are unchanged; only `metadata` fields are extended |

## Competition Fit Check

- Current phase: Phase 2 / Phase 3 boundary
- Does this change advance the phase goal? Yes
- Does this change improve A3 requirements fit? Yes
- The increment directly fixes a visible demo issue where LLM+RAG had DFS content in the database but did not receive DFS chunks in context.

## Test Assessment

- Tests run by Builder: `python -m unittest tests.test_rag_retrieval -v`, `npm run build`, `./scripts/verify.ps1`
- Tests run by Reviewer:
  - `python -m unittest tests.test_rag_retrieval tests.test_llm_provider_tutor tests.test_backend_contracts -v`: 24 tests passed
  - `npm run build`: passed
  - `python -m compileall -q src\backend tests`: passed
  - `git diff --check`: passed with Windows CRLF notices only
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`: passed, including 54 backend tests, frontend build, and Playwright smoke
- Missing but necessary tests: None before merge.
- Is verification sufficient for this change? Yes

## Final Recommendation

建议提交本轮增量。它在不引入 embedding、VectorStore 或 PostgreSQL 依赖的情况下，提升了 BFS/DFS 复合问题的 RAG 召回稳定性，并让前端能看到 matched terms 与 chunk 摘要。后续可以把 anchor aliases 从硬编码常量升级为课程概念 alias 配置，但这不阻塞当前比赛演示。
