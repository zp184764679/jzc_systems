import React from "react";

const STATUS_MAP = {
  approved: "已批准",
  submitted: "待审批",
  rejected: "已驳回",
  draft: "草稿",
};

const STATUS_COLORS = {
  approved: "bg-green-100 text-green-700",
  submitted: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-700",
  draft: "bg-gray-100 text-gray-700",
};

const URGENCY_MAP = {
  高: "高",
  中: "中",
  低: "低",
};

const URGENCY_COLORS = {
  高: "bg-red-100 text-red-700",
  中: "bg-yellow-100 text-yellow-700",
  低: "bg-blue-100 text-blue-700",
};

const formatTime = (v) => {
  if (!v) return "-";
  try {
    const d = new Date(v);
    if (isNaN(d.getTime())) return "-";
    return d.toLocaleString("zh-CN", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "-";
  }
};

/**
 * DetailModal - 详情弹窗
 * 展示采购申请的完整信息和操作选项
 */
export default function DetailModal({
  isOpen,
  item,
  isLoading,
  onClose,
  onApprove,
  onReject,
  canApprove = false,
}) {
  if (!isOpen) return null;

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50">
        <div className="bg-white w-full max-w-2xl rounded-lg shadow-lg p-6">
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        </div>
      </div>
    );
  }

  if (item?.error) {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50">
        <div className="bg-white w-full max-w-2xl rounded-lg shadow-lg border">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">详情</h2>
          </div>
          <div className="px-6 py-4">
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded text-sm">
              {item.error}
            </div>
          </div>
          <div className="px-6 py-4 border-t flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded text-sm hover:bg-gray-50"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!item) {
    return null;
  }

  const statusCode = item.status_code || "draft";

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white w-full max-w-2xl rounded-lg shadow-lg border my-4">
        {/* 标题栏 */}
        <div className="px-6 py-4 border-b bg-gray-50 flex items-center justify-between">
          <h2 className="text-lg font-semibold">申请详情</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        </div>

        {/* 内容 */}
        <div className="px-6 py-4 space-y-3 max-h-[70vh] overflow-y-auto">
          {/* 基本信息 - 紧凑横向布局 */}
          <div className="grid grid-cols-4 gap-x-4 gap-y-2">
            <div>
              <label className="text-xs font-medium text-gray-500">申请号</label>
              <p className="text-sm text-gray-900 font-medium">{item.prNumber || "-"}</p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">状态</label>
              <p className="mt-0.5">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    STATUS_COLORS[statusCode] || "bg-gray-100"
                  }`}
                >
                  {item.status || STATUS_MAP[statusCode] || statusCode}
                </span>
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">发起人</label>
              <p className="text-sm text-gray-900">{item.owner_name || "-"}</p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">紧急程度</label>
              <p className="mt-0.5">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    URGENCY_COLORS[item.urgency] || "bg-gray-100"
                  }`}
                >
                  {item.urgency || "-"}
                </span>
              </p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">创建时间</label>
              <p className="text-sm text-gray-700">{formatTime(item.created_at)}</p>
            </div>
            {item.owner_department && (
              <div className="col-span-2">
                <label className="text-xs font-medium text-gray-500">申请部门</label>
                <p className="text-sm text-gray-900">{item.owner_department}</p>
              </div>
            )}
            {item.updated_at && (
              <div>
                <label className="text-xs font-medium text-gray-500">更新时间</label>
                <p className="text-sm text-gray-700">{formatTime(item.updated_at)}</p>
              </div>
            )}
          </div>

          {/* 标题和描述 - 合并为一个区域 */}
          <div className="border-t pt-2">
            <div className="mb-2">
              <label className="text-xs font-medium text-gray-500">标题</label>
              <p className="text-sm text-gray-900 font-medium">{item.title || "-"}</p>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-500">描述</label>
              <p className="text-sm text-gray-700">{item.description || "-"}</p>
            </div>
          </div>

          {/* 驳回原因（如有） */}
          {item.reject_reason && (
            <div className="p-3 bg-red-50 border border-red-200 rounded">
              <label className="text-sm font-medium text-red-700 block mb-1">整体驳回原因</label>
              <p className="text-sm text-red-700">{item.reject_reason}</p>
            </div>
          )}

          {/* 物料列表 - 紧凑表格式布局 */}
          {item.items && item.items.length > 0 ? (
            <div className="border-t pt-2">
              <label className="text-xs font-medium text-gray-500 block mb-2">
                采购物料明细（共 {item.items.length} 项）
              </label>
              <div className="space-y-2">
                {item.items.map((it, idx) => (
                  <div key={idx} className="p-2 border rounded bg-gray-50">
                    {/* 第一行：物料名称、规格、状态 */}
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-sm font-medium text-gray-900 min-w-[30px]">{idx + 1}.</span>
                      <span className="text-sm font-medium text-gray-900">{it.name || "-"}</span>
                      {it.spec && (
                        <span className="text-xs text-gray-600">规格: {it.spec}</span>
                      )}
                      <span className={`ml-auto px-2 py-0.5 rounded text-xs font-medium ${
                        it.status_code === 'approved' ? 'bg-green-100 text-green-700' :
                        it.status_code === 'rejected' ? 'bg-red-100 text-red-700' :
                        'bg-yellow-100 text-yellow-700'
                      }`}>
                        {it.status || it.status_code || "-"}
                      </span>
                    </div>

                    {/* 第二行：数量、分类、备注 - 横向排列 */}
                    <div className="flex items-center gap-4 text-xs text-gray-600 ml-[42px]">
                      <span>
                        <span className="text-gray-500">数量:</span>
                        <span className="font-medium text-gray-900 ml-1">{it.qty || 0} {it.unit || "件"}</span>
                      </span>
                      {it.classification && (
                        <span>
                          <span className="text-gray-500">分类:</span>
                          <span className="text-gray-700 ml-1">{it.classification}</span>
                        </span>
                      )}
                      {it.remark && (
                        <span className="flex-1">
                          <span className="text-gray-500">备注:</span>
                          <span className="text-gray-700 ml-1">{it.remark}</span>
                        </span>
                      )}
                    </div>

                    {/* 驳回原因（如有）*/}
                    {it.reject_reason && (
                      <div className="mt-1 ml-[42px] p-1.5 bg-red-50 border border-red-200 rounded text-xs">
                        <span className="text-red-700 font-medium">驳回原因：</span>
                        <span className="text-red-700">{it.reject_reason}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
              暂无物料明细信息
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="px-6 py-4 border-t bg-gray-50 flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 border rounded text-sm hover:bg-gray-100 transition"
          >
            关闭
          </button>
          {canApprove && statusCode === "submitted" && (
            <>
              <button
                onClick={() => onReject(item.id)}
                className="px-4 py-2 bg-red-50 border border-red-200 text-red-700 rounded text-sm hover:bg-red-100 transition"
              >
                驳回
              </button>
              <button
                onClick={() => onApprove(item.id)}
                className="px-4 py-2 bg-green-50 border border-green-200 text-green-700 rounded text-sm hover:bg-green-100 transition"
              >
                批准
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}