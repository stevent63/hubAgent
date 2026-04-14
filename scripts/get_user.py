#!/usr/bin/env python3
"""Load user profile path from USER_EMAIL in .env."""
from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
import os

REPO_ROOT = Path(__file__).resolve().parent.parent

def get_user_email() -> str | None:
    """Return USER_EMAIL from .env, or None if not set."""
    load_dotenv(REPO_ROOT / '.env')
    return os.getenv('USER_EMAIL')

def get_user_profile_path() -> Path | None:
    """Return path to user/{email}.md, or None if USER_EMAIL not set."""
    email = get_user_email()
    if not email:
        return None
    return REPO_ROOT / 'user' / f'{email}.md'

def log_user() -> None:
    """Print running-as banner."""
    email = get_user_email()
    if email:
        print(f'Running as user: {email}')
    else:
        print('Running as user: (USER_EMAIL not set in .env)')

if __name__ == '__main__':
    log_user()
    profile = get_user_profile_path()
    if profile and profile.exists():
        print(f'Profile: {profile}')
    elif profile:
        print(f'Profile path: {profile} (file not found)')
    else:
        print('No profile configured.')
