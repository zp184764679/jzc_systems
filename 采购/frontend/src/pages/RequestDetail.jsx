// src/pages/RequestDetail.jsx
// 物料申请单详情页面
import React, { useEffect, useState } from 'react';
import { formatDate, formatSimpleCurrency, formatNumber } from "../utils/formatters";
import { useParams, useNavigate } from 'react-router-dom';
import { api } from "../api/http";
import { ENDPOINTS } from "../api/endpoints";

// 状态配置
const STATUS_CONFIG = {
  pending: { label: "待审批", color: "bg-yellow-100 text-yellow-700 border-yellow-300", icon: "⏳" },
  approved: { label: "已批准", color: "bg-green-100 text-green-700 border-green-300", icon: "✓" },
  rejected: { label: "已拒绝", color: "bg-red-100 text-red-700 border-red-300", icon: "✗" },
  cancelled: { label: "已取消", color: "bg-gray-100 text-gray-700 border-gray-300", icon: "⊘" },
  in_progress: { label: "处理中", color: "bg-blue-100 text-blue-700 border-blue-300", icon: "⚙" },
};

// 紧急度配置
const URGENCY_CONFIG = {
  low: { label: "低", color: "text-gray-600", bg: "bg-gray-100" },
  normal: { label: "正常", color: "text-blue-600", bg: "bg-blue-100" },
  high: { label: "高", color: "text-orange-600", bg: "bg-orange-100" },
  urgent: { label: "紧急", color: "text-red-600", bg: "bg-red-100" },
};

export default function RequestDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchRequest = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.get(ENDPOINTS.PR.GET_DETAIL(id));
        setRequest(data);
      } catch (error) {
        console.error("Error fetching request details:", error);
        setError(error.message || "加载失败，请稍后重试");
      } finally {
        setLoading(false);
      }
    };

    fetchRequest();
  }, [id]);

  // 格式化日期

  // 信息行组件
  const InfoRow = ({ label, value, important = false }) => (
    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start py-2 sm:py-2.5 border-b border-gray-100 last:border-0">
      <span className="text-gray-600 font-medium text-sm sm:text-base sm:min-w-[120px] mb-0.5 sm:mb-0">{label}</span>
      <span className={`text-sm sm:text-base sm:text-right sm:flex-1 ${important ? 'font-bold text-gray-900' : 'text-gray-700'}`}>
        {value !== null && value !== undefined && value !== "" ? value : <span className="text-gray-400">-</span>}
      </span>
    </div>
  );

  // 加载状态
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 text-center">
          <div className="text-red-600 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-red-900 mb-2">加载失败</h2>
          <p className="text-red-700 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
          >
            返回上一页
          </button>
        </div>
      </div>
    );
  }

  if (!request) {
    return (
      <div className="max-w-7xl mx-auto p-6 text-center text-gray-500">
        未找到申请单信息
      </div>
    );
  }

  const statusInfo = STATUS_CONFIG[request.status] || { label: request.status, color: "bg-gray-100 text-gray-700", icon: "?" };
  const urgencyInfo = URGENCY_CONFIG[request.urgency] || URGENCY_CONFIG.normal;

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
      {/* 面包屑导航 */}
      <div className="flex items-center gap-2 text-xs sm:text-sm text-gray-600">
        <button
          onClick={() => navigate('/')}
          className="hover:text-blue-600 transition"
        >
          首页
        </button>
        <span>/</span>
        <span className="text-gray-900 font-medium">申请单详情</span>
      </div>

      {/* 页面标题和操作按钮 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-2 sm:gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-lg transition shrink-0"
            title="返回"
          >
            <svg className="w-5 h-5 sm:w-6 sm:h-6 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-gray-900">物料申请单详情</h1>
            <p className="text-gray-500 text-sm sm:text-base mt-0.5 sm:mt-1">PR# {request.prNumber || request.id}</p>
          </div>
        </div>

        {/* 操作按钮区域 */}
        <div className="flex gap-2 sm:gap-3 ml-8 sm:ml-0">
          {request.status === 'pending' && (
            <button
              onClick={() => {/* TODO: 实现撤回功能 */}}
              className="px-3 sm:px-4 py-1.5 sm:py-2 border-2 border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition font-medium text-sm sm:text-base"
            >
              撤回申请
            </button>
          )}
          <button
            onClick={() => {/* TODO: 实现导出功能 */}}
            className="px-3 sm:px-4 py-1.5 sm:py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium flex items-center gap-1.5 sm:gap-2 text-sm sm:text-base"
          >
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            导出
          </button>
        </div>
      </div>

      {/* 状态卡片 */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl sm:rounded-2xl p-4 sm:p-6 text-white shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
          <div className="flex items-center gap-2 sm:gap-4 flex-wrap">
            <div className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-sm sm:text-lg font-bold ${statusInfo.color} flex items-center gap-1.5 sm:gap-2`}>
              <span>{statusInfo.icon}</span>
              {statusInfo.label}
            </div>
            {request.urgency && (
              <div className={`px-2.5 sm:px-3 py-1 rounded-full ${urgencyInfo.bg} ${urgencyInfo.color} font-semibold text-xs sm:text-sm`}>
                紧急度: {urgencyInfo.label}
              </div>
            )}
          </div>
          <div className="text-left sm:text-right">
            <div className="text-blue-100 text-xs sm:text-sm">创建时间</div>
            <div className="text-base sm:text-lg font-semibold">{formatDate(request.createdAt || request.created_at)}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        {/* 左侧列 - 基本信息 */}
        <div className="lg:col-span-2 space-y-4 sm:space-y-6">
          {/* 基本信息卡片 */}
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6 border border-gray-200">
            <h3 className="font-bold text-gray-900 text-base sm:text-lg mb-3 sm:mb-4 flex items-center gap-2">
              <span className="text-xl sm:text-2xl">📋</span>
              基本信息
            </h3>
            <div className="space-y-1">
              <InfoRow label="申请单号" value={request.prNumber || `PR-${request.id}`} important />
              <InfoRow label="申请标题" value={request.title || request.name} important />
              <InfoRow label="申请人" value={request.requester_name || request.username} />
              <InfoRow label="部门" value={request.department} />
              <InfoRow label="用途说明" value={request.purpose || request.description} />
              <InfoRow label="预算代码" value={request.budget_code} />
              <InfoRow label="成本中心" value={request.cost_center} />
            </div>
          </div>

          {/* 物料清单卡片 */}
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6 border border-gray-200">
            <h3 className="font-bold text-gray-900 text-base sm:text-lg mb-3 sm:mb-4 flex items-center gap-2">
              <span className="text-xl sm:text-2xl">📦</span>
              物料清单
            </h3>

            {request.items && request.items.length > 0 ? (
              <>
                {/* 桌面端表格视图 */}
                <div className="hidden sm:block overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="bg-gray-50 border-b-2 border-gray-200">
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">序号</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">物料名称</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">规格型号</th>
                        <th className="text-right py-3 px-4 font-semibold text-gray-700">数量</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">单位</th>
                        <th className="text-right py-3 px-4 font-semibold text-gray-700">预估单价</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700">备注</th>
                      </tr>
                    </thead>
                    <tbody>
                      {request.items.map((item, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition">
                          <td className="py-3 px-4 text-gray-600">{index + 1}</td>
                          <td className="py-3 px-4 font-medium text-gray-900">{item.name || item.material_name}</td>
                          <td className="py-3 px-4 text-gray-600">{item.specification || item.spec || "-"}</td>
                          <td className="py-3 px-4 text-right font-semibold text-gray-900">{item.quantity || item.qty}</td>
                          <td className="py-3 px-4 text-gray-600">{item.unit || "件"}</td>
                          <td className="py-3 px-4 text-right text-gray-900">
                            {item.estimated_price ? `¥${parseFloat(item.estimated_price).toLocaleString()}` : "-"}
                          </td>
                          <td className="py-3 px-4 text-gray-600 text-sm">{item.remark || item.notes || "-"}</td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot>
                      <tr className="bg-gray-50 font-bold">
                        <td colSpan="3" className="py-3 px-4 text-right">合计:</td>
                        <td className="py-3 px-4 text-right text-blue-600">
                          {request.items.reduce((sum, item) => sum + (parseFloat(item.quantity || item.qty) || 0), 0)}
                        </td>
                        <td className="py-3 px-4"></td>
                        <td className="py-3 px-4 text-right text-blue-600">
                          ¥{request.items.reduce((sum, item) =>
                            sum + ((parseFloat(item.estimated_price) || 0) * (parseFloat(item.quantity || item.qty) || 0)), 0
                          ).toLocaleString()}
                        </td>
                        <td className="py-3 px-4"></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>

                {/* 移动端卡片视图 */}
                <div className="sm:hidden space-y-3">
                  {request.items.map((item, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                      <div className="flex justify-between items-start mb-2">
                        <span className="font-medium text-gray-900">
                          {index + 1}. {item.name || item.material_name}
                        </span>
                      </div>
                      {(item.specification || item.spec) && (
                        <div className="text-xs text-gray-500 mb-2">规格: {item.specification || item.spec}</div>
                      )}
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">
                          数量: {item.quantity || item.qty} {item.unit || "件"}
                        </span>
                        <span className="font-medium text-gray-900">
                          {item.estimated_price ? `¥${parseFloat(item.estimated_price).toLocaleString()}` : "-"}
                        </span>
                      </div>
                      {(item.remark || item.notes) && (
                        <div className="text-xs text-gray-500 mt-1.5 pt-1.5 border-t border-gray-200">
                          备注: {item.remark || item.notes}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* 移动端合计 */}
                  <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                    <div className="flex justify-between items-center text-sm">
                      <span className="font-medium text-gray-700">合计数量:</span>
                      <span className="font-bold text-blue-600">
                        {request.items.reduce((sum, item) => sum + (parseFloat(item.quantity || item.qty) || 0), 0)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-sm mt-1">
                      <span className="font-medium text-gray-700">合计金额:</span>
                      <span className="font-bold text-blue-600">
                        ¥{request.items.reduce((sum, item) =>
                          sum + ((parseFloat(item.estimated_price) || 0) * (parseFloat(item.quantity || item.qty) || 0)), 0
                        ).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              // 单个物料的简单显示
              <div className="bg-gray-50 rounded-lg p-3 sm:p-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-4">
                  <InfoRow label="物料名称" value={request.name} />
                  <InfoRow label="数量" value={request.qty} />
                  <InfoRow label="单位" value={request.unit || "件"} />
                  <InfoRow label="规格" value={request.specification} />
                </div>
              </div>
            )}
          </div>

          {/* 附件卡片 */}
          {request.attachments && request.attachments.length > 0 && (
            <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6 border border-gray-200">
              <h3 className="font-bold text-gray-900 text-base sm:text-lg mb-3 sm:mb-4 flex items-center gap-2">
                <span className="text-xl sm:text-2xl">📎</span>
                附件 ({request.attachments.length})
              </h3>
              <div className="space-y-2">
                {request.attachments.map((attachment, index) => (
                  <a
                    key={index}
                    href={attachment.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 sm:gap-3 p-2.5 sm:p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                  >
                    <svg className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900 text-sm sm:text-base truncate">{attachment.name}</div>
                      <div className="text-xs sm:text-sm text-gray-500">{attachment.size}</div>
                    </div>
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 右侧列 - 审批流程时间轴 */}
        <div className="space-y-4 sm:space-y-6">
          <div className="bg-white rounded-xl shadow-lg p-4 sm:p-6 border border-gray-200">
            <h3 className="font-bold text-gray-900 text-base sm:text-lg mb-3 sm:mb-4 flex items-center gap-2">
              <span className="text-xl sm:text-2xl">⏱️</span>
              审批流程
            </h3>

            {request.approval_history && request.approval_history.length > 0 ? (
              <div className="space-y-3 sm:space-y-4">
                {request.approval_history.map((step, index) => {
                  const isLast = index === request.approval_history.length - 1;
                  const isPending = step.status === 'pending';
                  const isApproved = step.status === 'approved';
                  const isRejected = step.status === 'rejected';

                  return (
                    <div key={index} className="flex gap-2 sm:gap-3">
                      {/* 时间轴线 */}
                      <div className="flex flex-col items-center">
                        <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-sm sm:text-lg font-bold ${
                          isApproved ? 'bg-green-100 text-green-600' :
                          isRejected ? 'bg-red-100 text-red-600' :
                          isPending ? 'bg-yellow-100 text-yellow-600' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {isApproved ? '✓' : isRejected ? '✗' : isPending ? '⏳' : index + 1}
                        </div>
                        {!isLast && (
                          <div className={`w-0.5 flex-1 min-h-[32px] sm:min-h-[40px] ${
                            isApproved ? 'bg-green-200' : 'bg-gray-200'
                          }`}></div>
                        )}
                      </div>

                      {/* 内容 */}
                      <div className="flex-1 pb-4 sm:pb-6">
                        <div className="font-semibold text-gray-900 text-sm sm:text-base">{step.approver_name || step.level}</div>
                        <div className="text-xs sm:text-sm text-gray-500">{step.role || step.position}</div>
                        {step.comment && (
                          <div className="mt-1.5 sm:mt-2 p-1.5 sm:p-2 bg-gray-50 rounded text-xs sm:text-sm text-gray-700 italic">
                            "{step.comment}"
                          </div>
                        )}
                        <div className="mt-1 text-xs text-gray-400">
                          {formatDate(step.timestamp || step.updated_at)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              // 默认流程展示
              <div className="space-y-3 sm:space-y-4">
                <div className="flex gap-2 sm:gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-sm sm:text-lg font-bold bg-green-100 text-green-600">
                      ✓
                    </div>
                    <div className="w-0.5 flex-1 min-h-[32px] sm:min-h-[40px] bg-gray-200"></div>
                  </div>
                  <div className="flex-1 pb-4 sm:pb-6">
                    <div className="font-semibold text-gray-900 text-sm sm:text-base">提交申请</div>
                    <div className="text-xs sm:text-sm text-gray-500">{request.requester_name || request.username}</div>
                    <div className="mt-1 text-xs text-gray-400">
                      {formatDate(request.createdAt || request.created_at)}
                    </div>
                  </div>
                </div>

                <div className="flex gap-2 sm:gap-3">
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded-full flex items-center justify-center text-sm sm:text-lg font-bold ${
                      request.status === 'approved' ? 'bg-green-100 text-green-600' :
                      request.status === 'rejected' ? 'bg-red-100 text-red-600' :
                      'bg-yellow-100 text-yellow-600'
                    }`}>
                      {request.status === 'approved' ? '✓' : request.status === 'rejected' ? '✗' : '⏳'}
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="font-semibold text-gray-900 text-sm sm:text-base">
                      {request.status === 'approved' ? '审批通过' :
                       request.status === 'rejected' ? '审批驳回' : '待审批'}
                    </div>
                    <div className="text-xs sm:text-sm text-gray-500">
                      {request.approver_name || '审批人'}
                    </div>
                    {request.status === 'pending' && (
                      <div className="mt-2 text-xs text-yellow-600 bg-yellow-50 p-2 rounded">
                        等待审批中...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 其他信息卡片 */}
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-4 sm:p-6 border-2 border-blue-200">
            <h3 className="font-bold text-gray-900 text-base sm:text-lg mb-3 sm:mb-4 flex items-center gap-2">
              <span className="text-xl sm:text-2xl">ℹ️</span>
              其他信息
            </h3>
            <div className="space-y-1">
              <InfoRow label="更新时间" value={formatDate(request.updatedAt || request.updated_at)} />
              <InfoRow label="申请单ID" value={request.id} />
              {request.reject_reason && (
                <div className="mt-2 sm:mt-3 p-2.5 sm:p-3 bg-red-50 border-2 border-red-200 rounded-lg">
                  <div className="font-semibold text-red-900 text-sm sm:text-base mb-1">驳回原因:</div>
                  <div className="text-red-700 text-xs sm:text-sm">{request.reject_reason}</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
