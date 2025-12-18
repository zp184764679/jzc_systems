"""
Two-Factor Authentication Service
Provides TOTP generation, verification, and backup code management
"""
import pyotp
import secrets
import hashlib
import base64
from datetime import datetime
from typing import Tuple, List, Optional


def generate_totp_secret() -> str:
    """Generate a new TOTP secret key (Base32 encoded)"""
    return pyotp.random_base32()


def get_totp_uri(secret: str, username: str, issuer: str = "JZC Systems") -> str:
    """
    Generate the TOTP provisioning URI for QR code generation

    Args:
        secret: The TOTP secret key
        username: The user's username or email
        issuer: The application name shown in authenticator apps

    Returns:
        The provisioning URI string
    """
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a TOTP code

    Args:
        secret: The user's TOTP secret key
        code: The 6-digit code to verify
        valid_window: Number of 30-second windows to check (default 1 = +-30 seconds)

    Returns:
        True if the code is valid, False otherwise
    """
    if not code or len(code) != 6 or not code.isdigit():
        return False

    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=valid_window)


def generate_backup_codes(count: int = 10) -> List[Tuple[str, str]]:
    """
    Generate a set of backup codes

    Args:
        count: Number of backup codes to generate

    Returns:
        List of tuples (plain_code, hashed_code)
        plain_code: The 8-character code shown to the user (e.g., "ABCD-1234")
        hashed_code: SHA256 hash of the code for storage
    """
    codes = []
    for _ in range(count):
        # Generate 8 random alphanumeric characters
        raw_code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        # Format as XXXX-XXXX
        formatted_code = f"{raw_code[:4]}-{raw_code[4:]}"
        # Hash for storage
        hashed_code = hashlib.sha256(formatted_code.encode()).hexdigest()
        codes.append((formatted_code, hashed_code))
    return codes


def verify_backup_code(plain_code: str, hashed_code: str) -> bool:
    """
    Verify a backup code against its hash

    Args:
        plain_code: The plain text backup code (e.g., "ABCD-1234")
        hashed_code: The stored SHA256 hash

    Returns:
        True if the code matches, False otherwise
    """
    import hmac  # P3-38: 导入 hmac 用于常量时间比较

    # Normalize the code (uppercase, ensure format)
    normalized = plain_code.strip().upper()
    if '-' not in normalized and len(normalized) == 8:
        normalized = f"{normalized[:4]}-{normalized[4:]}"

    computed_hash = hashlib.sha256(normalized.encode()).hexdigest()
    # P3-38: 使用 hmac.compare_digest 防止时序攻击
    return hmac.compare_digest(computed_hash, hashed_code)


def get_current_totp_code(secret: str) -> str:
    """
    Get the current TOTP code (for testing/debugging only)

    Args:
        secret: The TOTP secret key

    Returns:
        The current 6-digit TOTP code
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


class TwoFactorService:
    """
    Service class for managing two-factor authentication
    Wraps database operations with business logic
    """

    def __init__(self, db_session):
        """
        Initialize with a database session

        Args:
            db_session: SQLAlchemy session
        """
        self.session = db_session

    def setup_2fa(self, user_id: int, username: str) -> dict:
        """
        Set up 2FA for a user (generates secret but doesn't enable yet)

        Returns:
            Dict with secret, qr_uri, and backup_codes
        """
        from .models import TwoFactorAuth, TwoFactorBackupCode

        # Check if already exists
        existing = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
        if existing and existing.is_enabled:
            raise ValueError("2FA is already enabled for this user")

        # Generate new secret
        secret = generate_totp_secret()
        qr_uri = get_totp_uri(secret, username)

        # Generate backup codes
        backup_codes = generate_backup_codes(10)

        if existing:
            # Update existing record
            existing.secret_key = secret
            existing.is_verified = False
            existing.updated_at = datetime.utcnow()
        else:
            # Create new record
            two_fa = TwoFactorAuth(
                user_id=user_id,
                secret_key=secret,
                is_enabled=False,
                is_verified=False
            )
            self.session.add(two_fa)

        # Delete old backup codes
        self.session.query(TwoFactorBackupCode).filter_by(user_id=user_id).delete()

        # Store new backup codes
        for plain_code, hashed_code in backup_codes:
            backup = TwoFactorBackupCode(
                user_id=user_id,
                code_hash=hashed_code
            )
            self.session.add(backup)

        self.session.commit()

        return {
            'secret': secret,
            'qr_uri': qr_uri,
            'backup_codes': [code for code, _ in backup_codes]
        }

    def verify_and_enable(self, user_id: int, code: str) -> bool:
        """
        Verify a TOTP code and enable 2FA if valid

        Args:
            user_id: The user's ID
            code: The 6-digit TOTP code

        Returns:
            True if verified and enabled successfully
        """
        from .models import TwoFactorAuth

        two_fa = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
        if not two_fa:
            raise ValueError("2FA setup not found")

        if two_fa.is_enabled:
            raise ValueError("2FA is already enabled")

        if not verify_totp_code(two_fa.secret_key, code):
            return False

        two_fa.is_verified = True
        two_fa.is_enabled = True
        two_fa.enabled_at = datetime.utcnow()
        two_fa.last_used_at = datetime.utcnow()
        self.session.commit()

        return True

    def verify_code(self, user_id: int, code: str) -> bool:
        """
        Verify a TOTP code for login

        Args:
            user_id: The user's ID
            code: The 6-digit TOTP code

        Returns:
            True if the code is valid
        """
        from .models import TwoFactorAuth

        two_fa = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
        if not two_fa or not two_fa.is_enabled:
            return False

        if verify_totp_code(two_fa.secret_key, code):
            two_fa.last_used_at = datetime.utcnow()
            self.session.commit()
            return True

        return False

    def verify_backup_code_for_login(self, user_id: int, code: str) -> bool:
        """
        Verify a backup code for login

        Args:
            user_id: The user's ID
            code: The backup code (e.g., "ABCD-1234")

        Returns:
            True if the code is valid and unused
        """
        from .models import TwoFactorBackupCode

        backup_codes = self.session.query(TwoFactorBackupCode).filter_by(
            user_id=user_id,
            is_used=False
        ).all()

        for backup in backup_codes:
            if verify_backup_code(code, backup.code_hash):
                backup.is_used = True
                backup.used_at = datetime.utcnow()
                self.session.commit()
                return True

        return False

    def disable_2fa(self, user_id: int) -> bool:
        """
        Disable 2FA for a user

        Args:
            user_id: The user's ID

        Returns:
            True if disabled successfully
        """
        from .models import TwoFactorAuth, TwoFactorBackupCode

        two_fa = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
        if not two_fa:
            return False

        # Delete 2FA record
        self.session.delete(two_fa)

        # Delete backup codes
        self.session.query(TwoFactorBackupCode).filter_by(user_id=user_id).delete()

        self.session.commit()
        return True

    def regenerate_backup_codes(self, user_id: int) -> List[str]:
        """
        Regenerate backup codes for a user

        Args:
            user_id: The user's ID

        Returns:
            List of new backup codes (plain text)
        """
        from .models import TwoFactorAuth, TwoFactorBackupCode

        two_fa = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
        if not two_fa or not two_fa.is_enabled:
            raise ValueError("2FA is not enabled")

        # Delete old backup codes
        self.session.query(TwoFactorBackupCode).filter_by(user_id=user_id).delete()

        # Generate new backup codes
        backup_codes = generate_backup_codes(10)

        # Store new backup codes
        for plain_code, hashed_code in backup_codes:
            backup = TwoFactorBackupCode(
                user_id=user_id,
                code_hash=hashed_code
            )
            self.session.add(backup)

        self.session.commit()

        return [code for code, _ in backup_codes]

    def get_2fa_status(self, user_id: int) -> dict:
        """
        Get the 2FA status for a user

        Args:
            user_id: The user's ID

        Returns:
            Dict with 2FA status information
        """
        from .models import TwoFactorAuth, TwoFactorBackupCode

        two_fa = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()

        if not two_fa:
            return {
                'is_enabled': False,
                'is_verified': False,
                'backup_codes_remaining': 0
            }

        # Count remaining backup codes
        remaining = self.session.query(TwoFactorBackupCode).filter_by(
            user_id=user_id,
            is_used=False
        ).count()

        return {
            'is_enabled': two_fa.is_enabled,
            'is_verified': two_fa.is_verified,
            'enabled_at': two_fa.enabled_at.isoformat() if two_fa.enabled_at else None,
            'last_used_at': two_fa.last_used_at.isoformat() if two_fa.last_used_at else None,
            'recovery_email': two_fa.recovery_email,
            'backup_codes_remaining': remaining
        }

    def is_2fa_required(self, user_id: int) -> bool:
        """
        Check if 2FA verification is required for a user

        Args:
            user_id: The user's ID

        Returns:
            True if 2FA is enabled and verification is required
        """
        from .models import TwoFactorAuth

        two_fa = self.session.query(TwoFactorAuth).filter_by(user_id=user_id).first()
        return two_fa is not None and two_fa.is_enabled
