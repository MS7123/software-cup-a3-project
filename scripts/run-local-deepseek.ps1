param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "127.0.0.1",
    [int]$FrontendPort = 5173,
    [string]$DatabaseUrl = "sqlite:///./data/demo.sqlite3",
    [string]$Model = "deepseek-v4-flash",
    [int]$TimeoutSeconds = 10,
    [int]$MaxRetries = 0,
    [switch]$BypassProxy,
    [switch]$SmokeOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

$apiKey = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = $env:DEEPSEEK_API_KEY
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "Missing DEEPSEEK_API_KEY. Set it once with: [Environment]::SetEnvironmentVariable('DEEPSEEK_API_KEY', '<your-deepseek-api-key>', 'User')"
}

$oldLlmProvider = $env:LLM_PROVIDER
$oldLlmBaseUrl = $env:LLM_BASE_URL
$oldLlmApiKey = $env:LLM_API_KEY
$oldLlmModel = $env:LLM_MODEL
$oldLlmTimeout = $env:LLM_TIMEOUT_SECONDS
$oldLlmRetries = $env:LLM_MAX_RETRIES
$oldLlmFallback = $env:LLM_FALLBACK_MODE
$oldLlmBypassProxy = $env:LLM_BYPASS_PROXY
$oldLlmTutorEnabled = $env:LLM_ENABLE_FOR_TUTOR
$oldLlmResourceEnabled = $env:LLM_ENABLE_FOR_RESOURCE
$oldLlmEvaluatorEnabled = $env:LLM_ENABLE_FOR_EVALUATOR
$oldLlmProfileUpdaterEnabled = $env:LLM_ENABLE_FOR_PROFILE_UPDATER

try {
    $env:LLM_PROVIDER = "openai_compatible"
    $env:LLM_BASE_URL = "https://api.deepseek.com"
    $env:LLM_API_KEY = $apiKey
    $env:LLM_MODEL = $Model
    $env:LLM_TIMEOUT_SECONDS = [string]$TimeoutSeconds
    $env:LLM_MAX_RETRIES = [string]$MaxRetries
    $env:LLM_FALLBACK_MODE = "rule_based"
    $env:LLM_BYPASS_PROXY = if ($BypassProxy) { "true" } else { "false" }
    $env:LLM_ENABLE_FOR_TUTOR = "true"
    $env:LLM_ENABLE_FOR_RESOURCE = "true"
    $env:LLM_ENABLE_FOR_EVALUATOR = "true"
    $env:LLM_ENABLE_FOR_PROFILE_UPDATER = "true"

    $scriptArgs = @{
        BackendHost = $BackendHost
        BackendPort = $BackendPort
        FrontendHost = $FrontendHost
        FrontendPort = $FrontendPort
        DatabaseUrl = $DatabaseUrl
        UseRemoteTutorLLM = $true
    }
    if ($SmokeOnly) {
        $scriptArgs["SmokeOnly"] = $true
    }

    & (Join-Path $repoRoot "scripts/run-local.ps1") @scriptArgs
} finally {
    if ($null -eq $oldLlmProvider) { Remove-Item Env:\LLM_PROVIDER -ErrorAction SilentlyContinue } else { $env:LLM_PROVIDER = $oldLlmProvider }
    if ($null -eq $oldLlmBaseUrl) { Remove-Item Env:\LLM_BASE_URL -ErrorAction SilentlyContinue } else { $env:LLM_BASE_URL = $oldLlmBaseUrl }
    if ($null -eq $oldLlmApiKey) { Remove-Item Env:\LLM_API_KEY -ErrorAction SilentlyContinue } else { $env:LLM_API_KEY = $oldLlmApiKey }
    if ($null -eq $oldLlmModel) { Remove-Item Env:\LLM_MODEL -ErrorAction SilentlyContinue } else { $env:LLM_MODEL = $oldLlmModel }
    if ($null -eq $oldLlmTimeout) { Remove-Item Env:\LLM_TIMEOUT_SECONDS -ErrorAction SilentlyContinue } else { $env:LLM_TIMEOUT_SECONDS = $oldLlmTimeout }
    if ($null -eq $oldLlmRetries) { Remove-Item Env:\LLM_MAX_RETRIES -ErrorAction SilentlyContinue } else { $env:LLM_MAX_RETRIES = $oldLlmRetries }
    if ($null -eq $oldLlmFallback) { Remove-Item Env:\LLM_FALLBACK_MODE -ErrorAction SilentlyContinue } else { $env:LLM_FALLBACK_MODE = $oldLlmFallback }
    if ($null -eq $oldLlmBypassProxy) { Remove-Item Env:\LLM_BYPASS_PROXY -ErrorAction SilentlyContinue } else { $env:LLM_BYPASS_PROXY = $oldLlmBypassProxy }
    if ($null -eq $oldLlmTutorEnabled) { Remove-Item Env:\LLM_ENABLE_FOR_TUTOR -ErrorAction SilentlyContinue } else { $env:LLM_ENABLE_FOR_TUTOR = $oldLlmTutorEnabled }
    if ($null -eq $oldLlmResourceEnabled) { Remove-Item Env:\LLM_ENABLE_FOR_RESOURCE -ErrorAction SilentlyContinue } else { $env:LLM_ENABLE_FOR_RESOURCE = $oldLlmResourceEnabled }
    if ($null -eq $oldLlmEvaluatorEnabled) { Remove-Item Env:\LLM_ENABLE_FOR_EVALUATOR -ErrorAction SilentlyContinue } else { $env:LLM_ENABLE_FOR_EVALUATOR = $oldLlmEvaluatorEnabled }
    if ($null -eq $oldLlmProfileUpdaterEnabled) { Remove-Item Env:\LLM_ENABLE_FOR_PROFILE_UPDATER -ErrorAction SilentlyContinue } else { $env:LLM_ENABLE_FOR_PROFILE_UPDATER = $oldLlmProfileUpdaterEnabled }
}
