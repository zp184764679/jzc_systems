import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ENDPOINTS } from "../api/endpoints"

export default function RFQSendPanel({ rfqId }) {
  const [suppliers, setSuppliers] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [links, setLinks] = useState([])
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    fetch(ENDPOINTS.SUPPLIER.GET_ALL)
      .then(r => r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`)))
      .then(setSuppliers)
      .catch(e => setErr(`加载供应商失败：${e.message}`))
  }, [])

  const toggle = (id) => {
    const s = new Set(selected)
    s.has(id) ? s.delete(id) : s.add(id)
    setSelected(s)
  }

  const send = async () => {
    setErr('')
    setLinks([])
    if (rfqId === undefined || rfqId === null || rfqId === '') {
      setErr('没有 RFQ 编号，请先创建 RFQ 或在上方输入框填写。')
      return
    }
    const body = { supplier_ids: Array.from(selected) }
    if (!body.supplier_ids.length) {
      setErr('请至少勾选一个供应商。')
      return
    }

    try {
      setLoading(true)
      const res = await fetch(ENDPOINTS.RFQ.SEND(rfqId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      const txt = await res.text()
      if (!res.ok) {
        // 尝试解析更友好的错误
        try {
          const j = JSON.parse(txt)
          throw new Error(j.error ? `发送失败：${j.error}` : `发送失败：HTTP ${res.status}`)
        } catch {
          throw new Error(`发送失败：HTTP ${res.status} ${txt || ''}`)
        }
      }
      const data = txt ? JSON.parse(txt) : {}
      const got = Array.isArray(data?.links) ? data.links : []
      setLinks(got)

      // 实时反馈：若只选 1 个供应商，直接跳转到报价提交页
      if (got.length === 1 && got[0]?.submit_url) {
        navigate(got[0].submit_url)
      } else if (got.length === 0) {
        setErr('后端没有返回报价链接，请确认 RFQ 是否存在。')
      }
    } catch (e) {
      setErr(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  const safeLinks = Array.isArray(links) ? links : []

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-semibold">选择供应商并发送</h3>

      {!!err && (
        <div className="p-3 rounded border border-red-300 bg-red-50 text-red-700 text-sm">
          {err}
        </div>
      )}

      <ul className="divide-y rounded border">
        {suppliers.map(s => (
          <li key={s.id} className="flex items-center gap-3 p-3">
            <input type="checkbox" onChange={() => toggle(s.id)} />
            <span className="font-medium">{s.name}</span>
            <span className="text-sm text-gray-500">{s.contact_email}</span>
          </li>
        ))}
      </ul>

      <button
        onClick={send}
        disabled={loading}
        className={`px-4 py-2 rounded text-white ${loading ? 'bg-gray-500' : 'bg-black hover:opacity-90'}`}
      >
        {loading ? '正在发送…' : '发送 RFQ'}
      </button>

      {safeLinks.length > 1 && (
        <div className="mt-4">
          <h4 className="font-semibold">一次性报价链接（多选时会列出所有链接）</h4>
          <ul className="list-disc pl-5">
            {safeLinks.map(l => (
              <li key={l.supplier_id}>
                <a
                  className="text-blue-600 underline break-all"
                  href={l.submit_url}
                >
                  {l.submit_url}
                </a>
              </li>
            ))}
          </ul>
          <p className="text-sm text-gray-500 mt-2">
            链接是相对路径，已内置跳转；若需复制，请加前缀 <code>http://127.0.0.1:5173</code>。
          </p>
        </div>
      )}
    </div>
  )
}