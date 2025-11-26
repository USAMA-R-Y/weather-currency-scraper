import subprocess
import logging
from pathlib import Path
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


def commit_and_push() -> bool:
    """
    Commit and push database changes to repository.
    
    This is optional and can be used to track database changes over time.
    The database file will be committed and pushed to the remote repository.
    
    Returns:
        True if successful, False otherwise
    """
    if not settings.GIT_PUSH_ENABLED:
        logger.info("Git push disabled in settings")
        return False
    
    try:
        # Configure git user if provided
        if settings.GIT_USER_NAME:
            subprocess.run(
                ["git", "config", "user.name", settings.GIT_USER_NAME],
                check=True,
                capture_output=True
            )
        
        if settings.GIT_USER_EMAIL:
            subprocess.run(
                ["git", "config", "user.email", settings.GIT_USER_EMAIL],
                check=True,
                capture_output=True
            )
        
        # Add database file
        db_path = "data/weather_tracker.db"
        subprocess.run(["git", "add", db_path], check=True, capture_output=True)
        logger.info(f"Added {db_path} to git staging")
        
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True
        )
        
        if result.returncode == 0:
            logger.info("No changes to commit")
            return True
        
        # Commit changes
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        commit_message = f"chore(scrape): update data {timestamp}"
        
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            check=True,
            capture_output=True
        )
        logger.info(f"Committed changes: {commit_message}")
        
        # Push to remote
        subprocess.run(
            ["git", "push", "origin", "main"],
            check=True,
            capture_output=True
        )
        logger.info("Successfully pushed database updates to remote")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e}")
        logger.error(f"Command output: {e.output.decode() if e.output else 'N/A'}")
        logger.error(f"Command stderr: {e.stderr.decode() if e.stderr else 'N/A'}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during git sync: {e}", exc_info=True)
        return False


def check_git_status() -> dict:
    """
    Check the current git status.
    
    Returns:
        Dictionary with git status information
    """
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True
        )
        branch = branch_result.stdout.strip()
        
        # Get last commit
        commit_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%H %s"],
            check=True,
            capture_output=True,
            text=True
        )
        last_commit = commit_result.stdout.strip()
        
        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        )
        has_changes = bool(status_result.stdout.strip())
        
        return {
            "branch": branch,
            "last_commit": last_commit,
            "has_uncommitted_changes": has_changes,
            "status": "ok"
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check git status: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
