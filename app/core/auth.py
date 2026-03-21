"""
CounterFlow v1.0.0 — Authentication & Role-Based Access Control
================================================================
Handles:
  - Secure password hashing and verification (bcrypt)
  - User creation (Admin onboarding + Staff account management)
  - Login authentication for Admin and Staff roles
  - In-memory session state for the currently logged-in user
  - Permission checking by action name

Password policy:
  - Minimum 6 characters (configurable via COUNTERFLOW_MIN_PASSWORD_LEN)
  - Hashed with bcrypt (12 rounds) — never stored in plain text

Session:
  CounterFlowAuthSession is a module-level singleton that tracks
  the currently logged-in user throughout the application lifetime.
"""

import bcrypt
from sqlalchemy.orm import Session

from app.db.models import CounterFlowUser


# ── Constants ─────────────────────────────────────────────────
COUNTERFLOW_MIN_PASSWORD_LEN = 6
COUNTERFLOW_BCRYPT_ROUNDS    = 12

# ── Permission Map ────────────────────────────────────────────
# Maps action name → minimum role required ("STAFF" or "ADMIN")
COUNTERFLOW_PERMISSIONS: dict[str, str] = {
    # Billing
    "create_bill":          "STAFF",
    "view_bills":           "STAFF",
    # Customers
    "add_customer":         "STAFF",
    "view_customers":       "STAFF",
    "clear_debt":           "STAFF",
    "delete_customer":      "ADMIN",
    # Inventory
    "view_inventory":       "STAFF",
    "edit_inventory":       "ADMIN",
    # Staff management
    "manage_staff":         "ADMIN",
    # Logs
    "view_logs":            "ADMIN",
}

_ROLE_RANK = {"STAFF": 1, "ADMIN": 2}


# ──────────────────────────────────────────────────────────────
class CounterFlowPasswordError(Exception):
    """Raised when a password does not meet policy requirements."""


class CounterFlowAuthError(Exception):
    """Raised on authentication failure (wrong credentials or inactive user)."""


class CounterFlowDuplicateUserError(Exception):
    """Raised when creating a user with an already-taken username."""


# ──────────────────────────────────────────────────────────────
# ── Password Utilities ────────────────────────────────────────
# ──────────────────────────────────────────────────────────────

def counterflow_hash_password(plain_password: str) -> str:
    """
    CounterFlow — Hash a plain-text password with bcrypt.
    Returns the hashed string suitable for database storage.
    Never call this without first validating the password policy.
    """
    password_bytes = plain_password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=COUNTERFLOW_BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def counterflow_verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    CounterFlow — Verify a plain-text password against a bcrypt hash.
    Uses constant-time comparison internally (bcrypt.checkpw).
    Returns True if the password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except Exception:
        return False


def counterflow_validate_password_policy(password: str) -> None:
    """
    CounterFlow — Enforce password policy rules.
    Raises CounterFlowPasswordError with a human-readable message on failure.
    """
    if len(password) < COUNTERFLOW_MIN_PASSWORD_LEN:
        raise CounterFlowPasswordError(
            f"Password must be at least {COUNTERFLOW_MIN_PASSWORD_LEN} characters long."
        )


# ──────────────────────────────────────────────────────────────
# ── Auth Session (module-level singleton) ─────────────────────
# ──────────────────────────────────────────────────────────────

class CounterFlowAuthSession:
    """
    CounterFlow — Application-wide authentication session state.
    Tracks the currently logged-in user.
    This is a module-level singleton — do not instantiate per-screen.

    Access via the global:  counterflow_auth_session
    """

    def __init__(self):
        self._current_user: CounterFlowUser | None = None

    # ── Login / Logout ─────────────────────────────────────────

    def counterflow_login(self, user: CounterFlowUser) -> None:
        """CounterFlow — Set the active user after successful authentication."""
        self._current_user = user

    def counterflow_logout(self) -> None:
        """CounterFlow — Clear the active user session."""
        self._current_user = None

    # ── Accessors ─────────────────────────────────────────────

    @property
    def counterflow_current_user(self) -> CounterFlowUser | None:
        """CounterFlow — The currently logged-in user, or None."""
        return self._current_user

    @property
    def counterflow_is_authenticated(self) -> bool:
        return self._current_user is not None

    @property
    def counterflow_is_admin(self) -> bool:
        return (
            self._current_user is not None
            and self._current_user.counterflow_role == "ADMIN"
        )

    @property
    def counterflow_user_id(self) -> int | None:
        return (
            self._current_user.counterflow_user_id
            if self._current_user else None
        )

    @property
    def counterflow_display_name(self) -> str:
        return (
            self._current_user.counterflow_display_name
            if self._current_user else "Unknown"
        )

    @property
    def counterflow_role(self) -> str | None:
        return (
            self._current_user.counterflow_role
            if self._current_user else None
        )

    # ── Permission Check ───────────────────────────────────────

    def counterflow_can(self, action: str) -> bool:
        """
        CounterFlow — Check if the current user has permission for an action.
        Returns False if not logged in or insufficient role.
        """
        if not self._current_user:
            return False
        required_role = COUNTERFLOW_PERMISSIONS.get(action)
        if required_role is None:
            return False  # Unknown action = deny by default
        user_rank     = _ROLE_RANK.get(self._current_user.counterflow_role, 0)
        required_rank = _ROLE_RANK.get(required_role, 99)
        return user_rank >= required_rank


# ── Module-level singleton ────────────────────────────────────
counterflow_auth_session = CounterFlowAuthSession()


# ──────────────────────────────────────────────────────────────
# ── Auth Manager ─────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────

class CounterFlowAuthManager:
    """
    CounterFlow — Handles all user account operations:
      - First-run Admin creation
      - Login authentication
      - Staff account creation / deactivation
      - User listing and lookup
    """

    def __init__(self, counterflow_session: Session):
        self.counterflow_session = counterflow_session

    # ── First-Run Check ────────────────────────────────────────

    def counterflow_has_any_user(self) -> bool:
        """
        CounterFlow — Returns True if at least one user exists in the DB.
        Used at startup to decide whether to show onboarding or login.
        """
        return (
            self.counterflow_session
            .query(CounterFlowUser)
            .first()
        ) is not None

    # ── User Creation ──────────────────────────────────────────

    def counterflow_create_admin(
        self,
        username:     str,
        display_name: str,
        password:     str,
    ) -> CounterFlowUser:
        """
        CounterFlow — Create the first Admin account (onboarding).
        Should only be called once on first run.
        Raises:
            CounterFlowPasswordError       — password too short
            CounterFlowDuplicateUserError  — username already taken
        """
        counterflow_validate_password_policy(password)
        self._counterflow_assert_username_free(username)

        user = CounterFlowUser(
            counterflow_username=username.strip().lower(),
            counterflow_display_name=display_name.strip(),
            counterflow_role="ADMIN",
            counterflow_password_hash=counterflow_hash_password(password),
            counterflow_admin_id=None,
        )
        self.counterflow_session.add(user)
        self.counterflow_session.commit()
        self.counterflow_session.refresh(user)
        return user

    def counterflow_create_staff(
        self,
        username:     str,
        display_name: str,
        password:     str,
        admin_id:     int,
    ) -> CounterFlowUser:
        """
        CounterFlow — Create a Staff account under a given Admin.
        Raises:
            CounterFlowPasswordError       — password too short
            CounterFlowDuplicateUserError  — username already taken
        """
        counterflow_validate_password_policy(password)
        self._counterflow_assert_username_free(username)

        user = CounterFlowUser(
            counterflow_username=username.strip().lower(),
            counterflow_display_name=display_name.strip(),
            counterflow_role="STAFF",
            counterflow_password_hash=counterflow_hash_password(password),
            counterflow_admin_id=admin_id,
        )
        self.counterflow_session.add(user)
        self.counterflow_session.commit()
        self.counterflow_session.refresh(user)
        return user

    # ── Authentication ─────────────────────────────────────────

    def counterflow_authenticate(
        self,
        username:      str,
        password:      str,
        expected_role: str,         # "ADMIN" or "STAFF"
    ) -> CounterFlowUser:
        """
        CounterFlow — Authenticate a user.
        Verifies username, password hash, role, and active status.
        On success: populates counterflow_auth_session and returns the user.
        On failure: raises CounterFlowAuthError.
        """
        user = (
            self.counterflow_session
            .query(CounterFlowUser)
            .filter_by(counterflow_username=username.strip().lower())
            .first()
        )

        if user is None or not counterflow_verify_password(password, user.counterflow_password_hash):
            raise CounterFlowAuthError("Invalid username or password.")

        if not user.counterflow_is_active:
            raise CounterFlowAuthError("This account has been deactivated. Contact your Admin.")

        if user.counterflow_role != expected_role:
            raise CounterFlowAuthError(
                f"This account is not a {expected_role.title()} account. "
                f"Please use the correct login option."
            )

        counterflow_auth_session.counterflow_login(user)
        return user

    # ── Staff Management ───────────────────────────────────────

    def counterflow_get_all_staff(self) -> list[CounterFlowUser]:
        """CounterFlow — Return all Staff accounts."""
        return (
            self.counterflow_session
            .query(CounterFlowUser)
            .filter_by(counterflow_role="STAFF")
            .order_by(CounterFlowUser.counterflow_created_at.desc())
            .all()
        )

    def counterflow_deactivate_staff(self, user_id: int) -> None:
        """CounterFlow — Deactivate a staff account (soft delete)."""
        user = self.counterflow_session.get(CounterFlowUser, user_id)
        if user and user.counterflow_role == "STAFF":
            user.counterflow_is_active = False
            self.counterflow_session.commit()

    def counterflow_reactivate_staff(self, user_id: int) -> None:
        """CounterFlow — Reactivate a previously deactivated staff account."""
        user = self.counterflow_session.get(CounterFlowUser, user_id)
        if user and user.counterflow_role == "STAFF":
            user.counterflow_is_active = True
            self.counterflow_session.commit()

    def counterflow_change_password(
        self,
        user_id:      int,
        new_password: str,
    ) -> None:
        """CounterFlow — Change password for any user (Admin only action)."""
        counterflow_validate_password_policy(new_password)
        user = self.counterflow_session.get(CounterFlowUser, user_id)
        if user:
            user.counterflow_password_hash = counterflow_hash_password(new_password)
            self.counterflow_session.commit()

    # ── Internal Helpers ───────────────────────────────────────

    def _counterflow_assert_username_free(self, username: str) -> None:
        existing = (
            self.counterflow_session
            .query(CounterFlowUser)
            .filter_by(counterflow_username=username.strip().lower())
            .first()
        )
        if existing:
            raise CounterFlowDuplicateUserError(
                f"Username '{username}' is already taken. Please choose another."
            )
