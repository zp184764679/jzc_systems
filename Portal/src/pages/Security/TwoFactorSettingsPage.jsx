/**
 * Two-Factor Authentication Settings Page
 */
import { useState } from 'react';
import TwoFactorSetup from '../../TwoFactorSetup';

function TwoFactorSettingsPage() {
  const [showSetup, setShowSetup] = useState(false);

  const handleSetupSuccess = () => {
    // Refresh page to update status
    window.location.reload();
  };

  return (
    <div style={{ padding: '24px' }}>
      <h2 style={{ margin: '0 0 24px 0', fontSize: '20px', color: '#333' }}>
        双因素认证设置
      </h2>

      <div style={{
        background: '#fff',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            background: '#e6f7ff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#1890ff'
          }}>
            <svg viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
            </svg>
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', color: '#333' }}>双因素认证 (2FA)</h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '14px', color: '#666' }}>
              使用验证器应用为您的账户添加额外的安全保护
            </p>
          </div>
        </div>

        <div style={{
          background: '#f5f5f5',
          padding: '16px',
          borderRadius: '8px',
          marginBottom: '24px'
        }}>
          <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#333' }}>
            什么是双因素认证？
          </h4>
          <p style={{ margin: 0, fontSize: '13px', color: '#666', lineHeight: 1.6 }}>
            双因素认证是一种额外的安全措施，除了密码之外，还需要输入验证器应用生成的动态验证码才能登录。
            这样即使密码泄露，攻击者也无法访问您的账户。
          </p>
        </div>

        <div style={{
          display: 'flex',
          gap: '16px',
          flexWrap: 'wrap'
        }}>
          <div style={{
            flex: '1 1 200px',
            padding: '16px',
            border: '1px solid #e8e8e8',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '13px', color: '#999', marginBottom: '4px' }}>支持的验证器</div>
            <div style={{ fontSize: '14px', color: '#333' }}>
              Google Authenticator, Microsoft Authenticator, Authy
            </div>
          </div>
          <div style={{
            flex: '1 1 200px',
            padding: '16px',
            border: '1px solid #e8e8e8',
            borderRadius: '8px'
          }}>
            <div style={{ fontSize: '13px', color: '#999', marginBottom: '4px' }}>备用码</div>
            <div style={{ fontSize: '14px', color: '#333' }}>
              启用后会生成 10 个备用码，用于手机丢失时登录
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px' }}>
          <button
            onClick={() => setShowSetup(true)}
            style={{
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              color: '#fff',
              background: '#1890ff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.background = '#40a9ff'}
            onMouseLeave={(e) => e.target.style.background = '#1890ff'}
          >
            设置双因素认证
          </button>
        </div>
      </div>

      {showSetup && (
        <TwoFactorSetup
          onClose={() => setShowSetup(false)}
          onSuccess={handleSetupSuccess}
        />
      )}
    </div>
  );
}

export default TwoFactorSettingsPage;
