"""Accounts: users and sessions in the same SQLite file as matters.
Passwords are hashed with scrypt (standard library); sessions are random tokens in an HttpOnly cookie."""
from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

SESSION_DAYS = 14
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class AccountError(ValueError):
    """A sign-up or sign-in problem the person can fix; the message says how."""


@dataclass(frozen=True)
class User:
    id: str
    email: str
    name: str
    chambers: str
    kind: str          # advocate | lender | business


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)


class Accounts:
    def __init__(self, path: Path | str):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._db()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS users(
                    id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, chambers TEXT NOT NULL,
                    kind TEXT NOT NULL, salt BLOB NOT NULL, hash BLOB NOT NULL, created_at TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions(
                    token TEXT PRIMARY KEY, user_id TEXT NOT NULL, expires_at TEXT NOT NULL);
            """)

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def sign_up(self, email: str, name: str, password: str, chambers: str = "", kind: str = "advocate") -> User:
        email, name, chambers = email.strip().lower(), name.strip(), chambers.strip()
        if not name:
            raise AccountError("Enter your name.")
        if not EMAIL.match(email):
            raise AccountError("Enter an email address like name@chambers.in.")
        if len(password) < 8:
            raise AccountError("Use a password of at least 8 characters.")
        if kind not in ("advocate", "lender", "business"):
            kind = "advocate"
        salt = secrets.token_bytes(16)
        uid = "u_" + secrets.token_hex(6)
        try:
            with closing(self._db()) as db, db:
                db.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?)",
                           (uid, email, name, chambers or f"{name}'s chambers", kind, salt, _hash(password, salt),
                            datetime.now(timezone.utc).isoformat()))
        except sqlite3.IntegrityError:
            raise AccountError("An account with this email already exists. Sign in instead.") from None
        return self.get(uid)

    def sign_in(self, email: str, password: str) -> User:
        with closing(self._db()) as db:
            row = db.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
        if row is None or not hmac.compare_digest(_hash(password, row["salt"]), row["hash"]):
            raise AccountError("That email and password do not match an account.")
        return self.get(row["id"])

    def get(self, user_id: str) -> User:
        with closing(self._db()) as db:
            r = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if r is None:
            raise KeyError(user_id)
        return User(r["id"], r["email"], r["name"], r["chambers"], r["kind"])

    def new_session(self, user: User) -> str:
        token = secrets.token_urlsafe(32)
        exp = (datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)).isoformat()
        with closing(self._db()) as db, db:
            db.execute("INSERT INTO sessions VALUES (?,?,?)", (token, user.id, exp))
        return token

    def user_for(self, token: str | None) -> User | None:
        if not token:
            return None
        with closing(self._db()) as db:
            r = db.execute("SELECT * FROM sessions WHERE token=?", (token,)).fetchone()
        if r is None or r["expires_at"] < datetime.now(timezone.utc).isoformat():
            return None
        return self.get(r["user_id"])

    def end_session(self, token: str | None) -> None:
        if token:
            with closing(self._db()) as db, db:
                db.execute("DELETE FROM sessions WHERE token=?", (token,))
