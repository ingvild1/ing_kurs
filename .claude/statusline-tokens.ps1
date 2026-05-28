$input_json = $input | Out-String
$data = $input_json | ConvertFrom-Json

$transcript = $data.transcript_path
if (-not $transcript -or -not (Test-Path $transcript)) {
    exit 0
}

# Read JSONL lines, parse each, keep only assistant messages that have usage data
$last_usage = $null
Get-Content $transcript | ForEach-Object {
    try {
        $line = $_ | ConvertFrom-Json
        if ($line.type -eq "assistant" -and $line.message.usage) {
            $last_usage = $line.message.usage
        }
    } catch {}
}

if ($null -eq $last_usage) {
    exit 0
}

$input_tok   = if ($last_usage.input_tokens)                { [int]$last_usage.input_tokens }                else { 0 }
$cache_read  = if ($last_usage.cache_read_input_tokens)     { [int]$last_usage.cache_read_input_tokens }     else { 0 }
$cache_write = if ($last_usage.cache_creation_input_tokens) { [int]$last_usage.cache_creation_input_tokens } else { 0 }
$output_tok  = if ($last_usage.output_tokens)               { [int]$last_usage.output_tokens }               else { 0 }

$total = $input_tok + $cache_read + $cache_write + $output_tok

$context_size = $data.context_window.context_window_size
if ($context_size -and $context_size -gt 0) {
    $pct = [math]::Round(($total / $context_size) * 100, 1)
    Write-Host "Context: $("{0:N0}" -f $total) tokens ($pct% of $("{0:N0}" -f $context_size))"
} else {
    Write-Host "Context: $("{0:N0}" -f $total) tokens"
}
