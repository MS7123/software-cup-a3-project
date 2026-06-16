# 2026-06-16 Review: SQLite Vector Retrieval Phase 2

## Review Conclusion

Result: Pass

Allowed to commit: Yes

## Scope Reviewed

- Documents read: `docs/11-sqlite-vector-retrieval-plan.md`, `docs/12-rag-phase-roadmap.md`, `docs/05-agile-development-log.md`, `README.md`, `deployment/README.md`, `deployment/local.env.example`
- Diff / files reviewed: `src/backend/app/adapters/protocols.py`, `src/backend/app/adapters/embedding_provider.py`, `src/backend/app/models.py`, `src/backend/app/services/document_ingestion_service.py`, `src/backend/app/services/embedding_index_service.py`, `src/backend/app/services/vector_search_service.py`, `src/backend/app/services/knowledge_base_service.py`, `tests/test_embedding_provider.py`, `tests/test_vector_retrieval.py`, `tests/test_backend_contracts.py`, `scripts/run-local-deepseek.ps1`, `scripts/run-local-aliyun-hybrid.ps1`, `scripts/run-local-deepseek-hybrid.ps1`
- Builder claimed: SQLite `chunk_embeddings`, OpenAI-compatible embedding adapter, SQLite Python cosine vector search, keyword/vector/hybrid retrieval modes, embedding failure fallback to keyword, optional hybrid launch scripts
- Tests reported: targeted backend tests and full `scripts/verify.ps1`

## Findings

### Blocking

- None.

### Fix Before Merge

- None.

### Optional

- File: `src/backend/app/services/document_ingestion_service.py`
- Issue: When `RAG_EMBEDDING_ENABLED=true`, document ingestion calls `EmbeddingIndexService.index_course(course_id)` for the whole course after each import.
- Impact: This is acceptable for the current small demo dataset, but it can become slow after many documents because each import scans the course chunks and skips already-indexed embeddings one by one.
- Minimal fix: Later add a document-scoped indexing path or async indexing queue. Do not block this merge because default `RAG_EMBEDDING_ENABLED=false` avoids this cost.

## Implementation Boundary Check

| Check | Result | Evidence |
|---|---|---|
| Controller/frontend business logic | Pass | No frontend or API handler embedding/vector logic was added; retrieval remains behind service calls |
| Service/orchestrator boundary | Pass | Embedding indexing is in `EmbeddingIndexService`; vector retrieval is in `SQLiteVectorSearchService`; hybrid ranking is in `KnowledgeBaseService` |
| Adapter/provider boundary | Pass | External embedding HTTP calls are isolated in `app/adapters/embedding_provider.py` behind `EmbeddingProvider` |
| Hardcoded demo/mock risk | Pass | Tests use fake embeddings, but production code reads provider/model/settings from env and does not hardcode source refs or answers |
| API contract stability | Pass | Search result shape is preserved; hybrid/vector scores are added through `metadata` only |

## Competition Fit Check

- Current phase: RAG Phase 2, hybrid retrieval
- Does this change advance the phase goal? Yes
- Does this change improve A3 requirements fit? Yes
- The change adds opt-in semantic retrieval while preserving the default SQLite keyword demo path, improving RAG credibility without making local deployment heavier.

## Test Assessment

- Tests run by Builder: targeted backend tests and `scripts/verify.ps1`
- Tests run by Reviewer:
  - `python -m unittest tests.test_embedding_provider tests.test_vector_retrieval tests.test_rag_retrieval tests.test_backend_contracts -v`: 24 tests passed
  - `python -m compileall -q src\backend tests`: passed
  - PowerShell syntax check for `run-local-deepseek.ps1`, `run-local-aliyun-hybrid.ps1`, `run-local-deepseek-hybrid.ps1`: passed
  - `git diff --check`: passed with Windows CRLF notices only
  - `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify.ps1`: passed, including 64 backend tests, frontend production build, and Playwright smoke
- Missing but necessary tests: None before merge.
- Is verification sufficient for this change? Yes

## Final Recommendation

建议提交本轮增量。该实现符合 `docs/11-sqlite-vector-retrieval-plan.md` 的默认边界：SQLite 和 keyword retrieval 仍是默认路径，embedding / hybrid retrieval 需要显式 opt-in，且 provider 失败会回退到 keyword。后续如果资料量增加，应把当前 course-wide indexing 改为 document-scoped 或异步索引，但这不是当前比赛演示的合并阻塞项。
