# RAG Reranking and Citation Quality Review

## Review Conclusion

Result: Pass

Allowed to commit: Yes

## Scope Reviewed

- Documents read:
  - `docs/04-development-roadmap.md`
  - `docs/00-project-brief.md`
  - `docs/02-acceptance-criteria.md`
  - `docs/06-project-state.md`
  - `docs/05-agile-development-log.md`
  - `docs/13-rag-reranking-plan.md`
  - `docs/14-rag-citation-quality-plan.md`
- Diff / files reviewed:
  - `src/backend/app/services/reranking_service.py`
  - `src/backend/app/services/citation_service.py`
  - `src/backend/app/services/knowledge_base_service.py`
  - `src/backend/app/services/vector_search_service.py`
  - `src/backend/app/services/tutor_service.py`
  - `src/backend/app/services/resource_service.py`
  - `src/backend/app/agents/tutor_agents.py`
  - `src/backend/app/agents/resource_agents.py`
  - `src/backend/app/agents/rule_based_agents.py`
  - `src/backend/app/agents/tutor_prompts.py`
  - `src/frontend/src/App.tsx`
  - `src/frontend/src/styles.css`
  - `src/frontend/tests/student-loop.spec.ts`
  - `tests/test_rag_reranking.py`
  - `tests/test_rag_citations.py`
  - `deployment/local.env.example`
  - `scripts/run-local-deepseek-rerank.ps1`
- Builder claimed:
  - Added Phase 3 RAG reranking as an opt-in service behind environment flags.
  - Added Phase 4 citation metadata, citation validation, and frontend source evidence display.
  - Preserved SQLite + Python retrieval defaults and demo stability when reranking is disabled.
- Tests reported:
  - Targeted backend tests.
  - Backend compile check.
  - Frontend production build.
  - Full local verification script.

## Findings

### Blocking

None.

### Fix Before Merge

None.

### Optional

- File: `src/backend/app/services/reranking_service.py`
  - Issue: The current source diversity bonus is based on `document_id`, so multiple useful chunks from one document do not get diversity credit.
  - Impact: This does not break the demo or current BFS/DFS comparison path, but later multi-section documents may need more precise diversity behavior.
  - Minimal fix: In a later increment, use a document plus section key, chunk group, or content fingerprint before applying duplicate-source penalties.

- File: `src/backend/app/services/citation_service.py`
  - Issue: Citation validation checks source reference format and availability, but does not verify claim-to-source semantic alignment.
  - Impact: This is acceptable for Phase 4.1 citation quality, but LLM answers can still cite a valid chunk for a weakly supported sentence.
  - Minimal fix: In Phase 4.2, add sentence-level source mapping or stricter prompt/output validation for evidence-backed claims.

## Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | Frontend only renders `source_refs`, scores, excerpts, and metadata. It does not compute retrieval, rerank, or citation validation logic. |
| Service/orchestrator boundary | Pass | Reranking lives in `RAG_RerankingService`; citation metadata and validation live in `citation_service`; orchestration remains in existing service layer. |
| Adapter/provider boundary | Pass | No new required remote provider. LLM prompt constraints were updated, while retrieval/rerank/citation behavior remains locally testable. |
| Hardcoded demo/mock risk | Pass | No hardcoded answer path was introduced. Source references are built from retrieved document/chunk metadata. |
| API contract stability | Pass | Existing response shape is preserved; `source_refs` and metadata are enriched rather than replacing request/response schemas. |

## Competition Fit Check

- Current phase: Phase 3 / Phase 4 RAG demo hardening.
- Does this change advance the phase goal? Yes.
- Does this change improve A3 requirements fit? Yes.

This increment improves the A3 path from simple grounded Q&A toward traceable retrieval, reranked context, and judge-visible evidence. It supports the current MVP mainline without restoring the old multi-agent heavy process.

## Test Assessment

- Tests run by Builder:
  - Not independently trusted without reviewer rerun.
- Tests run by Reviewer:
  - `python -m unittest tests.test_rag_reranking tests.test_rag_citations tests.test_rag_retrieval tests.test_vector_retrieval tests.test_llm_provider_tutor tests.test_backend_contracts -v`
  - `python -m compileall -q src\backend tests`
  - `npm run build`
  - `git diff --check`
  - PowerShell syntax check for `scripts/run-local-deepseek-rerank.ps1`
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`
- Missing but necessary tests:
  - None for this merge. Later increments should add claim-level citation quality checks when sentence-level grounding is implemented.
- Is verification sufficient for this change? Yes.

## Verification Notes

- Targeted backend suite passed: 38 tests OK.
- Full `verify.ps1` passed after stopping a locked project-local `esbuild.exe` process that blocked `npm ci` on Windows.
- Final full verification passed backend compile, 71 backend tests, `pip check`, backend wheel build, frontend dependency install, frontend production build, and Playwright smoke.
- Remaining warnings:
  - Vite chunk size warning remains non-blocking.
  - `npm audit` reports two high severity findings from the existing dependency tree; this was not introduced as a blocking regression in this increment.

## Final Recommendation

Recommend merge and commit. The increment is aligned with the current RAG roadmap and improves demo evidence quality without breaking fallback behavior. No blocking or fix-before-merge issues were found. The next focused work should be citation precision and manual judge-facing validation, not broad architecture restructuring.
