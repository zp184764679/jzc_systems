import React, { useState } from "react";

/**
 * RejectReasonModal - 驳回原因弹窗
 * 用于输入驳回申请时的原因
 */
export default function RejectReasonModal({ isOpen, isLoading, onConfirm, onCancel }) {
  const [reason, setReason] = useState("");

  const handleConfirm = () => {
    if (!reason.trim()) {
      alert("请填写驳回原因");
      return;
    }
    onConfirm(reason);
    setReason("");
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50">
      <div className="bg-white w-full max-w-md rounded-lg shadow-lg border">
        {/* 标题 */}
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">驳回原因</h2>
        </div>

        {/* 内容 */}
        <div className="px-6 py-4 space-y-3">
          <textarea
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="请填写驳回的原因（必填）"
            disabled={isLoading}
            rows={5}
            className="w-full px-3 py-2 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-red-400 disabled:bg-gray-50"
          />
        </div>

        {/* 操作按钮 */}
        <div className="px-6 py-4 border-t flex gap-2 justify-end">
          <button
            onClick={onCancel}
            disabled={isLoading}
            className="px-4 py-2 border rounded text-sm hover:bg-gray-50 transition disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={handleConfirm}
            disabled={isLoading}
            className="px-4 py-2 bg-red-500 text-white rounded text-sm hover:bg-red-600 transition disabled:opacity-50"
          >
            {isLoading ? "处理中..." : "确认驳回"}
          </button>
        </div>
      </div>
    </div>
  );
}