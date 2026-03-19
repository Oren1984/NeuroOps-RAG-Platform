# scripts/run.ps1
# Main script to run RAG agent

Write-Host "[INFO] Starting NeuroOps – RAG Platform..." -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[FAIL] .env file not found. Copy .env.example to .env" -ForegroundColor Red
    exit 1
}

# Run audit
Write-Host "[INFO] Running audit..." -ForegroundColor Cyan
python scripts/rag_audit.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Audit failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Run server
Write-Host "[INFO] Starting server..." -ForegroundColor Cyan
python -m src.cli serve
