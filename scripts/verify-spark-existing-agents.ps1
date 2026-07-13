param(
    [string]$Model = "xop3qwen1b7",
    [int]$TimeoutSeconds = 60,
    [int]$MaxRetries = 1,
    [switch]$BypassProxy
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$apiKey = $env:XFYUN_SPARK_API_KEY
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    $apiKey = [Environment]::GetEnvironmentVariable("XFYUN_SPARK_API_KEY", "User")
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "Missing XFYUN_SPARK_API_KEY. Configure it before running the Spark online acceptance test."
}

$managedVariables = @(
    "PYTHONPATH",
    "RUN_SPARK_ONLINE_TESTS",
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
    "LLM_ENABLE_FOR_PROFILE_UPDATER"
)
$previousValues = @{}
foreach ($name in $managedVariables) {
    $previousValues[$name] = [Environment]::GetEnvironmentVariable($name, "Process")
}

try {
    $env:PYTHONPATH = Join-Path $repoRoot "src/backend"
    $env:RUN_SPARK_ONLINE_TESTS = "true"
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

    & python -m unittest tests.test_spark_existing_agents_online -v
    if ($LASTEXITCODE -ne 0) {
        throw "Spark existing-agent online acceptance failed with exit code $LASTEXITCODE."
    }
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
