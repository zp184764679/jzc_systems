/**
 * Two-Factor Verification Component
 * Used during login when 2FA is enabled
 */
import { useState } from 'react';
import './TwoFactorVerify.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function TwoFactorVerify({ userId, username, onSuccess, onCancel }) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [useBackup, setUseBackup] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();

    const codeLength = useBackup ? 9 : 6; // Backup codes are XXXX-XXXX format
    if (!code || (useBackup ? code.replace('-', '').length !== 8 : code.length !== 6)) {
      setError(useBackup ? '请输入完整的备用码 (格式: XXXX-XXXX)' : '请输入6位验证码');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const res = await fetch(`${API_BASE}/2fa/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          code: code,
          is_backup: useBackup
        })
      });

      const data = await res.json();

      if (data.code === 0) {
        // Save token and user info
        localStorage.setItem('token', data.data.token);
        localStorage.setItem('user', JSON.stringify(data.data.user));
        onSuccess?.(data.data);
      } else {
        setError(data.message || '验证失败');
      }
    } catch (err) {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleCodeChange = (e) => {
    let value = e.target.value;
    if (useBackup) {
      // Allow alphanumeric and dash for backup codes
      value = value.toUpperCase().replace(/[^A-Z0-9-]/g, '');
      // Auto-format backup code
      if (value.length === 4 && !value.includes('-')) {
        value += '-';
      }
      value = value.slice(0, 9);
    } else {
      // Only digits for TOTP
      value = value.replace(/\D/g, '').slice(0, 6);
    }
    setCode(value);
  };

  const toggleMode = () => {
    setUseBackup(!useBackup);
    setCode('');
    setError('');
  };

  return (
    <div className="tfa-verify-container">
      <div className="tfa-verify-card">
        <div className="tfa-verify-icon">
          <svg viewBox="0 0 24 24" width="48" height="48" fill="currentColor">
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
          </svg>
        </div>

        <h2>双因素验证</h2>
        <p className="tfa-verify-desc">
          {useBackup
            ? '请输入您的备用码'
            : '请输入验证器应用显示的验证码'
          }
        </p>

        <p className="tfa-verify-user">
          用户: <strong>{username}</strong>
        </p>

        {error && <div className="tfa-verify-error">{error}</div>}

        <form onSubmit={handleVerify}>
          <input
            type="text"
            value={code}
            onChange={handleCodeChange}
            placeholder={useBackup ? 'XXXX-XXXX' : '000000'}
            className={`tfa-verify-input ${useBackup ? 'backup' : ''}`}
            autoFocus
            autoComplete="one-time-code"
          />

          <button
            type="submit"
            className="tfa-verify-btn primary"
            disabled={loading}
          >
            {loading ? '验证中...' : '验证'}
          </button>
        </form>

        <button
          type="button"
          className="tfa-verify-link"
          onClick={toggleMode}
        >
          {useBackup ? '使用验证器应用' : '使用备用码'}
        </button>

        <button
          type="button"
          className="tfa-verify-cancel"
          onClick={onCancel}
        >
          取消登录
        </button>
      </div>
    </div>
  );
}

export default TwoFactorVerify;
