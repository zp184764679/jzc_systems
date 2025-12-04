import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

function Translator({ onBack, user }) {
  const [inputMail, setInputMail] = useState('')
  const [mailResult, setMailResult] = useState('')
  const [myReply, setMyReply] = useState('')
  const [replyResult, setReplyResult] = useState('')
  const [targetLang, setTargetLang] = useState('中文')
  const [status, setStatus] = useState({ text: '就绪', type: '' })
  const [loadingMail, setLoadingMail] = useState(false)
  const [loadingReply, setLoadingReply] = useState(false)

  // 页面加载时尝试自动粘贴
  useEffect(() => {
    handlePaste()
  }, [])

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText()
      if (text) {
        setInputMail(text)
        setStatus({ text: '已从剪贴板粘贴', type: 'success' })
      }
    } catch (e) {
      // 用户可能没有授权剪贴板权限
    }
  }

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      setStatus({ text: '已复制到剪贴板', type: 'success' })
    } catch (e) {
      setStatus({ text: '复制失败', type: 'error' })
    }
  }

  const translateMail = async () => {
    if (!inputMail.trim()) {
      setStatus({ text: '请先输入邮件内容', type: 'error' })
      return
    }

    setLoadingMail(true)
    setStatus({ text: '翻译中...', type: 'loading' })
    setMailResult('')

    try {
      const resp = await fetch(`${API_BASE}/api/translate/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          content: inputMail,
          target: targetLang
        })
      })

      const data = await resp.json()

      if (data.result) {
        setMailResult(data.result)
        setStatus({ text: '翻译完成', type: 'success' })
      } else {
        setStatus({ text: `翻译失败: ${data.error || '未知错误'}`, type: 'error' })
      }
    } catch (e) {
      setStatus({ text: `请求失败: ${e.message}`, type: 'error' })
    } finally {
      setLoadingMail(false)
    }
  }

  const translateReply = async () => {
    if (!myReply.trim()) {
      setStatus({ text: '请先输入回复内容', type: 'error' })
      return
    }

    setLoadingReply(true)

    // 检测目标语言
    let target = 'English'
    if (inputMail) {
      try {
        const resp = await fetch(`${API_BASE}/api/translate/detect`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: inputMail })
        })
        const data = await resp.json()
        if (data.lang === '日本語') target = '日本語'
        else if (data.lang === '中文') target = 'English'
        else target = data.lang
      } catch (e) {
        // 默认英文
      }
    }

    setStatus({ text: `翻译成${target}中...`, type: 'loading' })
    setReplyResult('')

    try {
      const resp = await fetch(`${API_BASE}/api/translate/text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          content: myReply,
          target,
          context: inputMail,
          is_reply: true
        })
      })

      const data = await resp.json()

      if (data.result) {
        setReplyResult(data.result)
        setStatus({ text: `翻译完成 (${target})`, type: 'success' })
      } else {
        setStatus({ text: `翻译失败: ${data.error || '未知错误'}`, type: 'error' })
      }
    } catch (e) {
      setStatus({ text: `请求失败: ${e.message}`, type: 'error' })
    } finally {
      setLoadingReply(false)
    }
  }

  const isMobile = typeof window !== 'undefined' && window.innerWidth < 900

  const styles = {
    container: {
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
      padding: isMobile ? '16px' : '24px',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      color: '#e0e0e0'
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '24px',
      flexWrap: 'wrap',
      gap: '12px'
    },
    title: {
      fontSize: isMobile ? '20px' : '24px',
      fontWeight: '500',
      color: '#fff',
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    },
    backBtn: {
      padding: '8px 16px',
      background: 'rgba(255,255,255,0.1)',
      border: '1px solid rgba(255,255,255,0.2)',
      borderRadius: '8px',
      color: '#fff',
      cursor: 'pointer',
      fontSize: '14px',
      transition: 'all 0.2s'
    },
    mainGrid: {
      display: 'grid',
      gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr',
      gap: '20px'
    },
    section: {
      background: 'rgba(255,255,255,0.05)',
      borderRadius: '12px',
      padding: '16px',
      border: '1px solid rgba(255,255,255,0.1)'
    },
    sectionTitle: {
      fontSize: '13px',
      color: '#888',
      marginBottom: '10px',
      display: 'flex',
      alignItems: 'center',
      gap: '8px'
    },
    titleBar: {
      width: '3px',
      height: '14px',
      background: '#4facfe',
      borderRadius: '2px'
    },
    textarea: {
      width: '100%',
      height: '160px',
      background: 'rgba(0,0,0,0.3)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '8px',
      padding: '12px',
      color: '#fff',
      fontSize: '14px',
      lineHeight: '1.6',
      resize: 'none',
      fontFamily: 'inherit',
      boxSizing: 'border-box'
    },
    resultBox: {
      background: 'rgba(0,0,0,0.3)',
      border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: '8px',
      padding: '12px',
      minHeight: '160px',
      fontSize: '14px',
      lineHeight: '1.6',
      whiteSpace: 'pre-wrap',
      wordBreak: 'break-word'
    },
    controls: {
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      marginTop: '12px',
      flexWrap: 'wrap'
    },
    select: {
      background: 'rgba(0,0,0,0.3)',
      border: '1px solid rgba(255,255,255,0.2)',
      borderRadius: '6px',
      padding: '8px 12px',
      color: '#fff',
      fontSize: '14px',
      cursor: 'pointer'
    },
    btn: {
      background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
      border: 'none',
      borderRadius: '6px',
      padding: '8px 18px',
      color: '#000',
      fontSize: '14px',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'all 0.2s'
    },
    btnSecondary: {
      background: 'rgba(255,255,255,0.1)',
      border: '1px solid rgba(255,255,255,0.2)',
      borderRadius: '6px',
      padding: '8px 14px',
      color: '#fff',
      fontSize: '13px',
      cursor: 'pointer'
    },
    divider: {
      gridColumn: '1 / -1',
      height: '1px',
      background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
      margin: '8px 0'
    },
    rowTitle: {
      gridColumn: '1 / -1',
      fontSize: '15px',
      color: '#fff',
      padding: '8px 0',
      display: 'flex',
      alignItems: 'center',
      gap: '10px'
    },
    status: {
      textAlign: 'center',
      padding: '12px',
      fontSize: '13px',
      color: status.type === 'loading' ? '#4facfe' : status.type === 'success' ? '#00f2a0' : status.type === 'error' ? '#ff6b6b' : '#888'
    }
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.title}>
          <span>📧</span>
          邮件翻译助手
        </div>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', color: '#888' }}>
            {user?.full_name || user?.username}
          </span>
          <button style={styles.backBtn} onClick={onBack}>
            返回门户
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={styles.mainGrid}>
        {/* 收到的邮件 */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>
            <div style={styles.titleBar}></div>
            收到的邮件
          </div>
          <textarea
            style={styles.textarea}
            placeholder="粘贴收到的邮件内容..."
            value={inputMail}
            onChange={(e) => setInputMail(e.target.value)}
          />
          <div style={styles.controls}>
            <button style={styles.btnSecondary} onClick={handlePaste}>
              📋 粘贴
            </button>
            <span style={{ color: '#666' }}>→</span>
            <select
              style={styles.select}
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
            >
              <option value="中文">中文</option>
              <option value="English">English</option>
              <option value="日本語">日本語</option>
            </select>
            <button
              style={{ ...styles.btn, opacity: loadingMail ? 0.6 : 1 }}
              onClick={translateMail}
              disabled={loadingMail}
            >
              {loadingMail ? '翻译中...' : '翻译邮件'}
            </button>
          </div>
        </div>

        {/* 翻译结果 */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>
            <div style={styles.titleBar}></div>
            翻译结果
          </div>
          <div style={{ ...styles.resultBox, color: mailResult ? '#fff' : '#555' }}>
            {mailResult || '翻译结果将显示在这里'}
          </div>
          <div style={styles.controls}>
            <button
              style={styles.btnSecondary}
              onClick={() => mailResult && copyToClipboard(mailResult)}
            >
              📋 复制
            </button>
          </div>
        </div>

        {/* 分隔线 */}
        <div style={styles.divider}></div>
        <div style={styles.rowTitle}>
          <span>✍️</span>
          写回复
          <div style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.1)' }}></div>
        </div>

        {/* 我的回复 */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>
            <div style={styles.titleBar}></div>
            我的回复（中文）
          </div>
          <textarea
            style={styles.textarea}
            placeholder="用中文写你的回复..."
            value={myReply}
            onChange={(e) => setMyReply(e.target.value)}
          />
          <div style={styles.controls}>
            <button
              style={{ ...styles.btn, opacity: loadingReply ? 0.6 : 1 }}
              onClick={translateReply}
              disabled={loadingReply}
            >
              {loadingReply ? '翻译中...' : '翻译回复'}
            </button>
            <span style={{ fontSize: '12px', color: '#666' }}>
              自动检测对方语言
            </span>
          </div>
        </div>

        {/* 回复翻译结果 */}
        <div style={styles.section}>
          <div style={styles.sectionTitle}>
            <div style={styles.titleBar}></div>
            翻译后的回复
          </div>
          <div style={{ ...styles.resultBox, color: replyResult ? '#fff' : '#555' }}>
            {replyResult || '翻译后的回复将显示在这里'}
          </div>
          <div style={styles.controls}>
            <button
              style={styles.btnSecondary}
              onClick={() => replyResult && copyToClipboard(replyResult)}
            >
              📋 复制
            </button>
          </div>
        </div>
      </div>

      {/* Status */}
      <div style={styles.status}>
        {status.type === 'loading' && <span style={{ marginRight: '8px' }}>⏳</span>}
        {status.text}
      </div>
    </div>
  )
}

export default Translator
