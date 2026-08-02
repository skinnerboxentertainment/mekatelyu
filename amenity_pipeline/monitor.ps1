# Whappin amenity/attribute run monitor
# Shows overall progress + per-category yield. Ctrl+C to stop.
$base = "C:\Users\oscar\AI WORKBENCH\_Active\WhatHappeningPV\mekatelyu\amenity_pipeline"
$statusPath = Join-Path $base "output-about\status.json"
$resultsPath = Join-Path $base "output-about\amenities.jsonl"

while ($true) {
    Clear-Host
    Write-Host "=== Whappin About-attribute run ===" -ForegroundColor Cyan
    if (Test-Path $statusPath) {
        $s = Get-Content $statusPath | ConvertFrom-Json
        $eta = if ($s.etaSeconds) { "$([math]::Round($s.etaSeconds/60,0)) min" } else { "--" }
        Write-Host ("{0}/{1}  |  OK {2}  |  no-attr {3}  |  fail {4}  |  elapsed {5} min  |  ETA {6}" -f `
            $s.processed, $s.total, $s.succeeded, $s.noAmenities, $s.failed, [math]::Round($s.elapsedSeconds/60,1), $eta)
        Write-Host "now: $($s.current)" -ForegroundColor Yellow
    } else {
        Write-Host "status.json not found yet" -ForegroundColor Yellow
    }

    if (Test-Path $resultsPath) {
        $recs = Get-Content $resultsPath | ConvertFrom-Json
        Write-Host ""
        Write-Host "=== Per-category (this run) ===" -ForegroundColor Cyan
        $recs | Group-Object category | Sort-Object { $_.Name } | ForEach-Object {
            $ok = @($_.Group | Where-Object { $_.status -like "success*" }).Count
            $none = @($_.Group | Where-Object { $_.status -eq "attributes_not_exposed" }).Count
            $mismatch = @($_.Group | Where-Object { $_.status -eq "place_identity_mismatch" }).Count
            Write-Host ("{0,-16} done {1,3}  |  attributes {2,3}  |  none {3,3}  |  mismatch {4,2}" -f $_.Name, $_.Count, $ok, $none, $mismatch)
        }
    }
    Start-Sleep 15
}
