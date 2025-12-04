// CRM新建订单页面
import React, { useMemo, useRef, useState, useCallback, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";

/* ========== 工具函数 ========== */
const toInt = (v) => (Number.isFinite(Number(v)) ? Math.trunc(Number(v)) : 0);
const toFloat = (v, d = 2) => {
  const n = Number(v);
  return Number.isFinite(n) ? Number(n.toFixed(d)) : 0;
};
const notEmpty = (v) => v !== undefined && v !== null && String(v).trim() !== "";
const toPercentNumber = (v) => {
  const s = String(v ?? "").trim();
  if (!s) return 0;
  const cleaned = s.replace(/,/g, "").replace(/[％%]$/, "");
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : 0;
};
const todayStr = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/* 币种白名单 + 统一规范 */
const CURRENCIES = ["USD", "HKD", "JPY", "CNY"];
const normalizeCurrency = (v) => {
  if (!v) return "";
  const s = String(v).trim().toUpperCase();
  if (s === "RMB" || s === "CNY(RMB)" || s === "RENMINBI" || s === "人民币" || s === "CNH" || s === "CN¥" || s === "CNY¥" || s === "¥") {
    return "CNY";
  }
  if (s === "US$" || s === "USD$" || s === "$") return "USD";
  if (s === "HK$") return "HKD";
  if (s === "JP¥" || s === "JPY¥") return "JPY";
  return CURRENCIES.includes(s) ? s : "";
};
const symbolOf = (c) => ({ USD: "$", HKD: "HK$", JPY: "¥", CNY: "¥" }[c] || "");

/* 请求封装 */
function makeUrl(u, params) {
  let full = u.startsWith("/") ? "/api" + u : "/api/" + u;
  const cleaned = {};
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") cleaned[k] = v;
  });
  const usp = new URLSearchParams(cleaned);
  if ([...usp].length) full += (full.includes("?") ? "&" : "?") + usp.toString();
  return full;
}
async function GET(u, { params } = {}) {
  const res = await fetch(makeUrl(u, params), { credentials: "include" });
  if (!res.ok) throw new Error(`[${res.status}] ${res.statusText}`);
  try { return await res.json(); } catch { return await res.text(); }
}
async function POST(u, data) {
  const res = await fetch(makeUrl(u), {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`[${res.status}] ${res.statusText}`);
  try { return await res.json(); } catch { return await res.text(); }
}

/* ========== Apple 风格样式 ========== */
const L = {
  page: { maxWidth: 1040, margin: "0 auto", padding: 16 },
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 },
  headerRight: { display: "flex", gap: 8 },
  card: {
    background: "#fff",
    border: "1px solid #E5E7EB",
    borderRadius: 14,
    padding: 16,
    boxShadow: "0 1px 0 rgba(0,0,0,0.02)",
  },
  gridBasic3: {
    display: "grid",
    gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
    gap: 12,
    alignItems: "start",
  },
  basicCell: { maxWidth: 340, minWidth: 0 },
  fieldCol: { display: "flex", flexDirection: "column", gap: 6, minWidth: 0 },
  label: { fontSize: 12, color: "#64748b", fontWeight: 500, letterSpacing: 0.2 },
  input: {
    height: 38,
    width: "100%",
    maxWidth: "100%",
    borderRadius: 10,
    background: "#fff",
    border: "1px solid #D2D2D7",
    padding: "0 12px",
    fontSize: 14,
    boxSizing: "border-box",
    outline: "none",
  },
  btn: {
    height: 36,
    padding: "0 12px",
    borderRadius: 12,
    background: "#fff",
    border: "1px solid #D2D2D7",
    cursor: "pointer",
  },
  btnSm: {
    height: 32,
    padding: "0 10px",
    borderRadius: 12,
    background: "#fff",
    border: "1px solid #D2D2D7",
    cursor: "pointer",
  },
  linesWrap: { display: "flex", flexDirection: "column", gap: 10 },
  lineCard: { border: "1px solid #E5E7EB", borderRadius: 12, padding: 12, background: "#fff" },
  lineRowGrid: {
    display: "grid",
    gridTemplateColumns: "minmax(0,1.2fr) minmax(0,1fr) minmax(0,1.1fr) minmax(0,1.1fr) 160px",
    gap: 10,
    alignItems: "start",
  },
  lineRowGrid2: {
    display: "grid",
    gridTemplateColumns: "minmax(0,1.2fr) minmax(0,1fr) minmax(0,1.1fr) minmax(0,1.1fr) 160px",
    gap: 10,
    alignItems: "start",
  },
  lineFieldCol: { display: "flex", flexDirection: "column", gap: 6, minWidth: 0 },
  twoBlocksRow: { display: "flex", gap: 16, marginTop: 16, alignItems: "stretch" },
};

/* ========== Field 组件 ========== */
const Field = ({ label, children }) => (
  <div style={L.fieldCol}>
    <div style={L.label}>{label}</div>
    <div style={{ minWidth: 0 }}>{children}</div>
  </div>
);

/* ========== 客户选择 ========== */
function CustomerPicker({ valueName, onNameChange, onPick, defaultQuery = "" }) {
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const boxRef = useRef(null);
  const debounceTimer = useRef(null);
  const lastKeywordRef = useRef(defaultQuery);

  const normalizeList = (res) => {
    if (!res) return [];
    if (Array.isArray(res)) return res;
    if (Array.isArray(res.items)) return res.items;
    if (res.data && Array.isArray(res.data.items)) return res.data.items;
    if (Array.isArray(res.data)) return res.data;
    return [];
  };

  const fetchNow = useCallback(async (kw) => {
    setLoading(true);
    try {
      const res = await GET(`/customers?keyword=${encodeURIComponent(kw || "")}&page=1&page_size=20`);
      const items = normalizeList(res).map((c) => {
        const name = c.name || c.short_name || c.code;
        const tr = toPercentNumber(c.tax_points ?? c.tax_rate ?? c.vat_rate ?? c.taxRate ?? 0);
        const currencyRaw = c.currency_default || c.currency || c.default_currency || "";
        return { id: c.id ?? c.code, label: name, tax_rate: Number.isFinite(tr) ? tr : 0, currency: normalizeCurrency(currencyRaw) };
      });
      setOptions(items);
    } catch (e) {
      console.error(e);
      setOptions([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const debouncedFetch = useCallback((kw) => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      lastKeywordRef.current = kw;
      fetchNow(kw);
    }, 300);
  }, [fetchNow]);

  useEffect(() => {
    const onDocDown = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOptions([]);
    };
    document.addEventListener("mousedown", onDocDown);
    return () => document.removeEventListener("mousedown", onDocDown);
  }, []);

  return (
    <div ref={boxRef} style={{ position: "relative" }}>
      <input
        id="field-customer"
        style={L.input}
        placeholder="输入名称/简称/代码搜索"
        value={valueName}
        onChange={(e) => { const v = e.target.value; onNameChange(v); debouncedFetch(v); }}
        onFocus={() => debouncedFetch(lastKeywordRef.current)}
      />
      {!!options.length && (
        <div
          style={{
            position: "absolute", left: 0, right: 0, top: 40, maxHeight: 240, overflow: "auto",
            border: "1px solid #d2d2d7", borderRadius: 12, background: "#fff",
            boxShadow: "0 8px 30px rgba(16,24,40,.08), 0 2px 10px rgba(16,24,40,.06)", zIndex: 20
          }}
        >
          {options.map((o) => (
            <div
              key={o.id}
              style={{ padding: "8px 12px", cursor: "pointer" }}
              onMouseDown={async () => {
                try {
                  let tr = toPercentNumber(o.tax_rate);
                  let cur = normalizeCurrency(o.currency);
                  try {
                    const detail = await GET(`/customers/${encodeURIComponent(o.id)}`);
                    const d = detail?.data ?? detail;
                    const tp = d?.tax_points ?? d?.tax_rate ?? d?.vat_rate ?? d?.taxRate;
                    const parsed = toPercentNumber(tp);
                    if (parsed > 0) tr = parsed;
                    const dc = d?.currency_default || d?.currency || d?.default_currency;
                    if (dc) cur = normalizeCurrency(dc);
                  } catch {}
                  onPick({ id: o.id, name: o.label, tax_rate: tr, currency: cur });
                } finally { setOptions([]); }
              }}
              onMouseEnter={(e) => (e.currentTarget.style.background = "#f2f6ff")}
              onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
            >
              {o.label}
            </div>
          ))}
          {loading && <div style={{ padding: 8, color: "#64748b" }}>加载中…</div>}
        </div>
      )}
    </div>
  );
}

/* ========== 明细表格 ========== */
function LinesGrid({ rows, setRowField, addRow, removeRow, copyDown, custCurrency }) {
  const totalQty = useMemo(() => rows.reduce((s, r) => s + toInt(r.qty), 0), [rows]);
  const totalAmount = useMemo(() => rows.reduce((s, r) => s + toInt(r.qty) * toFloat(r.unit_price, 2), 0), [rows]);
  const totalSymbol = symbolOf(normalizeCurrency(custCurrency));

  return (
    <div style={L.linesWrap}>
      {rows.map((r, idx) => {
        const amount = toFloat(toInt(r.qty) * toFloat(r.unit_price, 2), 2);
        const showCur = CURRENCIES.includes(r.unit) ? r.unit : normalizeCurrency(custCurrency);
        return (
          <div key={idx} style={L.lineCard}>
            <div style={L.lineRowGrid}>
              <div style={L.lineFieldCol}>
                <div style={L.label}>内部图号</div>
                <input
                  id={`line-${idx}-product_text`}
                  style={L.input}
                  placeholder="输入内部图号"
                  value={r.product_text}
                  onChange={(e) => setRowField(idx, "product_text", e.target.value)}
                />
              </div>
              <div style={L.lineFieldCol}>
                <div style={L.label}>规格</div>
                <input style={L.input} value={r.spec} onChange={(e) => setRowField(idx, "spec", e.target.value)} />
              </div>
              <div style={L.lineFieldCol}>
                <div style={L.label}>物料编码</div>
                <input style={L.input} value={r.material_code} onChange={(e) => setRowField(idx, "material_code", e.target.value)} />
              </div>
              <div style={L.lineFieldCol}>
                <div style={L.label}>材质</div>
                <input style={L.input} value={r.material} onChange={(e) => setRowField(idx, "material", e.target.value)} />
              </div>
              <div style={L.lineFieldCol}>
                <div style={L.label}>数量</div>
                <input
                  id={`line-${idx}-qty`}
                  type="number"
                  style={L.input}
                  value={r.qty}
                  onChange={(e) => setRowField(idx, "qty", toInt(e.target.value))}
                  onKeyDown={(e) => { if (e.key === "Enter" && idx === rows.length - 1) addRow(); }}
                />
              </div>
            </div>

            <div style={{ ...L.lineRowGrid2, marginTop: 10 }}>
              <div style={{ ...L.lineFieldCol, gridColumn: "1 / 2" }}>
                <div style={L.label}>单位/币种</div>
                <select
                  style={L.input}
                  value={CURRENCIES.includes(r.unit) ? r.unit : ""}
                  onChange={(e) => setRowField(idx, "unit", e.target.value)}
                >
                  <option value="">（请选择）</option>
                  <option value="USD">美元 (USD)</option>
                  <option value="HKD">港币 (HKD)</option>
                  <option value="JPY">日元 (JPY)</option>
                  <option value="CNY">人民币 (CNY)</option>
                </select>
              </div>

              <div style={{ ...L.lineFieldCol, gridColumn: "2 / 3" }}>
                <div style={L.label}>税率(%)</div>
                <input
                  type="number"
                  step="0.01"
                  style={L.input}
                  value={r.tax_rate}
                  onChange={(e) => setRowField(idx, "tax_rate", toFloat(e.target.value, 2))}
                />
              </div>

              <div style={{ ...L.lineFieldCol, gridColumn: "3 / 4" }}>
                <div style={L.label}>单价</div>
                <input
                  type="number"
                  step="0.01"
                  style={L.input}
                  value={r.unit_price}
                  onChange={(e) => setRowField(idx, "unit_price", toFloat(e.target.value, 2))}
                  onKeyDown={(e) => { if (e.key === "Enter" && idx === rows.length - 1) addRow(); }}
                />
              </div>

              <div style={{ ...L.lineFieldCol, gridColumn: "4 / 5" }}>
                <div style={L.label}>小计</div>
                <div style={{ display: "flex", alignItems: "center" }}>
                  <div
                    style={{
                      height: 38,
                      width: 120,
                      textAlign: "right",
                      paddingRight: 8,
                      lineHeight: "38px",
                      border: "1px solid #E5E7EB",
                      borderRadius: 10,
                      background: "#fff",
                      boxSizing: "border-box",
                    }}
                  >
                    {symbolOf(showCur)}{amount.toFixed(2)}
                  </div>
                </div>
              </div>

              <div
                style={{
                  gridColumn: "5 / 6",
                  display: "flex",
                  alignItems: "flex-end",
                  justifyContent: "flex-end",
                  gap: 8,
                }}
              >
                <button type="button" style={L.btnSm} title="复制上一行" onClick={() => copyDown(idx)} disabled={idx === 0}>复制</button>
                <button type="button" style={L.btnSm} title="删除本行" onClick={() => removeRow(idx)} disabled={rows.length <= 1}>删除</button>
              </div>
            </div>
          </div>
        );
      })}

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: 4, marginTop: 2 }}>
        <button type="button" style={L.btn} onClick={addRow}>+ 增加一行</button>
        <div style={{ fontSize: 13 }}>
          <span style={{ marginRight: 16 }}>合计数量：<strong>{totalQty}</strong></span>
          <span>合计金额：<strong>{totalSymbol}{totalAmount.toFixed(2)}</strong></span>
        </div>
      </div>
    </div>
  );
}

/* ========== 需求与库存 ========== */
function DemandStockBlock({ form, setField, shortage, onUseSumQty, sumQty, orderQtyManual }) {
  return (
    <div style={{ flex: 1 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>需求与库存</h3>
      <div style={{ ...L.card, ...L.gridBasic3 }}>
        <div style={L.basicCell}>
          <Field label="订单数量">
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="number"
                style={{ ...L.input, flex: 1 }}
                value={form.order_qty}
                onChange={(e) => setField("order_qty", toInt(e.target.value))}
                onFocus={() => setField("__set_manual", true)}
              />
              <button
                type="button"
                style={L.btnSm}
                title="用明细合计覆盖订单数量"
                onClick={onUseSumQty}
              >
                ↻ 合计
              </button>
            </div>
            <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>
              {orderQtyManual ? "当前为手动覆盖模式" : "当前随明细合计自动同步"}
            </div>
          </Field>
        </div>

        <div style={L.basicCell}>
          <Field label="预测数量">
            <input type="number" style={L.input} value={form.forecast_qty} onChange={(e) => setField("forecast_qty", toInt(e.target.value))} />
          </Field>
        </div>

        <div style={L.basicCell}>
          <Field label="已交数量">
            <input type="number" style={L.input} value={form.delivered_qty} onChange={(e) => setField("delivered_qty", toInt(e.target.value))} />
          </Field>
        </div>

        <div style={L.basicCell}>
          <Field label="欠交数量">
            <input readOnly style={L.input} value={shortage} />
          </Field>
        </div>

        <div style={L.basicCell}>
          <Field label="成品在库存">
            <input type="number" style={L.input} value={form.stock_finished_qty} onChange={(e) => setField("stock_finished_qty", toInt(e.target.value))} />
          </Field>
        </div>

        <div style={L.basicCell}>
          <Field label="库存所在地">
            <input style={L.input} placeholder="如：东莞仓 / 香港仓" value={form.stock_location} onChange={(e) => setField("stock_location", e.target.value)} />
          </Field>
        </div>
      </div>
    </div>
  );
}

/* ========== 包装 ========== */
function PackageBlock({ form, setField }) {
  return (
    <div style={{ flex: 1 }}>
      <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>包装</h3>
      <div style={{ ...L.card, ...L.gridBasic3 }}>
        <div style={L.basicCell}>
          <Field label="默认外包装"><input style={L.input} placeholder="如：外箱/胶袋/托盘…" value={form.default_outer_pack} onChange={(e) => setField("default_outer_pack", e.target.value)} /></Field>
        </div>
        <div style={L.basicCell}>
          <Field label="包装要求"><input style={L.input} value={form.package_requirement} onChange={(e) => setField("package_requirement", e.target.value)} /></Field>
        </div>
        <div style={L.basicCell}>
          <Field label="默认小袋数"><input type="number" style={L.input} value={form.default_small_bag_qty} onChange={(e) => setField("default_small_bag_qty", toInt(e.target.value))} /></Field>
        </div>
        <div style={L.basicCell}>
          <Field label="默认分箱数"><input type="number" style={L.input} value={form.default_box_qty} onChange={(e) => setField("default_box_qty", toInt(e.target.value))} /></Field>
        </div>
      </div>
    </div>
  );
}

/* ========== 主页面 ========== */
export default function OrderNew() {
  const nav = useNavigate();

  const [form, setForm] = useState({
    order_no: "",
    order_date: todayStr(),
    process_content: "",
    status: "Open",
    container_no: "",
    poid: "",
    request_date: todayStr(),
    customer_id: "",
    order_qty: 0,
    forecast_qty: 0,
    delivered_qty: 0,
    stock_finished_qty: 0,
    stock_location: "",
    package_requirement: "",
    default_outer_pack: "",
    default_small_bag_qty: 0,
    default_box_qty: 0,
    chinese_name: "",
    remarks: "",
  });

  const [orderQtyManual, setOrderQtyManual] = useState(false);
  const [custTaxRate, setCustTaxRate] = useState(0);
  const [custCurrency, setCustCurrency] = useState("");
  const [customerName, setCustomerName] = useState("");

  const [lines, setLines] = useState(() => ([
    { product_text: "", spec: "", material_code: "", material: "", qty: 1, unit: "", tax_rate: 0, unit_price: 0 },
  ]));
  const [errors, setErrors] = useState({});

  const setField = useCallback((k, v) => {
    if (k === "__set_manual") {
      setOrderQtyManual(true);
      return;
    }
    if (k === "order_qty") {
      setOrderQtyManual(true);
    }
    setForm((prev) => ({ ...prev, [k]: v }));
  }, []);

  const setLineField = useCallback((idx, k, v) => setLines((prev) => prev.map((row, i) => (i === idx ? { ...row, [k]: v } : row))), []);
  const addLine = useCallback(
    () => setLines((prev) => [
      ...prev,
      { product_text: "", spec: "", material_code: "", material: "", qty: 1, unit: normalizeCurrency(custCurrency) || "", tax_rate: custTaxRate, unit_price: 0 }
    ]),
    [custCurrency, custTaxRate]
  );
  const removeLine = useCallback((idx) => setLines((prev) => prev.filter((_, i) => i !== idx)), []);
  const copyDown = useCallback((idx) => {
    if (idx <= 0) return;
    setLines((prev) => {
      const p = prev[idx - 1]; const next = [...prev];
      next[idx] = { ...next[idx], product_text: p.product_text, spec: p.spec, material_code: p.material_code, material: p.material, unit: p.unit, tax_rate: p.tax_rate, unit_price: p.unit_price };
      return next;
    });
  }, []);

  const sumQty = useMemo(() => lines.reduce((s, r) => s + toInt(r.qty), 0), [lines]);

  useEffect(() => {
    if (!orderQtyManual && form.order_qty !== sumQty) {
      setForm((prev) => ({ ...prev, order_qty: sumQty }));
    }
  }, [sumQty, orderQtyManual]); // eslint-disable-line react-hooks/exhaustive-deps

  const shortage = useMemo(() => {
    const base = toInt(form.order_qty) || sumQty;
    const delivered = toInt(form.delivered_qty);
    const finished = toInt(form.stock_finished_qty);
    const forecast = toInt(form.forecast_qty);
    return Math.max(0, base - delivered - finished - forecast);
  }, [form.order_qty, form.delivered_qty, form.stock_finished_qty, form.forecast_qty, sumQty]);

  const onPickCustomer = useCallback(({ id, name, tax_rate, currency }) => {
    setCustomerName(name || "");
    setField("customer_id", id);
    const tr = Number.isFinite(tax_rate) ? tax_rate : 0;
    const cur = normalizeCurrency(currency || "");
    setCustTaxRate(tr);
    setCustCurrency(cur);
    setLines((prev) => prev.map((r) => ({ ...r, tax_rate: tr, unit: cur })));
  }, [setField]);

  const validate = useCallback(() => {
    const err = {};
    if (!notEmpty(form.order_no)) err.order_no = "必填";
    if (!notEmpty(form.customer_id)) err.customer_id = "必选";
    lines.forEach((r, i) => {
      if (!notEmpty(r.product_text)) err[`lines.${i}.product_text`] = "必填";
      if (toInt(r.qty) <= 0) err[`lines.${i}.qty`] = "数量>0";
    });
    setErrors(err);
    return Object.keys(err).length === 0;
  }, [form, lines]);

  const onSubmit = useCallback(async (e) => {
    e.preventDefault();
    if (!validate()) {
      alert("请先修正表单中的错误");
      return;
    }

    const lineRows = lines.map((r, i) => ({
      line_no: r.line_no || i + 1,
      product_id: r.product_id ?? null,
      product_text: r.product_text || null,
      spec: r.spec || null,
      material_code: r.material_code || null,
      material: r.material || null,
      qty: Number(r.qty) || 0,
      currency_code: normalizeCurrency(r.currency_code || r.unit) || null,
      tax_rate: (r.tax_rate === "" || r.tax_rate == null) ? 0 : Number(r.tax_rate),
      unit_price: Number(r.unit_price) || 0,
      amount: (Number(r.qty) || 0) * (Number(r.unit_price) || 0),
    }));

    const first = lineRows[0] || {};
    const sumAmt = lineRows.reduce((s, it) => s + (Number(it.amount) || 0), 0);
    const baseQty = toInt(form.order_qty) || sumQty;
    const mirroredUnitPrice = lineRows.length === 1 ? (Number(first.unit_price) || 0) : null;

    const payload = {
      order_no: form.order_no,
      order_date: form.order_date || null,
      status: form.status || "Open",
      request_date: form.request_date || null,
      due_date: form.request_date || form.due_date || null,
      customer_id: form.customer_id ? (String(form.customer_id).match(/^\d+$/) ? Number(form.customer_id) : form.customer_id) : null,
      poid: form.poid || null,
      process_content: form.process_content || null,
      container_code: form.container_no || null,
      packing_req: form.package_requirement || null,
      default_small_bag: toInt(form.default_small_bag_qty),
      default_box_num: toInt(form.default_box_qty),
      cn_name: form.chinese_name || null,
      remark: form.remarks || null,

      order_qty: baseQty,
      forecast_qty: toInt(form.forecast_qty),
      delivered_qty: toInt(form.delivered_qty),
      stock_qty: toInt(form.stock_finished_qty),
      stock_finished_qty: toInt(form.stock_finished_qty),
      shortage_qty: Math.max(0, baseQty - toInt(form.delivered_qty) - toInt(form.stock_finished_qty) - toInt(form.forecast_qty)),
      stock_location: form.stock_location || null,

      product: first.product_text || null,
      produce_no: first.product_text || null,

      amount_total: toFloat(sumAmt, 2),
      total: toFloat(sumAmt, 2),
      amount: toFloat(sumAmt, 2),
      qty_total: baseQty,
      unit_price: mirroredUnitPrice,

      lines: lineRows,
      items: lineRows,
    };

    try {
      await POST("/orders/", payload);
      alert("保存成功");
      nav("/orders");
    } catch (err) {
      console.error("Create order failed:", err);
      alert(err?.message || "保存失败");
    }
  }, [form, lines, nav, validate, sumQty]);

  const useSumQty = useCallback(() => {
    setOrderQtyManual(false);
    setForm((prev) => ({ ...prev, order_qty: sumQty }));
  }, [sumQty]);

  return (
    <div style={L.page}>
      <div style={L.header}>
        <h2 style={{ fontSize: 20, fontWeight: 700, margin: 0 }}>新建订单</h2>
        <div style={L.headerRight}>
          <Link to="/orders" style={{ lineHeight: "36px", textDecoration: "underline" }}>返回订单列表</Link>
          <button style={L.btn} onClick={onSubmit} type="button">保存</button>
        </div>
      </div>

      <form onSubmit={onSubmit}>
        <div style={{ ...L.card, marginBottom: 16 }}>
          <div style={L.gridBasic3}>
            <div style={L.basicCell}>
              <Field label="订单编号">
                <input id="field-order_no" style={L.input} value={form.order_no} onChange={(e) => setField("order_no", e.target.value)} />
                {errors.order_no && <em style={{ color: "#ef4444", fontSize: 12, marginLeft: 6 }}>必填</em>}
              </Field>
            </div>
            <div style={L.basicCell}>
              <Field label="订单日期">
                <input type="date" style={L.input} value={form.order_date || ""} onChange={(e) => setField("order_date", e.target.value)} />
              </Field>
            </div>
            <div style={L.basicCell}>
              <Field label="客户图号">
                <input style={L.input} value={form.process_content} onChange={(e) => setField("process_content", e.target.value)} />
              </Field>
            </div>
          </div>

          <div style={{ ...L.gridBasic3, marginTop: 8 }}>
            <div style={L.basicCell}>
              <Field label="状态">
                <select name="status" value={form.status} onChange={(e) => setField("status", e.target.value)} style={L.input}>
                  <option value="Open">进行中</option>
                  <option value="Closed">已关闭</option>
                  <option value="Cancelled">已取消</option>
                </select>
              </Field>
            </div>
            <div style={L.basicCell}>
              <Field label="货柜编号">
                <input style={L.input} value={form.container_no} onChange={(e) => setField("container_no", e.target.value)} />
              </Field>
            </div>
            <div style={L.basicCell}>
              <Field label="要求纳期">
                <input type="date" style={L.input} value={form.request_date || ""} onChange={(e) => setField("request_date", e.target.value)} />
              </Field>
            </div>
          </div>

          <div style={{ ...L.gridBasic3, marginTop: 8 }}>
            <div style={L.basicCell}>
              <Field label="客户">
                <CustomerPicker valueName={customerName} onNameChange={setCustomerName} onPick={onPickCustomer} />
                {errors.customer_id && <em style={{ color: "#ef4444", fontSize: 12, marginLeft: 6 }}>必选</em>}
              </Field>
            </div>
            <div style={L.basicCell}>
              <Field label="POID">
                <input style={L.input} value={form.poid} onChange={(e) => setField("poid", e.target.value)} />
              </Field>
            </div>
            <div style={L.basicCell}>
              <Field label="跟单员">
                <input style={L.input} value={form.chinese_name} onChange={(e) => setField("chinese_name", e.target.value)} />
              </Field>
            </div>
          </div>

          <div style={{ ...L.gridBasic3, marginTop: 8 }}>
            <div style={L.basicCell}>
              <Field label="备注">
                <input style={L.input} value={form.remarks} onChange={(e) => setField("remarks", e.target.value)} />
              </Field>
            </div>
            <div style={L.basicCell} />
            <div style={L.basicCell} />
          </div>
        </div>

        <div style={{ marginTop: 8 }}>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8 }}>明细</h3>
          <LinesGrid
            rows={lines}
            setRowField={setLineField}
            addRow={addLine}
            removeRow={removeLine}
            copyDown={copyDown}
            custCurrency={custCurrency}
          />
        </div>

        <div style={L.twoBlocksRow}>
          <DemandStockBlock
            form={form}
            setField={setField}
            shortage={shortage}
            onUseSumQty={useSumQty}
            sumQty={sumQty}
            orderQtyManual={orderQtyManual}
          />
          <PackageBlock form={form} setField={setField} />
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
          <button type="submit" style={L.btn}>保存</button>
          <Link to="/orders" style={{ lineHeight: "36px", textDecoration: "underline" }}>返回订单列表</Link>
        </div>
      </form>
    </div>
  );
}
