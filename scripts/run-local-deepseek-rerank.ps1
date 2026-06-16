param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "127.0.0.1",
    [int]$FrontendPort = 5173,
    [string]$DatabaseUrl = "sqlite:///./data/demo.sqlite3",
    [string]$Model = "deepseek-v4-flash",
    [int]$TimeoutSeconds = 10,
    [int]$MaxRetries = 0,
    [int]$MaxCandidates = 12,
    [int]$TopContext = 5,
    [int]$ContextCharLimit = 3500,
    [switch]$BypassProxy,
    [switch]$SmokeOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$oldRerankEnabled = $env:RAG_RERANK_ENABLED
$oldRerankMaxCandidates = $env:RAG_RERANK_MAX_CANDIDATES
$oldRerankTopContext = $env:RAG_RERANK_TOP_CONTEXT
$oldRerankContextCharLimit = $env:RAG_RERANK_CONTEXT_CHAR_LIMIT

try {
    $env:RAG_RERANK_ENABLED = "true"
    $env:RAG_RERANK_MAX_CANDIDATES = [string]$MaxCandidates
    $env:RAG_RERANK_TOP_CONTEXT = [string]$TopContext
    $env:RAG_RERANK_CONTEXT_CHAR_LIMIT = [string]$ContextCharLimit

    $scriptArgs = @{
        BackendHost = $BackendHost
        BackendPort = $BackendPort
        FrontendHost = $FrontendHost
        FrontendPort = $FrontendPort
        DatabaseUrl = $DatabaseUrl
        Model = $Model
        TimeoutSeconds = $TimeoutSeconds
        MaxRetries = $MaxRetries
    }
    if ($BypassProxy) {
        $scriptArgs["BypassProxy"] = $true
    }
    if ($SmokeOnly) {
        $scriptArgs["SmokeOnly"] = $true
    }

    & (Join-Path $repoRoot "scripts/run-local-deepseek.ps1") @scriptArgs
} finally {
    if ($null -eq $oldRerankEnabled) { Remove-Item Env:\RAG_RERANK_ENABLED -ErrorAction SilentlyContinue } else { $env:RAG_RERANK_ENABLED = $oldRerankEnabled }
    if ($null -eq $oldRerankMaxCandidates) { Remove-Item Env:\RAG_RERANK_MAX_CANDIDATES -ErrorAction SilentlyContinue } else { $env:RAG_RERANK_MAX_CANDIDATES = $oldRerankMaxCandidates }
    if ($null -eq $oldRerankTopContext) { Remove-Item Env:\RAG_RERANK_TOP_CONTEXT -ErrorAction SilentlyContinue } else { $env:RAG_RERANK_TOP_CONTEXT = $oldRerankTopContext }
    if ($null -eq $oldRerankContextCharLimit) { Remove-Item Env:\RAG_RERANK_CONTEXT_CHAR_LIMIT -ErrorAction SilentlyContinue } else { $env:RAG_RERANK_CONTEXT_CHAR_LIMIT = $oldRerankContextCharLimit }
}
