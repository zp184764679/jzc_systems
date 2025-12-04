// src/hooks/useQuoteLibrary.js
import { useState, useCallback, useEffect } from "react";
import { api } from "../api/http";
import { ENDPOINTS } from "../api/endpoints";

export function useQuoteLibrary(initialPage = 1, initialFilters = {}) {
  const [quotes, setQuotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: initialPage,
    per_page: 10,
    total: 0,
    total_pages: 0,
  });
  const [filters, setFilters] = useState(initialFilters);

  /**
   * 获取报价库列表
   * @param {number} page - 页码
   * @param {number} per_page - 每页数量
   * @param {object} customFilters - 自定义筛选条件 { keyword, status, sort_by }
   */
  const fetchQuotes = useCallback(
    async (page = pagination.page, per_page = 10, customFilters = {}) => {
      setLoading(true);
      setError(null);
      try {
        const mergedFilters = { ...filters, ...customFilters };

        const url = ENDPOINTS.QUOTE_LIBRARY.GET_QUOTES_WITH_FILTER(
          page,
          per_page,
          mergedFilters
        );

        const response = await api.get(url);

        setQuotes(response.data || []);
        setPagination({
          page: response.pagination?.page || page,
          per_page: response.pagination?.per_page || per_page,
          total: response.pagination?.total || 0,
          total_pages: response.pagination?.total_pages || 1,
        });

        return response.data;
      } catch (err) {
        const errorMsg =
          err.response?.data?.message || err.message || "获取报价库列表失败";
        setError(errorMsg);
        console.error("获取报价库失败:", err);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [filters, pagination.page]
  );

  /**
   * 获取单个报价详情
   * @param {number} id - 报价ID
   */
  const fetchQuoteDetail = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(ENDPOINTS.QUOTE_LIBRARY.GET_QUOTE_DETAIL(id));
      return response.data;
    } catch (err) {
      const errorMsg =
        err.response?.data?.message || err.message || "获取报价详情失败";
      setError(errorMsg);
      console.error("获取报价详情失败:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 参与报价
   * @param {number} quoteId - 报价ID
   * @param {object} participateData - 参与数据 { total_price, lead_time, quote_data }
   */
  const participateQuote = useCallback(async (quoteId, participateData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(
        ENDPOINTS.QUOTE_LIBRARY.PARTICIPATE(quoteId),
        participateData
      );

      // 更新本地列表中的报价状态
      setQuotes((prev) =>
        prev.map((q) =>
          q.id === quoteId ? { ...q, status: "participated", ...response.data } : q
        )
      );

      return response.data;
    } catch (err) {
      const errorMsg =
        err.response?.data?.message || err.message || "参与报价失败";
      setError(errorMsg);
      console.error("参与报价失败:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 撤回报价
   * @param {number} quoteId - 报价ID
   */
  const withdrawQuote = useCallback(async (quoteId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(
        ENDPOINTS.QUOTE_LIBRARY.WITHDRAW(quoteId)
      );

      // 更新本地列表中的报价状态
      setQuotes((prev) =>
        prev.map((q) =>
          q.id === quoteId ? { ...q, status: "withdrawn", ...response.data } : q
        )
      );

      return response.data;
    } catch (err) {
      const errorMsg =
        err.response?.data?.message || err.message || "撤回报价失败";
      setError(errorMsg);
      console.error("撤回报价失败:", err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 更新筛选条件
   * @param {object} newFilters - 新筛选条件
   */
  const updateFilters = useCallback((newFilters) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    setPagination((prev) => ({ ...prev, page: 1 })); // 重置页码
  }, []);

  /**
   * 清除筛选条件
   */
  const clearFilters = useCallback(() => {
    setFilters({});
    setPagination((prev) => ({ ...prev, page: 1 }));
  }, []);

  /**
   * 变更页码
   * @param {number} newPage - 新页码
   */
  const changePage = useCallback((newPage) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
  }, []);

  // 初始化：页面加载时获取数据
  useEffect(() => {
    fetchQuotes(pagination.page, pagination.per_page, filters);
  }, [pagination.page, filters]);

  return {
    // 数据
    quotes,
    loading,
    error,
    pagination,
    filters,

    // 方法
    fetchQuotes,
    fetchQuoteDetail,
    participateQuote,
    withdrawQuote,
    updateFilters,
    clearFilters,
    changePage,

    // 辅助方法
    setError,
    setQuotes,
  };
}

export default useQuoteLibrary;