# Whappin hours-run monitor
# Shows overall progress + per-status counts. Ctrl+C to stop.
$base = "C:\Users\oscar\AI WORKBENCH\_Active\WhatHappeningPV\mekatelyu\amenity_pipeline"
$statusPath = Join-Path $base "output-hours\status.json"
$resultsPath = Join-Path $base "output-hours\amenities.jsonl"

while ($true) {
    Clear-Host
    Write-Host "=== Whappin Hours run ===" -ForegroundColor Cyan
    if (Test-Path $statusPath) {
        $s = Get-Content $statusPath | ConvertFrom-Json
        $eta = if ($s.etaSeconds) { "$([math]::Round($s.etaSeconds/60,0)) min" } else { "--" }
        $pct = [math]::Round(($s.processed / $s.total) * 100, 1)
        Write-Host ("{0}/{1} ({2}%)  |  OK {3}  |  no-hours {4}  |  fail {5}  |  elapsed {6} min  |  ETA {7}" -f `
            $s.processed, $s.total, $pct, $s.succeeded, $s.noAmenities, $s.failed, [math]::Round($s.elapsedSeconds/60,1), $eta)
        Write-Host "now: $($s.current)" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Per-status:" -ForegroundColor Cyan
        $s.statuses.PSObject.Properties | Where-Object { $_.Value -gt 0 } | Sort-Object Value -Descending | ForEach-Object {
            Write-Host ("  {0,-30} {1}" -f $_.Name, $_.Value)
        }
    } else {
        Write-Host "status.json not found yet" -ForegroundColor Yellow
    }
    Start-Sleep 20
}
