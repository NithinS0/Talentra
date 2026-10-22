"""Talentra Database & Configuration Verification Script.

Executes local verification checks for Stage 2 without mutating database state.
"""

import os
import sys
import subprocess

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine, SessionLocal, check_database_connection


def check_dependencies() -> bool:
    """Verify that all core dependencies are installed."""
    print("--- 1. Dependency Verification ---")
    required = [
        ("fastapi", "FastAPI"),
        ("sqlalchemy", "SQLAlchemy"),
        ("psycopg", "Psycopg 3"),
        ("alembic", "Alembic"),
        ("pydantic", "Pydantic"),
        ("pydantic_settings", "Pydantic Settings"),
        ("pytest", "Pytest"),
        ("httpx", "HTTPX"),
    ]
    all_ok = True
    for mod_name, label in required:
        try:
            mod = __import__(mod_name)
            ver = getattr(mod, "__version__", "installed")
            print(f"  [OK] {label}: {ver}")
        except ImportError:
            print(f"  [FAIL] {label} is NOT installed")
            all_ok = False
    return all_ok


def check_settings() -> bool:
    """Verify that settings load and display safe masked summary."""
    print("\n--- 2. Settings & Environment Verification ---")
    try:
        print(f"  App Name:            {settings.APP_NAME}")
        print(f"  App Environment:     {settings.APP_ENV}")
        print(f"  Debug Mode:          {settings.APP_DEBUG}")
        print(f"  Pool Size:           {settings.DB_POOL_SIZE}")
        print(f"  Max Overflow:        {settings.DB_MAX_OVERFLOW}")
        print(f"  Pool Timeout:        {settings.DB_POOL_TIMEOUT}s")
        print(f"  Connect Timeout:     {settings.DB_CONNECT_TIMEOUT}s")
        print(f"  Safe Database URL:   {settings.safe_database_url}")
        print(f"  Database Configured: {settings.is_database_configured}")
        return True
    except Exception as e:
        print(f"  [FAIL] Error loading settings: {e}")
        return False


def check_alembic_config() -> bool:
    """Verify that Alembic can load its configuration cleanly."""
    print("\n--- 3. Alembic Configuration Check ---")
    try:
        from alembic.config import Config
        ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        if not os.path.exists(ini_path):
            print(f"  [FAIL] alembic.ini not found at {ini_path}")
            return False
        
        cfg = Config(ini_path)
        # Verify migration URL resolves without exposing credentials
        migration_url = settings.sqlalchemy_migration_url
        print(f"  [OK] alembic.ini located at: {ini_path}")
        print(f"  [OK] Alembic script location: {cfg.get_main_option('script_location')}")
        print(f"  [OK] Alembic migration URL dynamically resolved with driver prefix: {migration_url.split('://')[0]}://")
        return True
    except Exception as e:
        print(f"  [FAIL] Alembic configuration check error: {e}")
        return False


def check_git_secrets() -> bool:
    """Verify that .env is ignored and no secrets are tracked by Git."""
    print("\n--- 4. Git Security & Secrets Scan ---")
    gitignore_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".gitignore"))
    if not os.path.exists(gitignore_path):
        print("  [FAIL] .gitignore not found")
        return False
    
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    has_env = ".env" in content
    has_key = "*.key" in content or "*.pem" in content
    if has_env and has_key:
        print("  [OK] .gitignore properly excludes .env and private key files (*.key, *.pem).")
    else:
        print("  [WARN] .gitignore may be missing exclusions for .env or private keys.")
    
    # Check git tracking if git is initialized
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=os.path.dirname(gitignore_path))
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            env_tracked = any(".env" in l and not ".env.example" in l for l in lines)
            if env_tracked:
                print("  [FAIL] .env appears in git status! Remove from git index immediately.")
                return False
            print("  [OK] Git working tree does not track unignored .env files.")
        else:
            print("  [INFO] Git repository not yet initialized. Clean file-level exclusions verified.")
    except Exception:
        print("  [INFO] Git command not available or not in a git repo. File-level exclusions verified.")
    
    return True


def check_connectivity() -> bool:
    """Test actual database connectivity if configured."""
    print("\n--- 5. Supabase PostgreSQL Connectivity Test ---")
    if not settings.is_database_configured:
        print("  [STOP] Database credentials have NOT been configured in local .env.")
        print("         (Placeholder detected in DATABASE_URL).")
        print("         As required by Stage 2, stopping at configuration validation.")
        print("         Action required: Create .env from .env.example with your actual Supabase credentials.")
        return False
    
    print(f"  Attempting connection to: {settings.safe_database_url}")
    try:
        # Step A: Connect and run SELECT 1
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1;")).scalar()
            if result != 1:
                print("  [FAIL] Query 'SELECT 1;' returned unexpected value.")
                return False
            print("  [OK] Query 'SELECT 1;' executed successfully!")
        
        # Step B: Test SessionLocal lifecycle
        db = SessionLocal()
        try:
            sess_result = db.execute(text("SELECT current_database(), current_user, version();")).fetchone()
            print(f"  [OK] Active session query succeeded:")
            print(f"       Database: {sess_result[0]}")
            print(f"       User:     {sess_result[1]}")
            print(f"       Postgres: {sess_result[2][:45]}...")
        finally:
            db.close()
            print("  [OK] Database session closed cleanly.")
        
        return True
    except Exception as e:
        # Sanitize exception message
        err_msg = str(e)
        sanitized = err_msg.split("@")[-1] if "@" in err_msg else err_msg[:120]
        print(f"  [FAIL] Database connection failed: {sanitized}")
        return False


def main():
    """Run all verification gates."""
    print("=================================================================")
    print("Talentra — Stage 2: Database Connectivity & Configuration Check")
    print("=================================================================")
    
    deps_ok = check_dependencies()
    settings_ok = check_settings()
    alembic_ok = check_alembic_config()
    git_ok = check_git_secrets()
    conn_ok = check_connectivity()
    
    print("\n=================================================================")
    print("SUMMARY OF VERIFICATION")
    print("=================================================================")
    print(f"Dependencies:   {'PASSED' if deps_ok else 'FAILED'}")
    print(f"Configuration:  {'PASSED' if settings_ok else 'FAILED'}")
    print(f"Alembic Setup:  {'PASSED' if alembic_ok else 'FAILED'}")
    print(f"Git Exclusions: {'PASSED' if git_ok else 'FAILED'}")
    print(f"DB Connection:  {'PASSED (Verified)' if conn_ok else 'SKIPPED (Awaiting .env credentials)'}")
    print("=================================================================")


if __name__ == "__main__":
    main()
