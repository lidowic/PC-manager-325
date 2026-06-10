param(
    [string]$VncServerExe = "C:\Program Files\TightVNC\tvnserver.exe",
    [int]$VncPort = 5900,
    [int]$NoVncPort = 6080,
    [string]$WebsockifyExe = "websockify",
    [string]$NoVncWebDir = "C:\novnc"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $VncServerExe)) {
    throw "VNC server executable not found: $VncServerExe"
}

Start-Process -FilePath $VncServerExe
Start-Process -FilePath $WebsockifyExe -ArgumentList "--web `"$NoVncWebDir`" $NoVncPort 127.0.0.1:$VncPort"

Write-Host "VNC server started."
Write-Host "Remote desktop URL: http://localhost:$NoVncPort/vnc.html"
