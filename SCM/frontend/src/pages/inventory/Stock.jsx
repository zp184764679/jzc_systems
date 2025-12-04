// src/pages/inventory/Stock.jsx
// 库存总览（简化版 - 直接从库存流水聚合）

import React, { useEffect, useMemo, useState } from 'react'
import { inventoryApi } from '../../services/api'

/* ========== Apple 风样式 ========== */
const L = {
  page: { maxWidth: 1040, margin: '0 auto', padding: 16 },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  headerRight: { display: 'flex', gap: 8 },
  card: {
    background: '#fff',
    border: '1px solid #E5E7EB',
    borderRadius: 14,
    padding: 12,
    boxShadow: '0 1px 0 rgba(0,0,0,0.02)',
  },
  label: { fontSize: 12, color: '#64748b', fontWeight: 500, letterSpacing: 0.2 },
  input: {
    height: 38,
    width: '100%',
    borderRadius: 10,
    background: '#fff',
    border: '1px solid #D2D2D7',
    padding: '0 12px',
    fontSize: 14,
    boxSizing: 'border-box',
    outline: 'none',
  },
  btn: {
    height: 36,
    padding: '0 12px',
    borderRadius: 12,
    background: '#fff',
    border: '1px solid #D2D2D7',
    cursor: 'pointer',
  },
  btnSm: {
    height: 30,
    padding: '0 10px',
    borderRadius: 10,
    background: '#fff',
    border: '1px solid #D2D2D7',
    cursor: 'pointer',
    fontSize: 13,
  },
}

export default function Stock() {
  const [q, setQ] = useState('')
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [openKey, setOpenKey] = useState(null)
  const [tx, setTx] = useState({ loading: false, list: [] })

  // 加载库存总览
  const load = async () => {
    setLoading(true)
    try {
      const data = await inventoryApi.getStock({ page: 1, page_size: 200 })
      const items = Array.isArray(data?.items) ? data.items : []
      setRows(items)
    } catch (e) {
      console.error(e)
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  // 搜索过滤
  const currentRows = useMemo(() => {
    const kw = String(q || '').trim().toLowerCase()
    if (!kw) return rows
    return rows.filter(r => {
      const bag = [
        r.orderNo, r.internalNo, r.spec, r.bin, r.place,
      ].join(' ').toLowerCase()
      return bag.includes(kw)
    })
  }, [rows, q])

  // 导出 CSV
  const exportCSV = () => {
    const head = ['订单编号', '内部图号', '规格', '仓位', '数量', '单位', '地点']
    const lines = currentRows.map(r => [
      r.orderNo || '-', r.internalNo || '-', r.spec || '-', r.bin || '-', r.qty, r.uom || '-', r.place || '-',
    ])
    const csv = [head, ...lines].map(arr => arr.map(v => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `库存总览_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 打开详情
  const openDetail = async (internalNo) => {
    setOpenKey(internalNo)
    setTx({ loading: true, list: [] })

    try {
      const data = await inventoryApi.getTransactions({
        internal_no: internalNo,
        page: 1,
        page_size: 100
      })
      const list = Array.isArray(data?.items) ? data.items : []
      setTx({ loading: false, list })
    } catch (e) {
      console.error(e)
      setTx({ loading: false, list: [] })
    }
  }

  const closeDetail = () => {
    setOpenKey(null)
    setTx({ loading: false, list: [] })
  }

  const currentRow = useMemo(() => rows.find(r => r.internalNo === openKey) || null, [rows, openKey])

  const th = { padding: '10px 12px', borderBottom: '1px solid #eee' }
  const td = { padding: '10px 12px', borderBottom: '1px solid #f2f2f2' }

  return (
    <div style={L.page}>
      {/* 顶部操作 */}
      <div style={L.header}>
        <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>库存总览</h2>
        <div style={L.headerRight}>
          <button onClick={exportCSV} style={L.btn}>导出CSV</button>
        </div>
      </div>

      {/* 搜索 */}
      <div style={{ ...L.card, marginBottom: 12 }}>
        <div style={{ width: 320 }}>
          <div style={L.label}>搜索</div>
          <input
            placeholder="按订单编号/内部图号/规格/仓位/地点搜索"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            style={L.input}
          />
        </div>
      </div>

      {/* 表格 */}
      <div style={{ overflow: 'auto', border: '1px solid #eee', borderRadius: 12 }}>
        <table style={{ minWidth: 900, width: '100%', fontSize: 14, borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f9fafb', textAlign: 'left' }}>
              <th style={th}>订单编号</th>
              <th style={th}>内部图号</th>
              <th style={th}>规格</th>
              <th style={th}>仓位</th>
              <th style={th}>数量</th>
              <th style={th}>单位</th>
              <th style={th}>地点</th>
              <th style={th}>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={8} style={{ padding: 16, textAlign: 'center', color: '#888' }}>加载中…</td></tr>
            ) : currentRows.length === 0 ? (
              <tr><td colSpan={8} style={{ padding: 16, textAlign: 'center', color: '#999' }}>暂无数据</td></tr>
            ) : (
              currentRows.map((r, idx) => (
                <tr key={r.internalNo || idx}>
                  <td style={td}>{r.orderNo || '-'}</td>
                  <td style={td}>{r.internalNo || '-'}</td>
                  <td style={td}>{r.spec || '-'}</td>
                  <td style={td}>{r.bin || '-'}</td>
                  <td style={td}>{r.qty}</td>
                  <td style={td}>{r.uom || 'pcs'}</td>
                  <td style={td}>{r.place || '-'}</td>
                  <td style={td}>
                    <button style={L.btnSm} onClick={() => openDetail(r.internalNo)}>详情</button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 详情模态 */}
      {openKey && (
        <div
          onClick={closeDetail}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: 780, maxWidth: '92vw', maxHeight: '88vh', overflow: 'auto',
              background: '#fff', border: '1px solid #e5e7eb', borderRadius: 14, boxShadow: '0 12px 28px rgba(0,0,0,0.12)',
              padding: 16
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>
                  库存详情 · {openKey}
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', color: '#475569', fontSize: 12 }}>
                  <span style={{ padding: '2px 8px', border: '1px solid #e2e8f0', borderRadius: 999 }}>
                    当前库存: {currentRow?.qty ?? '-'} {currentRow?.uom || ''}
                  </span>
                </div>
              </div>
              <button onClick={closeDetail} style={L.btnSm}>关闭</button>
            </div>

            <div style={{ ...L.card }}>
              {tx.loading ? (
                <div style={{ color: '#888' }}>加载中…</div>
              ) : tx.list.length === 0 ? (
                <div style={{ color: '#999' }}>暂无流水记录</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb', textAlign: 'left' }}>
                      <th style={th}>时间</th>
                      <th style={th}>类型</th>
                      <th style={th}>变更</th>
                      <th style={th}>订单号</th>
                      <th style={th}>备注</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tx.list.map((x, i) => (
                      <tr key={i}>
                        <td style={td}>{x.occurred_at || x.created_at || '-'}</td>
                        <td style={td}>{x.tx_type || '-'}</td>
                        <td style={td}>{x.qty_delta ?? '-'}</td>
                        <td style={td}>{x.order_no || '-'}</td>
                        <td style={td}>{x.remark || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
