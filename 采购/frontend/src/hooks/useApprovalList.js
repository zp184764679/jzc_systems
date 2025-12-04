import { useState, useCallback } from "react";
import { api } from "../api/http";
import { ENDPOINTS } from "../api/endpoints";

/**
 * useApprovalList Hook
 * 处理审批列表的数据获取、筛选、统计
 */
export function useApprovalList(userId, userRole) {
  const [todoList, setTodoList] = useState([]);
  const [mineList, setMineList] = useState([]);
  const [allList, setAllList] = useState([]);
  
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // 检查是否为管理员
  const isAdmin = userRole === "admin" || userRole === "super_admin";

  // 加载待审批列表
  const loadTodoList = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.get(ENDPOINTS.PR.GET_TODO);
      const list = Array.isArray(data) ? data : data?.data || [];
      setTodoList(list);
      return list;
    } catch (err) {
      const errMsg = err?.response?.data?.message || err?.message || "加载待审批列表失败";
      setError(errMsg);
      setTodoList([]);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // 加载我发起的列表
  const loadMineList = useCallback(async () => {
    if (!userId) return [];
    setLoading(true);
    setError("");
    try {
      const data = await api.get(ENDPOINTS.PR.GET_MINE(userId));
      const list = Array.isArray(data) ? data : data?.data || [];
      setMineList(list);
      return list;
    } catch (err) {
      const errMsg = err?.response?.data?.message || err?.message || "加载我的申请列表失败";
      setError(errMsg);
      setMineList([]);
      return [];
    } finally {
      setLoading(false);
    }
  }, [userId]);

  // 加载所有申请（管理员）
  const loadAllList = useCallback(async () => {
    if (!isAdmin) return [];
    setLoading(true);
    setError("");
    try {
      const data = await api.get(ENDPOINTS.PR.GET_ALL());
      const list = Array.isArray(data) ? data : data?.data || [];
      setAllList(list);
      return list;
    } catch (err) {
      const errMsg = err?.response?.data?.message || err?.message || "加载全部申请列表失败";
      setError(errMsg);
      setAllList([]);
      return [];
    } finally {
      setLoading(false);
    }
  }, [userId, isAdmin]);

  // 初始化加载数据
  const loadInitial = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      let todoData = [];
      let mineData = [];
      let allData = [];

      if (isAdmin) {
        // 管理员加载所有数据
        const results = await Promise.all([
          api.get(ENDPOINTS.PR.GET_TODO).catch(() => []),
          userId ? api.get(ENDPOINTS.PR.GET_MINE(userId)).catch(() => []) : [],
          api.get(ENDPOINTS.PR.GET_ALL()).catch(() => []),
        ]);
        todoData = Array.isArray(results[0]) ? results[0] : results[0]?.data || [];
        mineData = Array.isArray(results[1]) ? results[1] : results[1]?.data || [];
        allData = Array.isArray(results[2]) ? results[2] : results[2]?.data || [];
      } else {
        // 普通员工只加载自己的和待审批的
        const results = await Promise.all([
          api.get(ENDPOINTS.PR.GET_TODO).catch(() => []),
          userId ? api.get(ENDPOINTS.PR.GET_MINE(userId)).catch(() => []) : [],
        ]);
        todoData = Array.isArray(results[0]) ? results[0] : results[0]?.data || [];
        mineData = Array.isArray(results[1]) ? results[1] : results[1]?.data || [];
      }

      setTodoList(todoData);
      setMineList(mineData);
      setAllList(allData);

      // 计算统计数据（合并后去重，因为可能有重叠）
      let dataForStats = [...todoData, ...mineData];
      let uniqueMap = new Map();
      dataForStats.forEach(r => {
        if (!uniqueMap.has(r.id)) {
          uniqueMap.set(r.id, r);
        }
      });
      let uniqueData = Array.from(uniqueMap.values());

      const total = uniqueData.length;
      const pending = uniqueData.filter(r => r.status_code === "submitted").length;
      const approved = uniqueData.filter(r => r.status_code === "approved").length;
      const rejected = uniqueData.filter(r => r.status_code === "rejected").length;

      setStats({
        total,
        pending,
        approved,
        rejected,
      });
    } catch (err) {
      const errMsg = err?.response?.data?.message || err?.message || "加载失败";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  }, [userId, isAdmin]);

  // 应用筛选
  const applyFilters = useCallback((list, filters) => {
    if (!list) return [];

    let filtered = [...list];

    // 按状态筛选（使用 status_code 英文状态码）
    if (filters.statusCodes && filters.statusCodes.length > 0) {
      filtered = filtered.filter(r => 
        filters.statusCodes.includes(r.status_code)
      );
    }

    // 按紧急程度筛选（使用中文）
    if (filters.urgencyCodes && filters.urgencyCodes.length > 0) {
      filtered = filtered.filter(r => 
        filters.urgencyCodes.includes(r.urgency)
      );
    }

    // 搜索（申请号、标题、发起人）
    if (filters.searchText && filters.searchText.trim()) {
      const text = filters.searchText.toLowerCase();
      filtered = filtered.filter(r => 
        (r.prNumber && r.prNumber.toLowerCase().includes(text)) ||
        (r.title && r.title.toLowerCase().includes(text)) ||
        (r.owner_name && r.owner_name.toLowerCase().includes(text))
      );
    }

    return filtered;
  }, []);

  return {
    todoList,
    mineList,
    allList,
    stats,
    loading,
    error,
    setError,
    isAdmin,
    loadTodoList,
    loadMineList,
    loadAllList,
    loadInitial,
    applyFilters,
  };
}