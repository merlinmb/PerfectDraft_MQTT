# Deploys this project to the homebridge Pi and (re)builds the container.
$ErrorActionPreference = "Stop"

$HostName = "pi@homebridge.local"
$RemoteDir = "/home/pi/portainer_data/perfectdraft"

ssh $HostName "mkdir -p $RemoteDir"
if (-not $?) { throw "ssh mkdir failed" }

scp -r Dockerfile docker-compose.yml requirements.txt src "${HostName}:${RemoteDir}/"
if (-not $?) { throw "scp failed" }

# config.yaml/token_cache.json in $RemoteDir may be owned by root (the container
# runs as root and writes into the bind-mounted /data), so a plain scp overwrite
# as the pi user can fail with "Permission denied". Upload to /tmp first, then
# move into place with sudo.
function Copy-RemoteFile($LocalPath, $RemoteFileName) {
    $RemoteTmpPath = "/tmp/perfectdraft_deploy_$RemoteFileName"
    scp $LocalPath "${HostName}:${RemoteTmpPath}"
    if (-not $?) { throw "scp of $RemoteFileName failed" }
    ssh $HostName "sudo mv $RemoteTmpPath $RemoteDir/$RemoteFileName && sudo chown pi:pi $RemoteDir/$RemoteFileName"
    if (-not $?) { throw "failed to move $RemoteFileName into place on $HostName" }
}

Copy-RemoteFile "config.yaml" "config.yaml"

$TokenCachePath = Join-Path $PSScriptRoot "data\token_cache.json"
if (Test-Path $TokenCachePath) {
    Copy-RemoteFile $TokenCachePath "token_cache.json"
    Write-Host "Copied local token_cache.json to the Pi."
} else {
    Write-Host "No local data\token_cache.json found (run get_auth_token.py first if needed) - skipping."
}

ssh $HostName "cd $RemoteDir && docker compose up -d --build"
if (-not $?) { throw "remote docker compose up failed" }

Write-Host "Deployed config.yaml and restarted perfectdraft-mqtt on $HostName."
