param(
    [string]$ConfigPath = "infra/configs/agent.example.yaml",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "Starting Windows agent with config $ConfigPath"
& $PythonExe -m agent.main --config $ConfigPath
