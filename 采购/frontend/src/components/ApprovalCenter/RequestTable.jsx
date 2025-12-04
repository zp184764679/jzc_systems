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
  high: "高",
  medium: "中",
  low: "低",
};

const URGENCY_COLORS = {
  high: "bg-red-100 text-red-700",
  medium: "bg-yellow-100 text-yellow-700",
  low: "bg-blue-100 text-blue-700",
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
 * RequestTable - 请求表格视图（桌面版）
 */
export default function RequestTable({
  loading,
  list,
  emptyMessage,
  onRowClick,
  onApprove,
  onReject,
  showTodoActions = false,
}) {
  return (
    <div className="overflow-x-auto bg-white rounded border">
      {loading ? (
        <div className="p-6 text-gray-500 text-center">加载中...</div>
      ) : (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left border-b bg-gray-50">
              <th className="px-3 py-2 font-medium text-gray-600">申请号</th>
              <th className="px-3 py-2 font-medium text-gray-600">标题</th>
              <th className="px-3 py-2 font-medium text-gray-600">发起人</th>
              <th className="px-3 py-2 font-medium text-gray-600">紧急程度</th>
              <th className="px-3 py-2 font-medium text-gray-600">状态</th>
              <th className="px-3 py-2 font-medium text-gray-600">创建时间</th>
              <th className="px-3 py-2 font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {list.length ? (
              list.map((item) => {
                const statusCode = item.status_code || "draft";
                const urgencyCode = item.urgency || "medium";
                return (
                  <tr key={item.id} className="border-b hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium">{item.prNumber}</td>
                    <td className="px-3 py-2 cursor-pointer hover:text-blue-600" onClick={() => onRowClick(item.id)}>
                      {item.title}
                    </td>
                    <td className="px-3 py-2">{item.owner_name || "-"}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          URGENCY_COLORS[urgencyCode] || "bg-gray-100"
                        }`}
                      >
                        {item.urgency || URGENCY_MAP[urgencyCode] || urgencyCode}
                      </span>
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          STATUS_COLORS[statusCode] || "bg-gray-100"
                        }`}
                      >
                        {item.status || STATUS_MAP[statusCode] || statusCode}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-gray-600">{formatTime(item.created_at)}</td>
                    <td className="px-3 py-2 space-x-1">
                      <button
                        onClick={() => onRowClick(item.id)}
                        className="px-2 py-1 text-xs border rounded hover:bg-gray-100 transition"
                      >
                        详情
                      </button>
                      {showTodoActions && statusCode === "submitted" && (
                        <>
                          <button
                            onClick={() => onApprove(item.id)}
                            className="px-2 py-1 text-xs bg-green-50 border border-green-200 text-green-700 rounded hover:bg-green-100 transition"
                          >
                            批准
                          </button>
                          <button
                            onClick={() => onReject(item.id)}
                            className="px-2 py-1 text-xs bg-red-50 border border-red-200 text-red-700 rounded hover:bg-red-100 transition"
                          >
                            驳回
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-gray-500">
                  {emptyMessage || "暂无数据"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}