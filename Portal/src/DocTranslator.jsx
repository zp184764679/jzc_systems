import { useState } from 'react'

function DocTranslator({ onBack, user }) {
  const [iframeError, setIframeError] = useState(false)

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 900

  // 如果iframe加载失败，显示备用方案
  if (iframeError) {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
        color: '#fff'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔒</div>
        <div style={{ fontSize: '18px', marginBottom: '12px' }}>Claude.ai 无法在此嵌入</div>
        <div style={{ fontSize: '14px', color: '#888', marginBottom: '24px' }}>
          请点击下方按钮在新窗口中打开
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <a
            href="https://claude.ai/new"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              borderRadius: '8px',
              color: '#000',
              textDecoration: 'none',
              fontWeight: '600'
            }}
          >
            打开 Claude.ai
          </a>
          <button
            onClick={onBack}
            style={{
              padding: '12px 24px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '8px',
              color: '#fff',
              cursor: 'pointer'
            }}
          >
            返回
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#1a1a2e'
    }}>
      {/* 顶部工具栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '12px 20px',
        background: 'rgba(0,0,0,0.3)',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#fff'
        }}>
          <span style={{ fontSize: '20px' }}>📄</span>
          <span style={{ fontSize: '16px', fontWeight: '500' }}>文档翻译工具</span>
          <span style={{ fontSize: '12px', color: '#888', marginLeft: '10px' }}>
            上传PDF文件，让Claude帮你翻译
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '13px', color: '#888' }}>
            {user?.full_name || user?.username}
          </span>
          <a
            href="https://claude.ai/new"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              padding: '6px 12px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              color: '#fff',
              textDecoration: 'none',
              fontSize: '13px'
            }}
          >
            新窗口打开
          </a>
          <button
            onClick={onBack}
            style={{
              padding: '6px 12px',
              background: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              color: '#fff',
              cursor: 'pointer',
              fontSize: '13px'
            }}
          >
            返回门户
          </button>
        </div>
      </div>

      {/* Claude.ai iframe */}
      <iframe
        src="https://claude.ai/new"
        style={{
          flex: 1,
          width: '100%',
          border: 'none'
        }}
        onError={() => setIframeError(true)}
        title="Claude AI"
        allow="clipboard-read; clipboard-write"
      />
    </div>
  )
}

export default DocTranslator
