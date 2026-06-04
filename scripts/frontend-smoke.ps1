param(
    [int]$BackendPort = 8123,
    [int]$FrontendPort = 5174
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$frontendRoot = Join-Path $repoRoot "src/frontend"
$viteEntry = Join-Path $frontendRoot "node_modules/vite/bin/vite.js"
$tmpDb = Join-Path $env:TEMP ("software-cup-a3-smoke-{0}.sqlite3" -f ([guid]::NewGuid().ToString("N")))
$backendOut = Join-Path $env:TEMP "software-cup-a3-backend-smoke.out.log"
$backendErr = Join-Path $env:TEMP "software-cup-a3-backend-smoke.err.log"
$frontendOut = Join-Path $env:TEMP "software-cup-a3-frontend-smoke.out.log"
$frontendErr = Join-Path $env:TEMP "software-cup-a3-frontend-smoke.err.log"

function Assert-PortFree {
    param([int]$Port)

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listeners) {
        $owners = ($listeners | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
        throw "Port $Port is already in use by process id(s): $owners"
    }
}

function Wait-ForHttp {
    param(
        [string]$Uri,
        [int]$Attempts = 40
    )

    for ($i = 0; $i -lt $Attempts; $i++) {
        try {
            return Invoke-WebRequest -Uri $Uri -UseBasicParsing
        } catch {
            Start-Sleep -Milliseconds 500
        }
    }
    throw "Timed out waiting for $Uri"
}

function Stop-OwnedProcess {
    param([System.Diagnostics.Process]$Process)

    if ($Process -and -not $Process.HasExited) {
        Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
        $Process.WaitForExit(5000) | Out-Null
    }
}

Remove-Item -LiteralPath $tmpDb,$backendOut,$backendErr,$frontendOut,$frontendErr -Force -ErrorAction SilentlyContinue
Assert-PortFree -Port $BackendPort
Assert-PortFree -Port $FrontendPort

if (-not (Test-Path -LiteralPath $viteEntry)) {
    throw "Frontend dependencies are missing. Run npm ci in $frontendRoot before smoke verification."
}

$oldPythonPath = $env:PYTHONPATH
$oldDatabaseUrl = $env:APP_DATABASE_URL
$oldViteBase = $env:VITE_API_BASE_URL
$oldViteProxyTarget = $env:VITE_PROXY_TARGET
$oldPlaywrightBase = $env:PLAYWRIGHT_BASE_URL
$oldLlmProvider = $env:LLM_PROVIDER
$oldLlmTutorEnabled = $env:LLM_ENABLE_FOR_TUTOR

$backend = $null
$frontend = $null

try {
    $env:PYTHONPATH = "src/backend"
    $env:APP_DATABASE_URL = "sqlite:///$tmpDb"
    $env:LLM_PROVIDER = "rule_based"
    $env:LLM_ENABLE_FOR_TUTOR = "false"
    $backend = Start-Process -FilePath python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", [string]$BackendPort) `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $backendOut `
        -RedirectStandardError $backendErr `
        -PassThru

    Wait-ForHttp -Uri "http://127.0.0.1:$BackendPort/api/v1/demo-data/status" | Out-Null

    $env:VITE_API_BASE_URL = "/api/v1"
    $env:VITE_PROXY_TARGET = "http://127.0.0.1:$BackendPort"
    $env:PLAYWRIGHT_BASE_URL = "http://127.0.0.1:$FrontendPort"
    $frontend = Start-Process -FilePath "node" `
        -ArgumentList @($viteEntry, "--host", "127.0.0.1", "--port", [string]$FrontendPort, "--strictPort") `
        -WorkingDirectory $frontendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr `
        -PassThru

    $frontendPage = Wait-ForHttp -Uri "http://127.0.0.1:$FrontendPort/"
    if (-not $frontendPage.Content.Contains('id="root"')) {
        throw "Frontend page did not contain React root."
    }

    Push-Location $frontendRoot
    try {
        npm.cmd run test:smoke -- --workers=1
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend browser smoke failed with exit code $LASTEXITCODE."
        }
    } finally {
        Pop-Location
    }

    [pscustomobject]@{
        FrontendStatus = $frontendPage.StatusCode
        BrowserSmoke = "Passed"
        BackendPort = $BackendPort
        FrontendPort = $FrontendPort
    } | Format-List
} finally {
    Stop-OwnedProcess -Process $frontend
    Stop-OwnedProcess -Process $backend

    if ($null -eq $oldPythonPath) { Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue } else { $env:PYTHONPATH = $oldPythonPath }
    if ($null -eq $oldDatabaseUrl) { Remove-Item Env:\APP_DATABASE_URL -ErrorAction SilentlyContinue } else { $env:APP_DATABASE_URL = $oldDatabaseUrl }
    if ($null -eq $oldViteBase) { Remove-Item Env:\VITE_API_BASE_URL -ErrorAction SilentlyContinue } else { $env:VITE_API_BASE_URL = $oldViteBase }
    if ($null -eq $oldViteProxyTarget) { Remove-Item Env:\VITE_PROXY_TARGET -ErrorAction SilentlyContinue } else { $env:VITE_PROXY_TARGET = $oldViteProxyTarget }
    if ($null -eq $oldPlaywrightBase) { Remove-Item Env:\PLAYWRIGHT_BASE_URL -ErrorAction SilentlyContinue } else { $env:PLAYWRIGHT_BASE_URL = $oldPlaywrightBase }
    if ($null -eq $oldLlmProvider) { Remove-Item Env:\LLM_PROVIDER -ErrorAction SilentlyContinue } else { $env:LLM_PROVIDER = $oldLlmProvider }
    if ($null -eq $oldLlmTutorEnabled) { Remove-Item Env:\LLM_ENABLE_FOR_TUTOR -ErrorAction SilentlyContinue } else { $env:LLM_ENABLE_FOR_TUTOR = $oldLlmTutorEnabled }

    Start-Sleep -Milliseconds 300
    Remove-Item -LiteralPath $tmpDb -Force -ErrorAction SilentlyContinue
}
