// pages/AdminApprovalCenter.jsx
// 厂长/总经理审批中心 - PR价格审批（增强版：支持历史记录查询和筛选）
//
// 角色说明：
// - factory_manager (厂长): 审批填写完价格的PR
// - general_manager (总经理): 审批超额PR（金额>2000或价格偏差>5%）
// - super_admin (超级管理员): 最高权限

import React, { useState, useEffect, useMemo } from "react";
import { useAuth } from "../auth/AuthContext";
import api from "../api";

export default function AdminApprovalCenter() {
  const { user, isAdmin, isSuperAdmin, isFactoryManager, isGeneralManager } = useAuth();

  // 视图模式：pending（待审批）/ history（历史记录）
  const [viewMode, setViewMode] = useState("pending");

  // 待审批数据
  const [adminPRs, setAdminPRs] = useState([]);
  const [superAdminPRs, setSuperAdminPRs] = useState([]);

  // 历史记录数据
  const [historyData, setHistoryData] = useState([]);
  const [historyStats, setHistoryStats] = useState({});
  const [departments, setDepartments] = useState([]);
  const [owners, setOwners] = useState([]);

  // 筛选条件
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [urgencyFilter, setUrgencyFilter] = useState("all");
  const [departmentFilter, setDepartmentFilter] = useState("");
  const [ownerFilter, setOwnerFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [amountMin, setAmountMin] = useState("");
  const [amountMax, setAmountMax] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // UI状态
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [selectedPR, setSelectedPR] = useState(null);
  const [prDetails, setPrDetails] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectModal, setShowRejectModal] = useState(false);

  useEffect(() => {
    if (viewMode === "pending") {
      fetchPRs();
    } else {
      fetchHistory();
    }
  }, [viewMode]);

  // 当筛选条件变化时重新获取历史数据
  useEffect(() => {
    if (viewMode === "history") {
      fetchHistory();
    }
  }, [statusFilter, urgencyFilter, departmentFilter, ownerFilter, dateFrom, dateTo, amountMin, amountMax]);

  const fetchPRs = async () => {
    try {
      setLoading(true);
      setError("");

      const adminResponse = await api.get("/api/v1/pr/need-admin-approve");
      setAdminPRs(adminResponse.data || []);

      const superAdminResponse = await api.get("/api/v1/pr/need-super-admin-approve");
      setSuperAdminPRs(superAdminResponse.data || []);
    } catch (err) {
      console.error("Failed to fetch PRs:", err);
      setError("获取待审批列表失败");
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      setLoading(true);
      setError("");

      const params = new URLSearchParams();
      if (statusFilter !== "all") params.append("status", statusFilter);
      if (urgencyFilter !== "all") params.append("urgency", urgencyFilter);
      if (departmentFilter) params.append("department", departmentFilter);
      if (ownerFilter) params.append("owner_id", ownerFilter);
      if (dateFrom) params.append("date_from", dateFrom);
      if (dateTo) params.append("date_to", dateTo);
      if (amountMin) params.append("amount_min", amountMin);
      if (amountMax) params.append("amount_max", amountMax);
      if (searchText) params.append("search", searchText);

      const response = await api.get(`/api/v1/pr/approval-history?${params.toString()}`);
      setHistoryData(response.data.data || []);
      setHistoryStats(response.data.stats || {});
      setDepartments(response.data.departments || []);
      setOwners(response.data.owners || []);
    } catch (err) {
      console.error("Failed to fetch history:", err);
      setError("获取历史记录失败");
    } finally {
      setLoading(false);
    }
  };

  // 搜索处理（带防抖）
  const handleSearch = () => {
    if (viewMode === "history") {
      fetchHistory();
    }
  };

  const fetchPRDetails = async (prId) => {
    try {
      const response = await api.get(`/api/v1/pr/requests/${prId}`);
      setPrDetails(response.data);
    } catch (err) {
      console.error("Failed to fetch PR details:", err);
    }
  };

  const handleSelectPR = async (pr) => {
    setSelectedPR(pr);
    await fetchPRDetails(pr.id);
  };

  const handleAdminApprove = async () => {
    if (!selectedPR) return;
    if (!window.confirm("确定审批通过吗？")) return;

    try {
      setError("");
      const response = await api.post(`/api/v1/pr/${selectedPR.id}/admin-approve`);

      if (response.data.auto_approved) {
        setSuccess(`PR#${selectedPR.prNumber} 已自动完成（${response.data.auto_approve_reason}）`);
      } else {
        setSuccess(`PR#${selectedPR.prNumber} 需要超管审批（${response.data.need_super_admin_reason}）`);
      }

      setSelectedPR(null);
      setPrDetails(null);
      fetchPRs();

      setTimeout(() => setSuccess(""), 5000);
    } catch (err) {
      console.error("Admin approve failed:", err);
      setError(err.response?.data?.error || "审批失败");
    }
  };

  const handleSuperAdminApprove = async () => {
    if (!selectedPR) return;
    if (!window.confirm("确定最终审批通过吗？")) return;

    try {
      setError("");
      const response = await api.post(`/api/v1/pr/${selectedPR.id}/super-admin-approve`);

      setSuccess(`PR#${selectedPR.prNumber} 超管审批完成`);
      setSelectedPR(null);
      setPrDetails(null);
      fetchPRs();

      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Super admin approve failed:", err);
      setError(err.response?.data?.error || "审批失败");
    }
  };

  const handleReject = async () => {
    if (!selectedPR) return;
    if (!rejectReason.trim()) {
      setError("请填写驳回原因");
      return;
    }

    try {
      setError("");
      await api.post(`/api/v1/pr/${selectedPR.id}/reject`, {
        reason: rejectReason,
      });

      setSuccess(`PR#${selectedPR.prNumber} 已驳回`);
      setSelectedPR(null);
      setPrDetails(null);
      setRejectReason("");
      setShowRejectModal(false);
      fetchPRs();

      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      console.error("Reject failed:", err);
      setError(err.response?.data?.error || "驳回失败");
    }
  };

  const formatCurrency = (amount) => {
    return `¥${parseFloat(amount || 0).toFixed(2)}`;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("zh-CN");
  };

  // 重置筛选条件
  const resetFilters = () => {
    setSearchText("");
    setStatusFilter("all");
    setUrgencyFilter("all");
    setDepartmentFilter("");
    setOwnerFilter("");
    setDateFrom("");
    setDateTo("");
    setAmountMin("");
    setAmountMax("");
  };

  // 过滤后的历史数据（前端搜索）
  const filteredHistoryData = useMemo(() => {
    if (!searchText) return historyData;
    const search = searchText.toLowerCase();
    return historyData.filter(pr =>
      pr.prNumber?.toLowerCase().includes(search) ||
      pr.title?.toLowerCase().includes(search) ||
      pr.owner_name?.toLowerCase().includes(search) ||
      pr.items?.some(item =>
        item.name?.toLowerCase().includes(search) ||
        item.spec?.toLowerCase().includes(search)
      )
    );
  }, [historyData, searchText]);

  // 状态样式
  const getStatusStyle = (statusCode) => {
    const styles = {
      price_filled: "bg-blue-100 text-blue-700",
      pending_super_admin: "bg-orange-100 text-orange-700",
      approved: "bg-green-100 text-green-700",
      rejected: "bg-red-100 text-red-700",
    };
    return styles[statusCode] || "bg-gray-100 text-gray-700";
  };

  // 紧急程度样式
  const getUrgencyStyle = (urgencyCode) => {
    const styles = {
      urgent: "bg-red-100 text-red-600",
      high: "bg-orange-100 text-orange-600",
      normal: "bg-gray-100 text-gray-600",
      low: "bg-green-100 text-green-600",
    };
    return styles[urgencyCode] || "bg-gray-100 text-gray-600";
  };

  if (loading && viewMode === "pending" && adminPRs.length === 0 && superAdminPRs.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 max-w-7xl mx-auto">
      {/* 标题和视图切换 */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 gap-3">
        <h1 className="text-xl sm:text-2xl font-bold">审批中心</h1>

        {/* 视图切换标签 */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-sm font-medium transition ${
              viewMode === "pending"
                ? "bg-white text-blue-600 shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
            onClick={() => setViewMode("pending")}
          >
            待审批
            {(adminPRs.length + superAdminPRs.length) > 0 && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                {adminPRs.length + superAdminPRs.length}
              </span>
            )}
          </button>
          <button
            className={`px-3 sm:px-4 py-1.5 sm:py-2 rounded-md text-sm font-medium transition ${
              viewMode === "history"
                ? "bg-white text-blue-600 shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
            onClick={() => setViewMode("history")}
          >
            历史记录
          </button>
        </div>
      </div>

      {/* 消息提示 */}
      {success && (
        <div className="mb-4 p-3 bg-green-100 text-green-700 rounded">
          {success}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
      )}

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
        <div
          className={`rounded-lg p-3 sm:p-4 border cursor-pointer transition hover:shadow-md ${
            viewMode === "pending" || statusFilter === "price_filled"
              ? "bg-blue-50 border-blue-300"
              : "bg-blue-50/50 border-blue-200"
          }`}
          onClick={() => {
            if (viewMode === "history") setStatusFilter(statusFilter === "price_filled" ? "all" : "price_filled");
          }}
        >
          <div className="text-xs sm:text-sm text-blue-600 mb-0.5 sm:mb-1">待厂长审批</div>
          <div className="text-xl sm:text-2xl font-bold text-blue-700">
            {viewMode === "pending" ? adminPRs.length : (historyStats.price_filled || 0)}
          </div>
        </div>
        <div
          className={`rounded-lg p-3 sm:p-4 border cursor-pointer transition hover:shadow-md ${
            statusFilter === "pending_super_admin"
              ? "bg-orange-50 border-orange-300"
              : "bg-orange-50/50 border-orange-200"
          }`}
          onClick={() => {
            if (viewMode === "history") setStatusFilter(statusFilter === "pending_super_admin" ? "all" : "pending_super_admin");
          }}
        >
          <div className="text-xs sm:text-sm text-orange-600 mb-0.5 sm:mb-1">待总经理审批</div>
          <div className="text-xl sm:text-2xl font-bold text-orange-700">
            {viewMode === "pending" ? superAdminPRs.length : (historyStats.pending_super_admin || 0)}
          </div>
        </div>
        <div
          className={`rounded-lg p-3 sm:p-4 border cursor-pointer transition hover:shadow-md ${
            statusFilter === "approved"
              ? "bg-green-50 border-green-300"
              : "bg-green-50/50 border-green-200"
          }`}
          onClick={() => {
            if (viewMode === "history") setStatusFilter(statusFilter === "approved" ? "all" : "approved");
          }}
        >
          <div className="text-xs sm:text-sm text-green-600 mb-0.5 sm:mb-1">已批准</div>
          <div className="text-xl sm:text-2xl font-bold text-green-700">
            {historyStats.approved || 0}
          </div>
        </div>
        <div
          className={`rounded-lg p-3 sm:p-4 border cursor-pointer transition hover:shadow-md ${
            statusFilter === "rejected"
              ? "bg-red-50 border-red-300"
              : "bg-red-50/50 border-red-200"
          }`}
          onClick={() => {
            if (viewMode === "history") setStatusFilter(statusFilter === "rejected" ? "all" : "rejected");
          }}
        >
          <div className="text-xs sm:text-sm text-red-600 mb-0.5 sm:mb-1">已驳回</div>
          <div className="text-xl sm:text-2xl font-bold text-red-700">
            {historyStats.rejected || 0}
          </div>
        </div>
      </div>

      {/* 待审批视图 */}
      {viewMode === "pending" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {/* Left: PR Lists */}
          <div className="space-y-4 sm:space-y-6">
            {/* Factory manager approval list - 厂长审批列表 */}
            {(isFactoryManager() || isSuperAdmin()) && (
              <div className="bg-white rounded-lg shadow p-3 sm:p-4">
                <h2 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-blue-700">
                  待厂长审批 ({adminPRs.length})
                </h2>
                {adminPRs.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">暂无待审批</p>
                ) : (
                  <div className="space-y-2 max-h-48 sm:max-h-64 overflow-y-auto">
                    {adminPRs.map((pr) => (
                      <div
                        key={pr.id}
                        className={`p-2.5 sm:p-3 border rounded cursor-pointer transition hover:bg-blue-50 ${
                          selectedPR?.id === pr.id
                            ? "border-blue-500 bg-blue-50"
                            : "border-gray-200"
                        }`}
                        onClick={() => handleSelectPR(pr)}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <span className="font-medium text-sm sm:text-base truncate">{pr.title}</span>
                          <span className="text-blue-600 font-semibold text-sm sm:text-base shrink-0">
                            {formatCurrency(pr.total_amount)}
                          </span>
                        </div>
                        <div className="text-xs sm:text-sm text-gray-500 mt-0.5">
                          单号: {pr.prNumber} | 申请人: {pr.owner_name}
                        </div>
                        {pr.urgency_code && pr.urgency_code !== 'normal' && (
                          <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded ${getUrgencyStyle(pr.urgency_code)}`}>
                            {pr.urgency}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* General manager approval list - 总经理审批列表 */}
            {(isGeneralManager() || isSuperAdmin()) && (
              <div className="bg-white rounded-lg shadow p-3 sm:p-4">
                <h2 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-orange-700">
                  待总经理审批 ({superAdminPRs.length})
                </h2>
                {superAdminPRs.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">暂无待审批</p>
                ) : (
                  <div className="space-y-2 max-h-48 sm:max-h-64 overflow-y-auto">
                    {superAdminPRs.map((pr) => (
                      <div
                        key={pr.id}
                        className={`p-2.5 sm:p-3 border rounded cursor-pointer transition hover:bg-orange-50 ${
                          selectedPR?.id === pr.id
                            ? "border-orange-500 bg-orange-50"
                            : "border-gray-200"
                        }`}
                        onClick={() => handleSelectPR(pr)}
                      >
                        <div className="flex justify-between items-start gap-2">
                          <span className="font-medium text-sm sm:text-base truncate">{pr.title}</span>
                          <span className="text-orange-600 font-semibold text-sm sm:text-base shrink-0">
                            {formatCurrency(pr.total_amount)}
                          </span>
                        </div>
                        <div className="text-xs sm:text-sm text-gray-500 mt-0.5">
                          单号: {pr.prNumber} | 申请人: {pr.owner_name}
                        </div>
                        {pr.urgency_code && pr.urgency_code !== 'normal' && (
                          <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded ${getUrgencyStyle(pr.urgency_code)}`}>
                            {pr.urgency}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right: PR Details */}
          <div className="bg-white rounded-lg shadow p-3 sm:p-4">
            <h2 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">申请详情</h2>
            {!selectedPR || !prDetails ? (
              <p className="text-gray-500 text-center py-8">请选择一个申请查看详情</p>
            ) : (
              <div>
                <div className="mb-3 sm:mb-4 p-2.5 sm:p-3 bg-gray-50 rounded">
                  <div className="font-medium text-base sm:text-lg">{prDetails.title}</div>
                  <div className="text-xs sm:text-sm text-gray-500">单号: {prDetails.prNumber}</div>
                  <div className="text-xs sm:text-sm text-gray-500">
                    申请人: {prDetails.owner_name} ({prDetails.owner_department})
                  </div>
                  <div className="text-xs sm:text-sm text-gray-500">
                    状态: {prDetails.status}
                  </div>
                </div>

                {/* Items */}
                <div className="mb-3 sm:mb-4">
                  <h3 className="font-medium text-sm sm:text-base mb-2">物料清单</h3>
                  <div className="space-y-2 max-h-48 sm:max-h-60 overflow-y-auto">
                    {prDetails.items.map((item, idx) => (
                      <div key={item.id} className="p-2 border rounded text-xs sm:text-sm">
                        <div className="flex justify-between gap-2">
                          <span className="truncate">
                            {idx + 1}. {item.name}
                          </span>
                          <span className="font-medium shrink-0">
                            {formatCurrency(item.total_price)}
                          </span>
                        </div>
                        {item.spec && (
                          <div className="text-gray-500 truncate">规格: {item.spec}</div>
                        )}
                        <div className="text-gray-500">
                          数量: {item.qty} {item.unit} × 单价: {formatCurrency(item.unit_price)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Total */}
                <div className="p-2.5 sm:p-3 bg-blue-50 rounded mb-3 sm:mb-4">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-sm sm:text-base">总金额:</span>
                    <span className="text-lg sm:text-xl font-bold text-blue-600">
                      {formatCurrency(prDetails.total_amount)}
                    </span>
                  </div>
                  {prDetails.total_amount > 2000 && (
                    <div className="text-xs sm:text-sm text-orange-600 mt-1">
                      金额 &gt; ¥2000，需要超管审批
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
                  {prDetails.status_code === "price_filled" && (isFactoryManager() || isSuperAdmin()) && (
                    <button
                      onClick={handleAdminApprove}
                      className="flex-1 bg-blue-600 text-white py-2 rounded text-sm sm:text-base hover:bg-blue-700"
                    >
                      厂长审批通过
                    </button>
                  )}
                  {prDetails.status_code === "pending_super_admin" && (isGeneralManager() || isSuperAdmin()) && (
                    <button
                      onClick={handleSuperAdminApprove}
                      className="flex-1 bg-green-600 text-white py-2 rounded text-sm sm:text-base hover:bg-green-700"
                    >
                      总经理审批通过
                    </button>
                  )}
                  <button
                    onClick={() => setShowRejectModal(true)}
                    className="px-4 py-2 bg-red-100 text-red-600 rounded text-sm sm:text-base hover:bg-red-200"
                  >
                    驳回
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 历史记录视图 */}
      {viewMode === "history" && (
        <div className="bg-white rounded-lg shadow">
          {/* 筛选栏 */}
          <div className="p-3 sm:p-4 border-b">
            {/* 搜索框 */}
            <div className="flex flex-col sm:flex-row gap-3 mb-3">
              <div className="flex-1 flex gap-2">
                <input
                  type="text"
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="搜索单号、标题、申请人、物料..."
                  className="flex-1 px-3 py-2 border rounded text-sm"
                />
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  搜索
                </button>
              </div>
              <button
                onClick={() => setShowFilters(!showFilters)}
                className={`px-3 py-2 border rounded text-sm ${showFilters ? "bg-blue-50 border-blue-300" : ""}`}
              >
                {showFilters ? "收起筛选" : "展开筛选"}
              </button>
            </div>

            {/* 展开的筛选器 */}
            {showFilters && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 border-t">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">状态</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  >
                    <option value="all">全部状态</option>
                    <option value="price_filled">待厂长审批</option>
                    <option value="pending_super_admin">待总经理审批</option>
                    <option value="pending">所有待审批</option>
                    <option value="approved">已批准</option>
                    <option value="rejected">已驳回</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">紧急程度</label>
                  <select
                    value={urgencyFilter}
                    onChange={(e) => setUrgencyFilter(e.target.value)}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  >
                    <option value="all">全部</option>
                    <option value="urgent">紧急</option>
                    <option value="high">高</option>
                    <option value="normal">普通</option>
                    <option value="low">低</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">部门</label>
                  <select
                    value={departmentFilter}
                    onChange={(e) => setDepartmentFilter(e.target.value)}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  >
                    <option value="">全部部门</option>
                    {departments.map((dept) => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">申请人</label>
                  <select
                    value={ownerFilter}
                    onChange={(e) => setOwnerFilter(e.target.value)}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  >
                    <option value="">全部申请人</option>
                    {owners.map((owner) => (
                      <option key={owner.id} value={owner.id}>{owner.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">开始日期</label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">结束日期</label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">最小金额</label>
                  <input
                    type="number"
                    value={amountMin}
                    onChange={(e) => setAmountMin(e.target.value)}
                    placeholder="0"
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">最大金额</label>
                  <input
                    type="number"
                    value={amountMax}
                    onChange={(e) => setAmountMax(e.target.value)}
                    placeholder="不限"
                    className="w-full px-2 py-1.5 border rounded text-sm"
                  />
                </div>
                <div className="col-span-2 sm:col-span-4 flex justify-end">
                  <button
                    onClick={resetFilters}
                    className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900"
                  >
                    重置筛选
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* 历史记录列表 */}
          <div className="divide-y">
            {loading ? (
              <div className="p-8 text-center text-gray-500">加载中...</div>
            ) : filteredHistoryData.length === 0 ? (
              <div className="p-8 text-center text-gray-500">暂无数据</div>
            ) : (
              filteredHistoryData.map((pr) => (
                <div
                  key={pr.id}
                  className="p-3 sm:p-4 hover:bg-gray-50 cursor-pointer transition"
                  onClick={() => handleSelectPR(pr)}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium truncate">{pr.title}</span>
                        <span className={`px-2 py-0.5 text-xs rounded ${getStatusStyle(pr.status_code)}`}>
                          {pr.status}
                        </span>
                        {pr.urgency_code && pr.urgency_code !== 'normal' && (
                          <span className={`px-2 py-0.5 text-xs rounded ${getUrgencyStyle(pr.urgency_code)}`}>
                            {pr.urgency}
                          </span>
                        )}
                      </div>
                      <div className="text-xs sm:text-sm text-gray-500 mt-1">
                        <span>单号: {pr.prNumber}</span>
                        <span className="mx-2">|</span>
                        <span>申请人: {pr.owner_name}</span>
                        {pr.owner_department && (
                          <>
                            <span className="mx-2">|</span>
                            <span>{pr.owner_department}</span>
                          </>
                        )}
                      </div>
                      {pr.reject_reason && (
                        <div className="text-xs text-red-500 mt-1">
                          驳回原因: {pr.reject_reason}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-4 shrink-0">
                      <div className="text-right">
                        <div className="text-lg font-semibold text-blue-600">
                          {formatCurrency(pr.total_amount)}
                        </div>
                        <div className="text-xs text-gray-400">
                          {formatDate(pr.created_at)}
                        </div>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* 分页信息 */}
          {filteredHistoryData.length > 0 && (
            <div className="p-3 border-t text-sm text-gray-500 text-center">
              共 {filteredHistoryData.length} 条记录
            </div>
          )}
        </div>
      )}

      {/* 详情弹窗（历史记录模式） */}
      {viewMode === "history" && selectedPR && prDetails && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 border-b flex justify-between items-center sticky top-0 bg-white">
              <h3 className="text-lg font-semibold">申请详情</h3>
              <button
                onClick={() => {
                  setSelectedPR(null);
                  setPrDetails(null);
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-4">
              <div className="mb-4 p-3 bg-gray-50 rounded">
                <div className="font-medium text-lg">{prDetails.title}</div>
                <div className="text-sm text-gray-500">单号: {prDetails.prNumber}</div>
                <div className="text-sm text-gray-500">
                  申请人: {prDetails.owner_name} ({prDetails.owner_department})
                </div>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`px-2 py-0.5 text-xs rounded ${getStatusStyle(prDetails.status_code)}`}>
                    {prDetails.status}
                  </span>
                  {prDetails.urgency_code && prDetails.urgency_code !== 'normal' && (
                    <span className={`px-2 py-0.5 text-xs rounded ${getUrgencyStyle(prDetails.urgency_code)}`}>
                      {prDetails.urgency}
                    </span>
                  )}
                </div>
                {prDetails.reject_reason && (
                  <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                    驳回原因: {prDetails.reject_reason}
                  </div>
                )}
              </div>

              <div className="mb-4">
                <h3 className="font-medium mb-2">物料清单</h3>
                <div className="space-y-2 max-h-60 overflow-y-auto">
                  {prDetails.items.map((item, idx) => (
                    <div key={item.id} className="p-2 border rounded text-sm">
                      <div className="flex justify-between gap-2">
                        <span className="truncate">
                          {idx + 1}. {item.name}
                        </span>
                        <span className="font-medium shrink-0">
                          {formatCurrency(item.total_price)}
                        </span>
                      </div>
                      {item.spec && (
                        <div className="text-gray-500 truncate">规格: {item.spec}</div>
                      )}
                      <div className="text-gray-500">
                        数量: {item.qty} {item.unit} × 单价: {formatCurrency(item.unit_price)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3 bg-blue-50 rounded">
                <div className="flex justify-between items-center">
                  <span className="font-medium">总金额:</span>
                  <span className="text-xl font-bold text-blue-600">
                    {formatCurrency(prDetails.total_amount)}
                  </span>
                </div>
              </div>
            </div>
            <div className="p-4 border-t">
              <button
                onClick={() => {
                  setSelectedPR(null);
                  setPrDetails(null);
                }}
                className="w-full py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Modal */}
      {showRejectModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-4 sm:p-6 w-full max-w-md">
            <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">驳回申请</h3>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="请输入驳回原因..."
              className="w-full p-2.5 sm:p-3 border rounded mb-3 sm:mb-4 h-28 sm:h-32 text-sm sm:text-base"
            />
            <div className="flex gap-2 sm:gap-3">
              <button
                onClick={handleReject}
                className="flex-1 bg-red-600 text-white py-2 rounded text-sm sm:text-base hover:bg-red-700"
              >
                确认驳回
              </button>
              <button
                onClick={() => {
                  setShowRejectModal(false);
                  setRejectReason("");
                }}
                className="flex-1 bg-gray-200 text-gray-700 py-2 rounded text-sm sm:text-base hover:bg-gray-300"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
