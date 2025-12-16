/**
 * Two-Factor Authentication Setup Component
 */
import { useState, useEffect } from 'react';
import './TwoFactorSetup.css';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

function TwoFactorSetup({ onClose, onSuccess }) {
  const [step, setStep] = useState('initial'); // initial, setup, verify, complete
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [setupData, setSetupData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/2fa/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.code === 0) {
        setStatus(data.data);
        if (data.data.is_enabled) {
          setStep('enabled');
        }
      }
    } catch (err) {
      console.error('Failed to fetch 2FA status:', err);
    }
  };

  const handleSetup = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/2fa/setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        }
      });
      const data = await res.json();
      if (data.code === 0) {
        setSetupData(data.data);
        setStep('setup');
      } else {
        setError(data.message || '设置失败');
      }
    } catch (err) {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!verifyCode || verifyCode.length !== 6) {
      setError('请输入6位验证码');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/2fa/verify-setup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ code: verifyCode })
      });
      const data = await res.json();
      if (data.code === 0) {
        setStep('complete');
        onSuccess?.();
      } else {
        setError(data.message || '验证失败');
      }
    } catch (err) {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleDisable = async () => {
    const password = prompt('请输入当前密码以禁用双因素认证:');
    if (!password) return;

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/2fa/disable`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ password })
      });
      const data = await res.json();
      if (data.code === 0) {
        alert('双因素认证已禁用');
        setStep('initial');
        setStatus(null);
        fetchStatus();
      } else {
        setError(data.message || '禁用失败');
      }
    } catch (err) {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateBackupCodes = async () => {
    const code = prompt('请输入当前验证码以重新生成备用码:');
    if (!code) return;

    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${API_BASE}/2fa/backup-codes/regenerate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ code })
      });
      const data = await res.json();
      if (data.code === 0) {
        setSetupData({ ...setupData, backup_codes: data.data.backup_codes });
        alert('备用码已重新生成，请妥善保管！');
      } else {
        setError(data.message || '生成失败');
      }
    } catch (err) {
      setError('网络错误，请重试');
    } finally {
      setLoading(false);
    }
  };

  const renderInitial = () => (
    <div className="tfa-content">
      <div className="tfa-icon">
        <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
          <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
        </svg>
      </div>
      <h3>双因素认证 (2FA)</h3>
      <p className="tfa-desc">
        双因素认证可以为您的账户添加额外的安全保护层。
        启用后，登录时除了密码外，还需要输入验证器应用生成的动态验证码。
      </p>
      <div className="tfa-benefits">
        <div className="benefit-item">
          <span className="benefit-icon">✓</span>
          <span>防止密码泄露后的账户盗用</span>
        </div>
        <div className="benefit-item">
          <span className="benefit-icon">✓</span>
          <span>符合企业安全合规要求</span>
        </div>
        <div className="benefit-item">
          <span className="benefit-icon">✓</span>
          <span>提供备用码以防手机丢失</span>
        </div>
      </div>
      <button
        className="tfa-btn primary"
        onClick={handleSetup}
        disabled={loading}
      >
        {loading ? '正在设置...' : '开始设置'}
      </button>
    </div>
  );

  const renderSetup = () => (
    <div className="tfa-content">
      <h3>步骤 1: 扫描二维码</h3>
      <p className="tfa-desc">
        使用 Google Authenticator、Microsoft Authenticator 或其他 TOTP 应用扫描下方二维码。
      </p>
      <div className="qr-container">
        <img
          src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(setupData?.qr_uri || '')}`}
          alt="2FA QR Code"
          className="qr-code"
        />
      </div>
      <div className="manual-entry">
        <p>无法扫描？手动输入此密钥：</p>
        <code className="secret-key">{setupData?.secret}</code>
      </div>

      <h3>步骤 2: 保存备用码</h3>
      <p className="tfa-desc warning">
        请将以下备用码保存在安全的地方。如果您无法访问验证器应用，可以使用备用码登录。
        每个备用码只能使用一次。
      </p>
      <div className="backup-codes">
        {setupData?.backup_codes?.map((code, index) => (
          <span key={index} className="backup-code">{code}</span>
        ))}
      </div>

      <h3>步骤 3: 验证设置</h3>
      <form onSubmit={handleVerify} className="verify-form">
        <label>输入验证器应用显示的 6 位验证码：</label>
        <input
          type="text"
          value={verifyCode}
          onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          placeholder="000000"
          maxLength={6}
          className="verify-input"
          autoFocus
        />
        <button
          type="submit"
          className="tfa-btn primary"
          disabled={loading || verifyCode.length !== 6}
        >
          {loading ? '验证中...' : '验证并启用'}
        </button>
      </form>
    </div>
  );

  const renderComplete = () => (
    <div className="tfa-content">
      <div className="tfa-icon success">
        <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
          <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
        </svg>
      </div>
      <h3>设置完成！</h3>
      <p className="tfa-desc">
        双因素认证已成功启用。下次登录时，您需要输入验证器应用生成的验证码。
      </p>
      <div className="tfa-reminder">
        <strong>重要提醒：</strong>
        <ul>
          <li>请妥善保管您的备用码</li>
          <li>不要将验证器应用或备用码分享给他人</li>
          <li>如果更换手机，请提前备份或重新设置 2FA</li>
        </ul>
      </div>
      <button className="tfa-btn primary" onClick={onClose}>
        完成
      </button>
    </div>
  );

  const renderEnabled = () => (
    <div className="tfa-content">
      <div className="tfa-icon enabled">
        <svg viewBox="0 0 24 24" width="64" height="64" fill="currentColor">
          <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm-2 16l-4-4 1.41-1.41L10 14.17l6.59-6.59L18 9l-8 8z"/>
        </svg>
      </div>
      <h3>双因素认证已启用</h3>
      <p className="tfa-desc">
        您的账户受到双因素认证保护。
      </p>
      {status && (
        <div className="tfa-status-info">
          <p><strong>启用时间：</strong> {status.enabled_at ? new Date(status.enabled_at).toLocaleString() : '-'}</p>
          <p><strong>上次使用：</strong> {status.last_used_at ? new Date(status.last_used_at).toLocaleString() : '-'}</p>
          <p><strong>剩余备用码：</strong> {status.backup_codes_remaining} / 10</p>
        </div>
      )}
      <div className="tfa-actions">
        <button
          className="tfa-btn secondary"
          onClick={handleRegenerateBackupCodes}
          disabled={loading}
        >
          重新生成备用码
        </button>
        <button
          className="tfa-btn danger"
          onClick={handleDisable}
          disabled={loading}
        >
          禁用双因素认证
        </button>
      </div>
    </div>
  );

  return (
    <div className="tfa-modal-overlay" onClick={onClose}>
      <div className="tfa-modal" onClick={(e) => e.stopPropagation()}>
        <button className="tfa-close" onClick={onClose}>&times;</button>

        {error && <div className="tfa-error">{error}</div>}

        {step === 'initial' && renderInitial()}
        {step === 'setup' && renderSetup()}
        {step === 'complete' && renderComplete()}
        {step === 'enabled' && renderEnabled()}
      </div>
    </div>
  );
}

export default TwoFactorSetup;
