// pages/FillPricePage.jsx
// 员工填写价格页面 - 增强版，支持历史记录查看和溯源

import React, { useState, useEffect, useMemo } from "react";
import { useAuth } from "../auth/AuthContext";
import api from "../api";

export default function FillPricePage() {
  const { user } = useAuth();
  const [prs, setPrs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPr, setSelectedPr] = useState(null);
  const [itemPrices, setItemPrices] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [canViewAll, setCanViewAll] = useState(false);

  // 视图模式：need_price（待填价）或 history（历史记录）
  const [viewMode, setViewMode] = useState("need_price");

  // 筛选状态
  const [searchText, setSearchText] = useState("");
  const [urgencyFilter, setUrgencyFilter] = useState("all");
  const [ownerFilter, setOwnerFilter] = useState("all");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [showFilters, setShowFilters] = useState(false);
  const [sortBy, setSortBy] = useState("urgency");

  // 部门列表（从API获取）
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    fetchData();
  }, [viewMode]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      if (viewMode === "need_price") {
        // 获取待填价的申请
        const response = await api.get("/api/v1/pr/need-price");
        const data = response.data || response;
        setPrs(data.data || data || []);
        setCanViewAll(data.can_view_all || false);
        // 从数据中提取部门
        const depts = new Set();
        (data.data || data || []).forEach(pr => {
          if (pr.owner_department) depts.add(pr.owner_department);
        });
        setDepartments(Array.from(depts).sort());
      } else {
        // 获取历史记录
        const params = new URLSearchParams();
        if (statusFilter !== "all") params.append("status", statusFilter);
        if (dateFrom) params.append("date_from", dateFrom);
        if (dateTo) params.append("date_to", dateTo);

        const response = await api.get(`/api/v1/pr/price-history?${params.toString()}`);
        const data = response.data || response;
        setPrs(data.data || []);
        setCanViewAll(data.can_view_all || false);
        if (data.departments) {
          setDepartments(data.departments);
        }
      }
    } catch (err) {
      console.error("Failed to fetch PRs:", err);
      setError("获取数据失败");
    } finally {
      setLoading(false);
    }
  };

  // 筛选后的PR列表
  const filteredPrs = useMemo(() => {
    let result = prs.filter(pr => {
      // 搜索筛选
      if (searchText) {
        const search = searchText.toLowerCase();
        const matchTitle = pr.title?.toLowerCase().includes(search);
        const matchPrNumber = pr.prNumber?.toLowerCase().includes(search);
        const matchOwner = pr.owner_name?.toLowerCase().includes(search);
        const matchMaterial = pr.items?.some(item =>
          item.name?.toLowerCase().includes(search) ||
          item.spec?.toLowerCase().includes(search)
        );
        if (!matchTitle && !matchPrNumber && !matchOwner && !matchMaterial) {
          return false;
        }
      }

      // 紧急程度筛选
      if (urgencyFilter !== "all" && pr.urgency_code !== urgencyFilter) {
        return false;
      }

      // 所有者筛选
      if (ownerFilter === "mine" && !pr.is_own) {
        return false;
      }
      if (ownerFilter === "others" && pr.is_own) {
        return false;
      }

      // 部门筛选
      if (departmentFilter !== "all" && pr.owner_department !== departmentFilter) {
        return false;
      }

      return true;
    });

    // 排序
    const urgencyOrder = { high: 0, medium: 1, low: 2 };
    result.sort((a, b) => {
      switch (sortBy) {
        case "urgency":
          return (urgencyOrder[a.urgency_code] || 2) - (urgencyOrder[b.urgency_code] || 2);
        case "date":
          return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        case "amount":
          return (b.total_amount || 0) - (a.total_amount || 0);
        default:
          return 0;
      }
    });

    return result;
  }, [prs, searchText, urgencyFilter, ownerFilter, departmentFilter, sortBy]);

  // 统计数据
  const stats = useMemo(() => {
    const needPrice = prs.filter(pr => pr.status_code === "supervisor_approved").length;
    const priceFilled = prs.filter(pr => pr.status_code === "price_filled").length;
    const approved = prs.filter(pr => pr.status_code === "approved").length;
    const highUrgency = prs.filter(pr => pr.urgency_code === "high").length;
    const mine = prs.filter(pr => pr.is_own).length;

    return {
      total: prs.length,
      filtered: filteredPrs.length,
      needPrice,
      priceFilled,
      approved,
      highUrgency,
      mine,
    };
  }, [prs, filteredPrs]);

  // 清除筛选
  const clearFilters = () => {
    setSearchText("");
    setUrgencyFilter("all");
    setOwnerFilter("all");
    setDepartmentFilter("all");
    setStatusFilter("all");
    setDateFrom("");
    setDateTo("");
  };

  const hasActiveFilters = searchText || urgencyFilter !== "all" || ownerFilter !== "all" ||
    departmentFilter !== "all" || statusFilter !== "all" || dateFrom || dateTo;

  const handleSelectPr = (pr) => {
    setSelectedPr(pr);
    const prices = {};
    pr.items.forEach((item) => {
      prices[item.id] = item.unit_price || "";
    });
    setItemPrices(prices);
    setError(null);
  };

  const handlePriceChange = (itemId, value) => {
    setItemPrices((prev) => ({
      ...prev,
      [itemId]: value,
    }));
  };

  const handleSubmitPrices = async () => {
    if (!selectedPr) return;

    const missingPrices = selectedPr.items.filter(
      (item) => !itemPrices[item.id] || parseFloat(itemPrices[item.id]) <= 0
    );
    if (missingPrices.length > 0) {
      setError(`请为所有物料填写价格（${missingPrices.length}项未填写）`);
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      const items = selectedPr.items.map((item) => ({
        id: item.id,
        unit_price: parseFloat(itemPrices[item.id]),
      }));

      const response = await api.post(`/api/v1/pr/${selectedPr.id}/fill-price`, {
        items,
      });

      alert(`价格提交成功！总金额: ¥${response.data.total_amount?.toFixed(2) || 0}`);
      setSelectedPr(null);
      setItemPrices({});
      fetchData();
    } catch (err) {
      console.error("Failed to submit prices:", err);
      setError(err.response?.data?.error || "提交价格失败");
    } finally {
      setSubmitting(false);
    }
  };

  const calculateTotal = () => {
    if (!selectedPr) return 0;
    return selectedPr.items.reduce((sum, item) => {
      const price = parseFloat(itemPrices[item.id]) || 0;
      return sum + price * (item.qty || 1);
    }, 0);
  };

  // 格式化日期
  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    const date = new Date(dateStr);
    return date.toLocaleDateString("zh-CN");
  };

  // 获取状态样式
  const getStatusStyle = (statusCode) => {
    const styles = {
      supervisor_approved: "bg-yellow-100 text-yellow-700",
      price_filled: "bg-blue-100 text-blue-700",
      pending_super_admin: "bg-purple-100 text-purple-700",
      approved: "bg-green-100 text-green-700",
      rejected: "bg-red-100 text-red-700",
    };
    return styles[statusCode] || "bg-gray-100 text-gray-600";
  };

  if (loading) {
    return (
      <div className="p-6 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-2 text-gray-600">加载中...</p>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto">
      {/* 页面标题和视图切换 */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold">填写价格</h1>
          <p className="text-sm text-gray-500 mt-1">
            {viewMode === "need_price" ? "待填写价格的采购申请" : "查看填价历史和已处理的申请"}
          </p>
        </div>

        {/* 视图模式切换 */}
        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => { setViewMode("need_price"); clearFilters(); }}
            className={`px-4 py-2 text-sm font-medium rounded-md transition ${
              viewMode === "need_price"
                ? "bg-white text-blue-600 shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            待填价
            {stats.needPrice > 0 && viewMode !== "need_price" && (
              <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-red-500 text-white rounded-full">
                {stats.needPrice}
              </span>
            )}
          </button>
          <button
            onClick={() => { setViewMode("history"); clearFilters(); }}
            className={`px-4 py-2 text-sm font-medium rounded-md transition ${
              viewMode === "history"
                ? "bg-white text-blue-600 shadow"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            历史记录
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      {viewMode === "history" && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div
            className={`p-3 rounded-lg cursor-pointer transition ${
              statusFilter === "all" ? "bg-blue-50 border-2 border-blue-300" : "bg-white border border-gray-200"
            }`}
            onClick={() => setStatusFilter("all")}
          >
            <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
            <div className="text-xs text-gray-500">全部记录</div>
          </div>
          <div
            className={`p-3 rounded-lg cursor-pointer transition ${
              statusFilter === "need_price" ? "bg-yellow-50 border-2 border-yellow-300" : "bg-white border border-gray-200"
            }`}
            onClick={() => setStatusFilter("need_price")}
          >
            <div className="text-2xl font-bold text-yellow-600">{stats.needPrice}</div>
            <div className="text-xs text-gray-500">待填价</div>
          </div>
          <div
            className={`p-3 rounded-lg cursor-pointer transition ${
              statusFilter === "pending" ? "bg-blue-50 border-2 border-blue-300" : "bg-white border border-gray-200"
            }`}
            onClick={() => setStatusFilter("pending")}
          >
            <div className="text-2xl font-bold text-blue-600">{stats.priceFilled}</div>
            <div className="text-xs text-gray-500">待审批</div>
          </div>
          <div
            className={`p-3 rounded-lg cursor-pointer transition ${
              statusFilter === "approved" ? "bg-green-50 border-2 border-green-300" : "bg-white border border-gray-200"
            }`}
            onClick={() => setStatusFilter("approved")}
          >
            <div className="text-2xl font-bold text-green-600">{stats.approved}</div>
            <div className="text-xs text-gray-500">已批准</div>
          </div>
        </div>
      )}

      {/* 筛选区域 */}
      <div className="bg-white rounded-lg shadow p-3 sm:p-4 mb-4">
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="搜索单号、标题、申请人、物料..."
              className="w-full pl-9 pr-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-3 py-2 border rounded-lg text-sm font-medium flex items-center gap-1.5 ${
                showFilters || hasActiveFilters ? "bg-blue-50 border-blue-300 text-blue-700" : "bg-white text-gray-600"
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              筛选
              {hasActiveFilters && (
                <span className="w-5 h-5 bg-blue-600 text-white text-xs rounded-full flex items-center justify-center">!</span>
              )}
            </button>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
              >
                清除
              </button>
            )}
            <button
              onClick={fetchData}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
            >
              刷新
            </button>
          </div>
        </div>

        {/* 展开的筛选选项 */}
        {showFilters && (
          <div className="mt-3 pt-3 border-t">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {/* 紧急程度 */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">紧急程度</label>
                <select
                  value={urgencyFilter}
                  onChange={(e) => setUrgencyFilter(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">全部</option>
                  <option value="high">紧急</option>
                  <option value="medium">一般</option>
                  <option value="low">不急</option>
                </select>
              </div>

              {/* 申请来源 */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">申请来源</label>
                <select
                  value={ownerFilter}
                  onChange={(e) => setOwnerFilter(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">全部申请</option>
                  <option value="mine">我的申请 ({stats.mine})</option>
                  <option value="others">他人申请</option>
                </select>
              </div>

              {/* 部门 */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">申请部门</label>
                <select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">全部部门</option>
                  {departments.map(dept => (
                    <option key={dept} value={dept}>{dept}</option>
                  ))}
                </select>
              </div>

              {/* 排序 */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">排序方式</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                >
                  <option value="urgency">按紧急程度</option>
                  <option value="date">按申请时间</option>
                  <option value="amount">按金额</option>
                </select>
              </div>
            </div>

            {/* 历史模式下的额外筛选 */}
            {viewMode === "history" && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">状态</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => { setStatusFilter(e.target.value); fetchData(); }}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">全部状态</option>
                    <option value="need_price">待填价</option>
                    <option value="price_filled">已填价待审批</option>
                    <option value="approved">已批准</option>
                    <option value="rejected">已拒绝</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">开始日期</label>
                  <input
                    type="date"
                    value={dateFrom}
                    onChange={(e) => setDateFrom(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">结束日期</label>
                  <input
                    type="date"
                    value={dateTo}
                    onChange={(e) => setDateTo(e.target.value)}
                    className="w-full px-3 py-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* 筛选结果统计 */}
        {hasActiveFilters && (
          <div className="mt-3 text-sm text-gray-500">
            显示 {stats.filtered} / {stats.total} 条记录
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: PR List */}
        <div className="bg-white rounded-lg shadow p-3 sm:p-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3 sm:mb-4">
            <h2 className="text-base sm:text-lg font-semibold">
              {viewMode === "need_price" ? "待填价申请" : "历史记录"}
              ({filteredPrs.length}{hasActiveFilters ? ` / ${stats.total}` : ""})
            </h2>
            {viewMode === "need_price" && (
              <div className="flex gap-1.5 flex-wrap">
                <button
                  onClick={() => setUrgencyFilter(urgencyFilter === "high" ? "all" : "high")}
                  className={`text-xs px-2 py-1 rounded-full border transition ${
                    urgencyFilter === "high"
                      ? "bg-red-100 border-red-300 text-red-700"
                      : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50"
                  }`}
                >
                  🔥 紧急 ({prs.filter(p => p.urgency_code === "high").length})
                </button>
                <button
                  onClick={() => setOwnerFilter(ownerFilter === "mine" ? "all" : "mine")}
                  className={`text-xs px-2 py-1 rounded-full border transition ${
                    ownerFilter === "mine"
                      ? "bg-blue-100 border-blue-300 text-blue-700"
                      : "bg-white border-gray-200 text-gray-500 hover:bg-gray-50"
                  }`}
                >
                  👤 我的 ({stats.mine})
                </button>
              </div>
            )}
          </div>

          {filteredPrs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">
                {hasActiveFilters
                  ? "没有符合筛选条件的申请"
                  : viewMode === "need_price"
                  ? "暂无待填价的申请"
                  : "暂无历史记录"}
              </p>
              {hasActiveFilters && (
                <button onClick={clearFilters} className="mt-2 text-blue-600 text-sm hover:underline">
                  清除筛选条件
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-2 sm:space-y-3 max-h-[500px] sm:max-h-[600px] overflow-y-auto">
              {filteredPrs.map((pr) => (
                <div
                  key={pr.id}
                  className={`p-2.5 sm:p-3 border rounded cursor-pointer transition hover:bg-blue-50 ${
                    selectedPr?.id === pr.id ? "border-blue-500 bg-blue-50" : "border-gray-200"
                  }`}
                  onClick={() => handleSelectPr(pr)}
                >
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                        <span className="font-medium text-sm sm:text-base truncate">{pr.title}</span>
                        {pr.is_own && (
                          <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded shrink-0">我的</span>
                        )}
                        {viewMode === "history" && (
                          <span className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${getStatusStyle(pr.status_code)}`}>
                            {pr.status}
                          </span>
                        )}
                      </div>
                      <div className="text-xs sm:text-sm text-gray-500 mt-0.5">
                        单号: {pr.prNumber}
                      </div>
                      <div className="text-xs sm:text-sm text-gray-500">
                        申请人: {pr.owner_name || "未知"}
                        {pr.owner_department && ` (${pr.owner_department})`}
                      </div>
                      <div className="flex items-center gap-3 text-xs sm:text-sm text-gray-500">
                        <span>物料: {pr.items_count}项</span>
                        {pr.total_amount && (
                          <span className="text-blue-600">¥{pr.total_amount.toFixed(2)}</span>
                        )}
                        <span>{formatDate(pr.created_at)}</span>
                      </div>
                    </div>
                    <span
                      className={`text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded whitespace-nowrap shrink-0 ${
                        pr.urgency_code === "high"
                          ? "bg-red-100 text-red-700"
                          : pr.urgency_code === "medium"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {pr.urgency}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right: Detail / Price Entry Form */}
        <div className="bg-white rounded-lg shadow p-3 sm:p-4">
          <h2 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">
            {viewMode === "need_price" ? "填写物料价格" : "申请详情"}
          </h2>

          {!selectedPr ? (
            <p className="text-gray-500 text-center py-8">请选择一个申请</p>
          ) : (
            <div>
              <div className="mb-3 sm:mb-4 p-2.5 sm:p-3 bg-gray-50 rounded">
                <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                  <span className="font-medium text-sm sm:text-base">{selectedPr.title}</span>
                  {selectedPr.is_own && (
                    <span className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded">我的申请</span>
                  )}
                  <span className={`text-xs px-1.5 py-0.5 rounded ${getStatusStyle(selectedPr.status_code)}`}>
                    {selectedPr.status || (viewMode === "need_price" ? "待填价" : "")}
                  </span>
                </div>
                <div className="text-xs sm:text-sm text-gray-500 mt-0.5">
                  单号: {selectedPr.prNumber}
                </div>
                <div className="text-xs sm:text-sm text-gray-500">
                  申请人: {selectedPr.owner_name || "未知"}
                  {selectedPr.owner_department && ` (${selectedPr.owner_department})`}
                </div>
                <div className="text-xs sm:text-sm text-gray-500">
                  申请时间: {formatDate(selectedPr.created_at)}
                </div>
              </div>

              <div className="space-y-3 sm:space-y-4 max-h-72 sm:max-h-96 overflow-y-auto">
                {selectedPr.items.map((item, idx) => (
                  <div key={item.id} className="p-2.5 sm:p-3 border border-gray-200 rounded">
                    <div className="flex justify-between mb-1.5 sm:mb-2 gap-2">
                      <span className="font-medium text-sm sm:text-base">
                        {idx + 1}. {item.name}
                      </span>
                      <span className="text-xs sm:text-sm text-gray-500 shrink-0">
                        {item.qty} {item.unit || "个"}
                      </span>
                    </div>
                    {item.spec && (
                      <div className="text-xs sm:text-sm text-gray-500 mb-1.5 sm:mb-2">
                        规格: {item.spec}
                      </div>
                    )}
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                      <div className="flex items-center gap-2 flex-1">
                        <label className="text-xs sm:text-sm text-gray-600 shrink-0">单价:</label>
                        {viewMode === "need_price" && selectedPr.status_code === "supervisor_approved" ? (
                          <div className="relative flex-1">
                            <span className="absolute left-2 sm:left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">¥</span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={itemPrices[item.id] || ""}
                              onChange={(e) => handlePriceChange(item.id, e.target.value)}
                              className="w-full pl-6 sm:pl-8 pr-2 sm:pr-3 py-1.5 sm:py-2 border rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm sm:text-base"
                              placeholder="请输入单价"
                            />
                          </div>
                        ) : (
                          <span className="text-blue-600 font-medium">
                            ¥{item.unit_price?.toFixed(2) || "-"}
                          </span>
                        )}
                      </div>
                      <span className="text-xs sm:text-sm text-gray-500 text-right sm:whitespace-nowrap">
                        小计: ¥
                        {viewMode === "need_price" && selectedPr.status_code === "supervisor_approved"
                          ? ((parseFloat(itemPrices[item.id]) || 0) * (item.qty || 1)).toFixed(2)
                          : ((item.unit_price || 0) * (item.qty || 1)).toFixed(2)
                        }
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-3 sm:mt-4 pt-3 sm:pt-4 border-t">
                <div className="flex justify-between items-center mb-3 sm:mb-4">
                  <span className="font-semibold text-sm sm:text-base">总金额:</span>
                  <span className="text-lg sm:text-xl font-bold text-blue-600">
                    ¥{viewMode === "need_price" && selectedPr.status_code === "supervisor_approved"
                      ? calculateTotal().toFixed(2)
                      : (selectedPr.total_amount || 0).toFixed(2)
                    }
                  </span>
                </div>

                {viewMode === "need_price" && selectedPr.status_code === "supervisor_approved" && (
                  <button
                    onClick={handleSubmitPrices}
                    disabled={submitting}
                    className="w-full bg-blue-600 text-white py-2.5 sm:py-3 rounded font-medium text-sm sm:text-base hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {submitting ? "提交中..." : "提交价格"}
                  </button>
                )}

                {viewMode === "history" && selectedPr.status_code !== "supervisor_approved" && (
                  <div className="text-center text-sm text-gray-500">
                    此申请已{selectedPr.status}，仅供查看
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
