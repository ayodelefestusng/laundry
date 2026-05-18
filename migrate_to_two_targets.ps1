# migrate_to_two_targets.ps1
# ------------------------------------------------------------
# This script copies all tables and data from a source PostgreSQL
# database to two target databases:
#   1. A local PostgreSQL instance (localhost:5432)
#   2. A second remote PostgreSQL instance.
#
# Prerequisites:
#   * PostgreSQL client tools (pg_dump, pg_restore) must be in PATH.
#   * Network connectivity to all three databases.
#   * The target databases (local and second remote) already exist.
# ------------------------------------------------------------

# -----------------------------------------------------------------
# Configuration – adjust only if needed
# -----------------------------------------------------------------
# Source database (the one we are dumping from)
$sourceConn = "postgres://postgres:decs6192e4wd1d1e6s5cdwws111see1ee7659a82@147.182.194.8:5439/laundry_db?sslmode=disable"

# First target – local database
$localConn = "postgres://postgres:postgres@localhost:5432/laundry_db"

# Second target – remote database
$remoteConn2 = "postgres://postgres:postgres@24.144.119.35:5439/laundry_db?sslmode=disable"

# Set a connection timeout (seconds) for libpq connections used by pg_restore.
$env:PGCONNECT_TIMEOUT = "30"

# Temporary dump file (will be removed after the restores)
$dumpFile = "$env:TEMP\laundry_dump.backup"

# -----------------------------------------------------------------
# Step 1: Dump the source database
# -----------------------------------------------------------------
Write-Host "Dumping source database..."
# Use custom format for fast restore; omit ownership/ACL to avoid permission issues
pg_dump $sourceConn --format=custom --no-owner --no-acl --file=$dumpFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "pg_dump failed. Exiting."
    exit 1
}

# -----------------------------------------------------------------
# Step 2: Restore into the local database
# -----------------------------------------------------------------
Write-Host "Restoring dump into local database..."
# Use --clean and --if-exists to drop existing objects before restore, avoiding duplicate constraint errors.
pg_restore --dbname=$localConn --no-owner --no-acl --clean --if-exists $dumpFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "pg_restore to local DB failed."
    exit 1
}

# -----------------------------------------------------------------
# Step 3: Restore into the second remote database
# -----------------------------------------------------------------
Write-Host "Restoring dump into second remote database..."
$maxAttempts = 1  # Only try once; avoid repeated timeouts
$attempt = 0
while ($attempt -lt $maxAttempts) {
    $attempt++
    pg_restore --dbname=$remoteConn2 --no-owner --no-acl --clean --if-exists $dumpFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Second remote restore succeeded on attempt $attempt."
        break
    }
    else {
        Write-Warning "Attempt ${attempt}: pg_restore to second remote DB failed (exit code $LASTEXITCODE)."
        if ($attempt -lt $maxAttempts) {
            Write-Host "Retrying in 5 seconds..."
            Start-Sleep -Seconds 5
        }
    }
}

if ($attempt -eq $maxAttempts -and $LASTEXITCODE -ne 0) {
    Write-Warning "All $maxAttempts attempts to restore second remote DB failed. Continuing without second target."
}

# -----------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------
Remove-Item $dumpFile -Force
Write-Host "Migration to both targets completed successfully."

# ---------------------------------------------------------------
# Verification (optional)
# ---------------------------------------------------------------
Write-Host "Verifying local database tables..."
try {
    psql $localConn -c "\dt"
} catch {
    Write-Warning "Unable to list tables in local DB: $_"
}

if ($attempt -lt $maxAttempts) {
    Write-Host "Verifying second remote database tables..."
    try {
        psql $remoteConn2 -c "\dt"
    } catch {
        Write-Warning "Unable to list tables in second remote DB: $_"
    }
}