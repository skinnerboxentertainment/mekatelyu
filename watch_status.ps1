<#
.SYNOPSIS
  Real-time dashboard for the authenticated stealth CID search.
  Run in a separate terminal while stealth_auth_search.py is running.
.USAGE
  .\watch_status.ps1            # one-shot snapshot
  .\watch_status.ps1 -Watch     # auto-refresh every 5 seconds
  .\watch_status.ps1 -Watch -Interval 3   # every 3 seconds
#>

param(
  [switch]$Watch,
  [int]$Interval = 5
)

$BASE    = Split-Path -Parent $PSCommandPath
$LOG     = Join-Path $BASE "stealth_session.log"
$CP      = Join-Path $BASE "stealth_checkpoint.json"
$RESULTS = Join-Path $BASE "stealth_results.jsonl"
$TARGETS = Join-Path $BASE "stealth_targets.csv"

function Get-Dashboard {
  $lines = @()
  $lines += ("=" * 58)
  $lines += "  PARADISIO -- AUTHENTICATED CID SEARCH DASHBOARD"
  $lines += ("=" * 58)
  $lines += ""

  # --- Checkpoint ---
  $doneCount = 0; $sessionCount = 0; $lastRun = "—"
  if (Test-Path $CP) {
    $cp = Get-Content $CP -Raw | ConvertFrom-Json
    $doneCount = $cp.done.Count
    $sessionCount = $cp.session_count
    $lastRun = $cp.last_run
  }

  # --- Targets ---
  $totalTargets = 0
  if (Test-Path $TARGETS) {
    $totalTargets = (Import-Csv $TARGETS).Count
  }

  $displayDone = [math]::Min($doneCount, $totalTargets)
  $remaining = [math]::Max(0, $totalTargets - $displayDone)
  $pct = if ($totalTargets -gt 0) { [math]::Round($displayDone / $totalTargets * 100, 1) } else { 0 }

  # --- Progress bar ---
  $barWidth = 30
  $filled = [math]::Floor($displayDone / $totalTargets * $barWidth)
  if ($totalTargets -eq 0) { $filled = 0 }
  $empty = $barWidth - $filled
  $bar = ("#" * $filled) + ("." * $empty)

  $lines += "  Progress:  [$bar]  $doneCount / $totalTargets ($pct%)"
  $lines += ""
  $lines += "  Sessions:   $sessionCount"
  $lines += "  Remaining:  $remaining"
  $lines += "  Last run:   $lastRun"
  $lines += ""

  # --- Results summary ---
  $totalResults = 0; $withCid = 0; $highConf = 0; $withPhone = 0; $withWeb = 0
  if (Test-Path $RESULTS) {
    $totalResults = 0
    Get-Content $RESULTS -Encoding UTF8 -ErrorAction SilentlyContinue | ForEach-Object {
      if ($_) {
        $totalResults++
        try { $r = $_ | ConvertFrom-Json } catch { return }
        if ($r.cid) { $withCid++ }
        if ($r.confidence -eq "high") { $highConf++ }
        if ($r.phone) { $withPhone++ }
        if ($r.website) { $withWeb++ }
      }
    }
  }

  $lines += "  Results collected:   $totalResults"
  $lines += "  With CID:            $withCid"
  $lines += "  High confidence:     $highConf"
  $lines += "  With phone:          $withPhone"
  $lines += "  With website:        $withWeb"
  $lines += ""

  # --- Recent log activity ---
  if (Test-Path $LOG) {
    $tail = Get-Content $LOG -Tail 4 -ErrorAction SilentlyContinue
    $lines += "  -- Last activity --"
    foreach ($t in $tail) {
      $lines += "  $t"
    }
    $lines += ""
  }

  # --- Process check ---
  $proc = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "stealth_auth_search" -or $_.CommandLine -match "stealth_search"
  }
  if ($proc) {
    $lines += "  [RUNNING]  PID $($proc.Id), started $($proc.StartTime.ToString('HH:mm:ss'))"
  } else {
    $lines += "  [IDLE]     No search process running"
  }

  $lines += "=" * 58
  return $lines -join "`n"
}

if ($Watch) {
  Write-Host "Watching — Ctrl+C to stop`n"
  while ($true) {
    Clear-Host
    Write-Host (Get-Dashboard)
    Start-Sleep -Seconds $Interval
  }
} else {
  Write-Host (Get-Dashboard)
}
