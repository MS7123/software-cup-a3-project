param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$FrontendHost = "127.0.0.1",
    [int]$FrontendPort = 5173,
    [string]$DatabaseUrl = "sqlite:///./data/demo.sqlite3",
    [string]$Model = "xop3qwen1b7",
    [int]$TimeoutSeconds = 45,
    [int]$MaxRetries = 1,
    [switch]$BypassProxy,
    [switch]$SmokeOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$apiKey = $env:XFYUN_SPARK_API_KEY
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = [Environment]::GetEnvironmentVariable("XFYUN_SPARK_API_KEY", "User")
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "Missing XFYUN_SPARK_API_KEY. Set it once with: [Environment]::SetEnvironmentVariable('XFYUN_SPARK_API_KEY', '<your-spark-api-key>', 'User')"
}

$managedVariables = @(
    "LLM_PROVIDER",
    "LLM_BASE_URL",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_TIMEOUT_SECONDS",
    "LLM_MAX_RETRIES",
    "LLM_FALLBACK_MODE",
    "LLM_BYPASS_PROXY",
    "LLM_ENABLE_FOR_TUTOR",
    "LLM_ENABLE_FOR_RESOURCE",
    "LLM_ENABLE_FOR_EVALUATOR",
    "LLM_ENABLE_FOR_PROFILE_UPDATER",
    "LLM_ENABLE_FOR_PROFILE_BUILDER",
    "LLM_ENABLE_FOR_PLANNER",
    "LLM_ENABLE_FOR_QUIZ"
)
$previousValues = @{}
foreach ($name in $managedVariables) {
    $previousValues[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    $env:LLM_PROVIDER = "openai_compatible"
    $env:LLM_BASE_URL = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
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
    $env:LLM_ENABLE_FOR_PROFILE_BUILDER = "true"
    $env:LLM_ENABLE_FOR_PLANNER = "true"
    $env:LLM_ENABLE_FOR_QUIZ = "true"

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
    foreach ($name in $managedVariables) {
        $previousValue = $previousValues[$name]
        if ($null -eq $previousValue) {
            Remove-Item "Env:\$name" -ErrorAction SilentlyContinue
        } else {
            [Environment]::SetEnvironmentVariable($name, $previousValue, "Process")
        }
    }
}
