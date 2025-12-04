// src/components/PrLogisticsPanel.jsx
import React from "react";

/**
 * 物流面板（单据层级）
 * props:
 *  - value: { ...logistics }
 *  - onChange: (patch) => void
 *
 * 字段尽量覆盖常见需求；你可以按需再扩展。
 */
const initLogistics = {
  deliverySite: "",      // 到货地点/仓库（如：东莞一仓）
  deliveryAddress: "",   // 详细地址
  contact: "",           // 收货联系人
  phone: "",             // 联系电话
  deliveryMethod: "快递/物流", // 运输方式（快递/物流/自提）
  freightPayer: "到付",  // 运费承担（到付/寄付/第三方）
  incoterm: "EXW",       // 贸易术语（EXW/FOB/CIF/DDP…）
  deliveryWindow: "",    // 到货时间窗（如：工作日9:00-17:00）
  requiredDate: "",      // 期望到货日
  packagingReq: "",      // 包装/托盘要求（是否打托、木箱/纸箱、规格…）
  unloadingReq: "",      // 卸货要求（是否需叉车/尾板）
  invoiceType: "专票13%", // 发票类型（普票/专票 3%/6%/13%…）
  invoiceTitle: "",      // 发票抬头
  taxNo: "",             // 纳税人识别号
  paymentTerm: "货到30天",// 付款条款（现结/7天/30天/OA等）
  currency: "CNY",       // 结算币种
  notes: "",             // 其他物流备注
};

export function getDefaultLogistics() { return { ...initLogistics }; }

export default function PrLogisticsPanel({ value, onChange }) {
  const v = { ...initLogistics, ...(value || {}) };
  const set = (k, val) => onChange?.({ [k]: val });

  return (
    <div className="rounded-xl border p-4 space-y-3 bg-white">
      <div className="font-semibold">物流 / 到货要求（单据层级）</div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-2">
        <input className="md:col-span-3 border p-2 rounded" placeholder="到货地点/仓库"
               value={v.deliverySite} onChange={e=>set("deliverySite", e.target.value)} />
        <input className="md:col-span-6 border p-2 rounded" placeholder="详细地址"
               value={v.deliveryAddress} onChange={e=>set("deliveryAddress", e.target.value)} />
        <input className="md:col-span-2 border p-2 rounded" placeholder="联系人"
               value={v.contact} onChange={e=>set("contact", e.target.value)} />
        <input className="md:col-span-1 border p-2 rounded" placeholder="电话"
               value={v.phone} onChange={e=>set("phone", e.target.value)} />

        <input className="md:col-span-2 border p-2 rounded" placeholder="运输方式（快递/物流/自提）"
               value={v.deliveryMethod} onChange={e=>set("deliveryMethod", e.target.value)} />
        <input className="md:col-span-2 border p-2 rounded" placeholder="运费承担（到付/寄付）"
               value={v.freightPayer} onChange={e=>set("freightPayer", e.target.value)} />
        <input className="md:col-span-2 border p-2 rounded" placeholder="贸易术语（EXW/FOB/…）"
               value={v.incoterm} onChange={e=>set("incoterm", e.target.value)} />
        <input className="md:col-span-3 border p-2 rounded" placeholder="到货时间窗（例：工作日9-17点）"
               value={v.deliveryWindow} onChange={e=>set("deliveryWindow", e.target.value)} />
        <input type="date" className="md:col-span-3 border p-2 rounded" placeholder="期望到货日"
               value={v.requiredDate} onChange={e=>set("requiredDate", e.target.value)} />

        <input className="md:col-span-4 border p-2 rounded" placeholder="包装/托盘要求"
               value={v.packagingReq} onChange={e=>set("packagingReq", e.target.value)} />
        <input className="md:col-span-4 border p-2 rounded" placeholder="卸货要求（叉车/尾板等）"
               value={v.unloadingReq} onChange={e=>set("unloadingReq", e.target.value)} />
        <input className="md:col-span-2 border p-2 rounded" placeholder="发票类型（普票/专票13%）"
               value={v.invoiceType} onChange={e=>set("invoiceType", e.target.value)} />
        <input className="md:col-span-2 border p-2 rounded" placeholder="币种（CNY/USD…）"
               value={v.currency} onChange={e=>set("currency", e.target.value)} />

        <input className="md:col-span-6 border p-2 rounded" placeholder="发票抬头"
               value={v.invoiceTitle} onChange={e=>set("invoiceTitle", e.target.value)} />
        <input className="md:col-span-6 border p-2 rounded" placeholder="纳税人识别号"
               value={v.taxNo} onChange={e=>set("taxNo", e.target.value)} />

        <input className="md:col-span-6 border p-2 rounded" placeholder="付款条款（如：货到30天）"
               value={v.paymentTerm} onChange={e=>set("paymentTerm", e.target.value)} />
        <textarea className="md:col-span-6 border p-2 rounded" rows={1} placeholder="其他物流备注"
                  value={v.notes} onChange={e=>set("notes", e.target.value)} />
      </div>
    </div>
  );
}
