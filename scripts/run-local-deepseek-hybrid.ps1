param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "127.0.0.1",
    [int]$FrontendPort = 5173,
    [string]$DatabaseUrl = "sqlite:///./data/demo.sqlite3",
    [string]$ChatModel = "deepseek-v4-flash",
    [string]$EmbeddingModel = "text-embedding-v3",
    [int]$TimeoutSeconds = 10,
    [int]$MaxRetries = 0,
    [switch]$BypassProxy,
    [switch]$SmokeOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$embeddingApiKey = [Environment]::GetEnvironmentVariable("ALIYUN_BAILIAN_API_KEY", "User")
if ([string]::IsNullOrWhiteSpace($embeddingApiKey)) {
    $embeddingApiKey = $env:ALIYUN_BAILIAN_API_KEY
}
if ([string]::IsNullOrWhiteSpace($embeddingApiKey)) {
    throw "Missing ALIYUN_BAILIAN_API_KEY for embeddings. Set it once with: [Environment]::SetEnvironmentVariable('ALIYUN_BAILIAN_API_KEY', '<your-key>', 'User')"
}

$oldRagMode = $env:RAG_RETRIEVAL_MODE
$oldRagEmbeddingEnabled = $env:RAG_EMBEDDING_ENABLED
$oldRagVectorStore = $env:RAG_VECTOR_STORE
$oldRagVectorMaxCandidates = $env:RAG_VECTOR_MAX_CANDIDATES
$oldRagKeywordWeight = $env:RAG_KEYWORD_WEIGHT
$oldRagVectorWeight = $env:RAG_VECTOR_WEIGHT
$oldEmbeddingProvider = $env:EMBEDDING_PROVIDER
$oldEmbeddingBaseUrl = $env:EMBEDDING_BASE_URL
$oldEmbeddingModel = $env:EMBEDDING_MODEL
$oldEmbeddingApiKey = $env:EMBEDDING_API_KEY
$oldEmbeddingTimeout = $env:EMBEDDING_TIMEOUT_SECONDS
$oldEmbeddingRetries = $env:EMBEDDING_MAX_RETRIES
$oldEmbeddingBypassProxy = $env:EMBEDDING_BYPASS_PROXY

try {
    $env:RAG_RETRIEVAL_MODE = "hybrid"
    $env:RAG_EMBEDDING_ENABLED = "true"
    $env:RAG_VECTOR_STORE = "sqlite_cosine"
    $env:RAG_VECTOR_MAX_CANDIDATES = "1000"
    $env:RAG_KEYWORD_WEIGHT = "0.45"
    $env:RAG_VECTOR_WEIGHT = "0.55"

    $env:EMBEDDING_PROVIDER = "openai_compatible"
    $env:EMBEDDING_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    $env:EMBEDDING_MODEL = $EmbeddingModel
    $env:EMBEDDING_API_KEY = $embeddingApiKey
    $env:EMBEDDING_TIMEOUT_SECONDS = "10"
    $env:EMBEDDING_MAX_RETRIES = "0"
    $env:EMBEDDING_BYPASS_PROXY = "false"

    $scriptArgs = @{
        BackendHost = $BackendHost
        BackendPort = $BackendPort
        FrontendHost = $FrontendHost
        FrontendPort = $FrontendPort
        DatabaseUrl = $DatabaseUrl
        Model = $ChatModel
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
    if ($null -eq $oldRagMode) { Remove-Item Env:\RAG_RETRIEVAL_MODE -ErrorAction SilentlyContinue } else { $env:RAG_RETRIEVAL_MODE = $oldRagMode }
    if ($null -eq $oldRagEmbeddingEnabled) { Remove-Item Env:\RAG_EMBEDDING_ENABLED -ErrorAction SilentlyContinue } else { $env:RAG_EMBEDDING_ENABLED = $oldRagEmbeddingEnabled }
    if ($null -eq $oldRagVectorStore) { Remove-Item Env:\RAG_VECTOR_STORE -ErrorAction SilentlyContinue } else { $env:RAG_VECTOR_STORE = $oldRagVectorStore }
    if ($null -eq $oldRagVectorMaxCandidates) { Remove-Item Env:\RAG_VECTOR_MAX_CANDIDATES -ErrorAction SilentlyContinue } else { $env:RAG_VECTOR_MAX_CANDIDATES = $oldRagVectorMaxCandidates }
    if ($null -eq $oldRagKeywordWeight) { Remove-Item Env:\RAG_KEYWORD_WEIGHT -ErrorAction SilentlyContinue } else { $env:RAG_KEYWORD_WEIGHT = $oldRagKeywordWeight }
    if ($null -eq $oldRagVectorWeight) { Remove-Item Env:\RAG_VECTOR_WEIGHT -ErrorAction SilentlyContinue } else { $env:RAG_VECTOR_WEIGHT = $oldRagVectorWeight }
    if ($null -eq $oldEmbeddingProvider) { Remove-Item Env:\EMBEDDING_PROVIDER -ErrorAction SilentlyContinue } else { $env:EMBEDDING_PROVIDER = $oldEmbeddingProvider }
    if ($null -eq $oldEmbeddingBaseUrl) { Remove-Item Env:\EMBEDDING_BASE_URL -ErrorAction SilentlyContinue } else { $env:EMBEDDING_BASE_URL = $oldEmbeddingBaseUrl }
    if ($null -eq $oldEmbeddingModel) { Remove-Item Env:\EMBEDDING_MODEL -ErrorAction SilentlyContinue } else { $env:EMBEDDING_MODEL = $oldEmbeddingModel }
    if ($null -eq $oldEmbeddingApiKey) { Remove-Item Env:\EMBEDDING_API_KEY -ErrorAction SilentlyContinue } else { $env:EMBEDDING_API_KEY = $oldEmbeddingApiKey }
    if ($null -eq $oldEmbeddingTimeout) { Remove-Item Env:\EMBEDDING_TIMEOUT_SECONDS -ErrorAction SilentlyContinue } else { $env:EMBEDDING_TIMEOUT_SECONDS = $oldEmbeddingTimeout }
    if ($null -eq $oldEmbeddingRetries) { Remove-Item Env:\EMBEDDING_MAX_RETRIES -ErrorAction SilentlyContinue } else { $env:EMBEDDING_MAX_RETRIES = $oldEmbeddingRetries }
    if ($null -eq $oldEmbeddingBypassProxy) { Remove-Item Env:\EMBEDDING_BYPASS_PROXY -ErrorAction SilentlyContinue } else { $env:EMBEDDING_BYPASS_PROXY = $oldEmbeddingBypassProxy }
}
