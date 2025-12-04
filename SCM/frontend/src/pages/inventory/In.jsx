// src/pages/inventory/In.jsx
// 入库登记（简化版）

import React, { useState } from 'react'
import { inventoryApi } from '../../services/api'

const L = {
  page: { maxWidth: 1040, margin: '0 auto', padding: 16 },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  card: {
    background: '#fff', border: '1px solid #E5E7EB', borderRadius: 14, padding: 12,
    boxShadow: '0 1px 0 rgba(0,0,0,0.02)',
  },
  grid3: { display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0,1fr))', gap: 12, alignItems: 'start' },
  fieldCol: { display: 'flex', flexDirection: 'column', gap: 6, minWidth: 0 },
  label: { fontSize: 12, color: '#64748b', fontWeight: 500, letterSpacing: .2 },
  input: { height: 38, width: '100%', borderRadius: 10, background: '#fff', border: '1px solid #D2D2D7', padding: '0 12px', fontSize: 14, boxSizing: 'border-box', outline: 'none' },
  btn: { height: 36, padding: '0 12px', borderRadius: 12, background: '#fff', border: '1px solid #D2D2D7', cursor: 'pointer' },
}

const todayStr = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
}

export default function InventoryIn() {
  const [form, setForm] = useState({
    product_text: '',
    qty: '',
    bin_code: '',
    location: '',
    order_no: '',
    uom: 'pcs',
    remark: '',
    occurred_at: todayStr(),
  })
  const [submitting, setSubmitting] = useState(false)

  const onChange = (k, v) => setForm((s) => ({ ...s, [k]: v }))

  const onReset = () => {
    setForm({
      product_text: '',
      qty: '',
      bin_code: '',
      location: '',
      order_no: '',
      uom: 'pcs',
      remark: '',
      occurred_at: todayStr(),
    })
  }

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!form.product_text.trim()) { alert('请填写内部图号'); return }
    const qtyNum = Number(form.qty)
    if (!qtyNum || qtyNum <= 0) { alert('数量必须大于0'); return }
    if (!form.bin_code.trim()) { alert('请填写仓位'); return }

    setSubmitting(true)
    try {
      await inventoryApi.createIn({
        product_text: form.product_text,
        qty: qtyNum,
        bin_code: form.bin_code,
        location: form.location || undefined,
        order_no: form.order_no || undefined,
        uom: form.uom || 'pcs',
        remark: form.remark || undefined,
      })
      alert('入库登记成功')
      onReset()
    } catch (err) {
      console.error(err)
      alert('入库失败: ' + (err.response?.data?.error || err.message))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={L.page}>
      <div style={L.header}>
        <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>入库登记</h2>
        <button onClick={onSubmit} disabled={submitting} style={L.btn}>
          {submitting ? '提交中…' : '提交入库'}
        </button>
      </div>

      <div style={{ ...L.card, marginBottom: 12 }}>
        <div style={L.grid3}>
          <div style={L.fieldCol}>
            <div style={L.label}>内部图号 *</div>
            <input style={L.input} value={form.product_text} onChange={(e) => onChange('product_text', e.target.value)} placeholder="必填" />
          </div>
          <div style={L.fieldCol}>
            <div style={L.label}>数量 *</div>
            <input type="number" min="0" step="1" style={L.input} value={form.qty} onChange={(e) => onChange('qty', e.target.value)} placeholder="必填" />
          </div>
          <div style={L.fieldCol}>
            <div style={L.label}>仓位 *</div>
            <input style={L.input} value={form.bin_code} onChange={(e) => onChange('bin_code', e.target.value)} placeholder="必填，如A1-01" />
          </div>
          <div style={L.fieldCol}>
            <div style={L.label}>地点</div>
            <select style={L.input} value={form.location} onChange={(e) => onChange('location', e.target.value)}>
              <option value="">请选择</option>
              <option value="深圳">深圳</option>
              <option value="东莞">东莞</option>
            </select>
          </div>
          <div style={L.fieldCol}>
            <div style={L.label}>订单号</div>
            <input style={L.input} value={form.order_no} onChange={(e) => onChange('order_no', e.target.value)} placeholder="可选" />
          </div>
          <div style={L.fieldCol}>
            <div style={L.label}>单位</div>
            <input style={L.input} value={form.uom} onChange={(e) => onChange('uom', e.target.value)} placeholder="默认pcs" />
          </div>
          <div style={L.fieldCol}>
            <div style={L.label}>备注</div>
            <input style={L.input} value={form.remark} onChange={(e) => onChange('remark', e.target.value)} placeholder="可选" />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8 }}>
        <button type="button" onClick={onSubmit} disabled={submitting} style={L.btn}>
          {submitting ? '提交中…' : '提交入库'}
        </button>
        <button type="button" onClick={onReset} style={L.btn}>重置</button>
      </div>
    </div>
  )
}
