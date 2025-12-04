import { useEffect, useState } from "react";
import { api } from "../api/http";
import { useAuth } from "../auth/AuthContext";
import StatisticsCard from "../components/ApprovalCenter/StatisticsCard";
import FilterBar from "../components/ApprovalCenter/FilterBar";
import DetailModal from "../components/ApprovalCenter/DetailModal";
import RejectReasonModal from "../components/ApprovalCenter/RejectReasonModal";
import RequestTable from "../components/ApprovalCenter/RequestTable";
import RequestCard from "../components/ApprovalCenter/RequestCard";
import { useApprovalList } from "../hooks/useApprovalList";
import { ENDPOINTS } from "../api/endpoints";

/**
 * ApprovalCenter - 审批中心主组件
 * 
 * 普通员工：
 * - 待我审批：所有待审批的申请，可以批准/驳回
 * - 我发起的：自己的所有申请，只能查看详情
 * 
 * 管理员：
 * - 待我审批：所有待审批的申请，可以批准/驳回
 * - 我发起的：自己的所有申请，只能查看详情
 * - 全部申请：所有申请，可以批准/驳回（针对待审批的）
 */
export default function ApprovalCenter() {
  const { user } = useAuth();
  const {
    todoList,
    mineList,
    allList,
    stats,
    loading,
    error,
    setError,
    isAdmin,
    loadInitial,
    applyFilters,
  } = useApprovalList(user?.id, user?.role);

  // UI 状态
  const [tab, setTab] = useState("todo"); // "todo" | "mine" | "all"
  const [filters, setFilters] = useState({
    searchText: "",
    statusCodes: [],
    urgencyCodes: [],
  });
  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [rejectReasonOpen, setRejectReasonOpen] = useState(false);
  const [rejectTargetId, setRejectTargetId] = useState(null);
  const [rejectIsLoading, setRejectIsLoading] = useState(false);

  // 初始化加载数据
  useEffect(() => {
    if (user?.id) {
      loadInitial();
    }
  }, [user?.id, loadInitial]);

  // 计算当前展示的列表（应用筛选）
  let sourceList = [];
  if (tab === "todo") {
    sourceList = todoList;
  } else if (tab === "mine") {
    sourceList = mineList;
  } else if (tab === "all" && isAdmin) {
    sourceList = allList;
  }

  const filteredList = applyFilters(sourceList, filters);

  // 打开详情弹窗
  const openDetail = async (id) => {
    setDetailLoading(true);
    setDetail(null);
    try {
      const data = await api.get(ENDPOINTS.PR.GET_DETAIL(id));
      setDetail(data);  // API直接返回数据，不需要.data
    } catch (e) {
      const msg = e?.message || "获取详情失败";
      setDetail({ error: msg });
    } finally {
      setDetailLoading(false);
    }
    setDetailOpen(true);
  };

  // 执行审批操作（批准/驳回）
  const act = async (id, action, reason = null) => {
    try {
      const url =
        action === "approve"
          ? ENDPOINTS.PR.APPROVE(id)
          : ENDPOINTS.PR.REJECT(id);

      const payload = reason ? { reason } : {};
      
      await api.post(url, payload);

      // 关闭弹窗
      setDetailOpen(false);
      setRejectReasonOpen(false);
      setRejectTargetId(null);

      // 刷新数据
      await loadInitial();
      setError("");
    } catch (e) {
      const msg = e?.response?.data?.message || e?.message || "操作失败";
      setError(msg);
    }
  };

  // 打开驳回弹窗
  const openRejectModal = (id) => {
    setRejectTargetId(id);
    setRejectReasonOpen(true);
  };

  // 处理驳回确认
  const handleRejectConfirm = (reason) => {
    setRejectIsLoading(true);
    act(rejectTargetId, "reject", reason).finally(() => {
      setRejectIsLoading(false);
    });
  };

  // 判断是否为移动设备
  const isMobile = typeof window !== "undefined" && window.innerWidth < 768;

  // 判断当前Tab是否应该显示批准/驳回操作
  // 只有管理员才能批准/拒绝申请
  const showApprovalActions = (tab === "todo" || tab === "all") && isAdmin;

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-4">
      {/* 页面标题 */}
      <h1 className="text-xl md:text-2xl font-bold">审批中心</h1>

      {/* 错误提示 */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-sm rounded">
          {error}
        </div>
      )}

      {/* 统计卡片 */}
      <StatisticsCard
        stats={stats}
        onStatusClick={(statusCode) => {
          // 点击统计卡片时的行为：
          // 1. 如果是管理员且有"全部申请"Tab，跳到"全部申请"
          // 2. 否则跳到"待我审批"Tab
          const targetTab = isAdmin ? "all" : "todo";
          setTab(targetTab);
          setFilters({ searchText: "", statusCodes: [statusCode], urgencyCodes: [] });
        }}
      />

      {/* 标签页 */}
      <div className="flex flex-wrap gap-2">
        <button
          className={`px-3 py-2 sm:px-4 sm:py-2 border rounded text-xs sm:text-sm font-medium transition ${
            tab === "todo"
              ? "bg-black text-white border-black"
              : "bg-white text-gray-700 border-gray-300 hover:border-gray-400"
          }`}
          onClick={() => {
            setTab("todo");
            setFilters({ searchText: "", statusCodes: [], urgencyCodes: [] });
          }}
          disabled={loading}
        >
          待我审批
        </button>
        <button
          className={`px-4 py-2 border rounded text-sm font-medium transition ${
            tab === "mine"
              ? "bg-black text-white border-black"
              : "bg-white text-gray-700 border-gray-300 hover:border-gray-400"
          }`}
          onClick={() => {
            setTab("mine");
            setFilters({ searchText: "", statusCodes: [], urgencyCodes: [] });
          }}
          disabled={loading}
        >
          我发起的
        </button>

        {/* 仅管理员显示"全部申请"Tab */}
        {isAdmin && (
          <button
            className={`px-4 py-2 border rounded text-sm font-medium transition ${
              tab === "all"
                ? "bg-black text-white border-black"
                : "bg-white text-gray-700 border-gray-300 hover:border-gray-400"
            }`}
            onClick={() => {
              setTab("all");
              setFilters({ searchText: "", statusCodes: [], urgencyCodes: [] });
            }}
            disabled={loading}
          >
            全部申请
          </button>
        )}
      </div>

      {/* 筛选条 */}
      <FilterBar filters={filters} onFilterChange={setFilters} />

      {/* 列表展示 */}
      {isMobile ? (
        <RequestCard
          loading={loading}
          list={filteredList}
          emptyMessage={
            sourceList.length === 0
              ? "暂无数据"
              : "没有符合筛选条件的数据"
          }
          onRowClick={openDetail}
          onApprove={(id) => act(id, "approve")}
          onReject={openRejectModal}
          showTodoActions={showApprovalActions}
        />
      ) : (
        <RequestTable
          loading={loading}
          list={filteredList}
          emptyMessage={
            sourceList.length === 0
              ? "暂无数据"
              : "没有符合筛选条件的数据"
          }
          onRowClick={openDetail}
          onApprove={(id) => act(id, "approve")}
          onReject={openRejectModal}
          showTodoActions={showApprovalActions}
        />
      )}

      {/* 详情弹窗 */}
      <DetailModal
        isOpen={detailOpen}
        item={detail}
        isLoading={detailLoading}
        onClose={() => setDetailOpen(false)}
        onApprove={(id) => act(id, "approve")}
        onReject={(id) => openRejectModal(id)}
        canApprove={showApprovalActions}
      />

      {/* 驳回原因弹窗 */}
      <RejectReasonModal
        isOpen={rejectReasonOpen}
        isLoading={rejectIsLoading}
        onConfirm={handleRejectConfirm}
        onCancel={() => {
          setRejectReasonOpen(false);
          setRejectTargetId(null);
        }}
      />
    </div>
  );
}