# migrate_remote_to_local.ps1
# ------------------------------------------------------------
# This script copies all tables and data from a remote PostgreSQL
# database to a local PostgreSQL database, making the local DB a
# mirror of the remote one.
#
# Prerequisites:
#   * PostgreSQL client tools (pg_dump, pg_restore) must be in PATH.
#   * Both remote and local databases are reachable from this machine.
#   * The local database (vectra_db) already exists. If it does not,
#     you can create it with `createdb` or via psql.
# ------------------------------------------------------------

# Remote connection details (adjust if needed)
$remoteConn = "postgres://postgres:decs6192e4wd1d1e6s5cdwws111see1ee7659a82@147.182.194.8:5439/laundry_db?sslmode=disable"

# Local connection details (as provided by the user)
$localConn = "postgres://postgres:postgres@24.144.119.35:5439/laundry_db?sslmode=disable"

# Temporary dump file (will be removed after restore)
$dumpFile = "$env:TEMP\vectra_dump.backup"

Write-Host "Dumping remote database..."
# --no-owner and --no-acl avoid permission issues when restoring
pg_dump $remoteConn --format=custom --no-owner --no-acl --file=$dumpFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "pg_dump failed. Exiting."
    exit 1
}

Write-Host "Restoring dump into local database..."
pg_restore --dbname=$localConn --no-owner --no-acl $dumpFile

if ($LASTEXITCODE -ne 0) {
    Write-Error "pg_restore failed."
    exit 1
}

# Clean up temporary dump file
Remove-Item $dumpFile -Force

Write-Host "Migration completed successfully."
