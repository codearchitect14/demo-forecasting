# PowerShell script to run the application with Supabase credentials
# Replace these values with your actual Supabase credentials

# Supabase Configuration
$env:SUPABASE_URL = "YOUR_SUPABASE_URL_HERE"
$env:SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY_HERE"
$env:SUPABASE_SERVICE_KEY = "YOUR_SUPABASE_SERVICE_ROLE_KEY_HERE"

# Database Configuration (for backward compatibility)
$env:DB_HOST = "db.YOUR_SUPABASE_PROJECT_REF.supabase.co"
$env:DB_PORT = "5432"
$env:DB_NAME = "postgres"
$env:DB_USER = "postgres"
$env:DB_PASSWORD = "YOUR_SUPABASE_DB_PASSWORD_HERE"

# Connection Pool Settings
$env:DB_POOL_MIN_SIZE = "5"
$env:DB_POOL_MAX_SIZE = "20"
$env:DB_POOL_MAX_QUERIES = "50000"
$env:DB_POOL_MAX_INACTIVE_CONNECTION_LIFETIME = "300"

# Cache Settings
$env:CACHE_TTL = "300"
$env:CACHE_MAX_SIZE = "1000"

# Pagination Settings
$env:DEFAULT_PAGE_SIZE = "50"
$env:MAX_PAGE_SIZE = "100"

# Model Configuration
$env:MODEL_CACHE_DIR = "./model_cache"

# Logging Configuration
$env:LOG_LEVEL = "INFO"

Write-Host "Starting application with Supabase configuration..." -ForegroundColor Green
Write-Host "Make sure to update the credentials above with your actual Supabase values!" -ForegroundColor Yellow

# Run the application
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 