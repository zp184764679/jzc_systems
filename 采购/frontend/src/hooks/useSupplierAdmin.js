// src/hooks/useSupplierAdmin.js
import { useState, useCallback } from "react";
import { api } from "../api/http";
import { ENDPOINTS } from "../api/endpoints";

export function useSupplierAdmin() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total: 0,
    total_pages: 0,
  });

  /**
   * 获取供应商列表
   * @param {number} page - 页码
   * @param {string} status - 状态筛选 (approved, pending, rejected, all)
   * @param {string} keyword - 搜索关键词
   * @param {number} per_page - 每页数量
   */
  const fetchList = useCallback(
    async (page = 1, status = "all", keyword = "", per_page = 10) => {
      setLoading(true);
      setError(null);
      try {
        const url =
          status && status !== "all"
            ? ENDPOINTS.SUPPLIER.ADMIN_LIST(status)
            : ENDPOINTS.SUPPLIER.ADMIN_LIST();

        const response = await api.get(url, {
          params: {
            page,
            per_page,
            keyword: keyword || undefined,
          },
        });

        setSuppliers(response.data || []);
        setPagination({
          page: response.pagination?.page || page,
          per_page: response.pagination?.per_page || per_page,
          total: response.pagination?.total || 0,
          total_pages: response.pagination?.total_pages || 1,
        });

        return response.data;
      } catch (err) {
        const errorMsg = err.response?.data?.message || err.message || "获取供应商列表失败";
        setError(errorMsg);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /**
   * 获取单个供应商详情
   * @param {number} id - 供应商ID
   */
  const fetchDetail = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(ENDPOINTS.SUPPLIER.ADMIN_GET(id));
      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "获取供应商详情失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 更新供应商信息
   * @param {number} id - 供应商ID
   * @param {object} data - 更新数据
   */
  const updateSupplier = useCallback(async (id, data) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.put(ENDPOINTS.SUPPLIER.ADMIN_UPDATE(id), data);

      // 更新本地列表
      setSuppliers((prev) =>
        prev.map((s) => (s.id === id ? { ...s, ...response.data } : s))
      );

      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "更新供应商失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 删除供应商
   * @param {number} id - 供应商ID
   */
  const deleteSupplier = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      await api.delete(ENDPOINTS.SUPPLIER.ADMIN_DELETE(id));

      // 更新本地列表
      setSuppliers((prev) => prev.filter((s) => s.id !== id));

      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "删除供应商失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 冻结供应商
   * @param {number} id - 供应商ID
   * @param {string} reason - 冻结原因
   */
  const freezeSupplier = useCallback(async (id, reason = "") => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.put(ENDPOINTS.SUPPLIER.ADMIN_FREEZE(id), {
        reason,
      });

      // 更新本地列表
      setSuppliers((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, status: "frozen", frozen_reason: reason } : s
        )
      );

      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "冻结供应商失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 加入黑名单
   * @param {number} id - 供应商ID
   * @param {string} reason - 黑名单原因
   */
  const blacklistSupplier = useCallback(async (id, reason = "") => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.put(ENDPOINTS.SUPPLIER.ADMIN_BLACKLIST(id), {
        reason,
      });

      // 更新本地列表
      setSuppliers((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, status: "blacklisted", blacklist_reason: reason } : s
        )
      );

      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "加入黑名单失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 批准供应商
   * @param {number} id - 供应商ID
   */
  const approveSupplier = useCallback(async (id) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(ENDPOINTS.SUPPLIER.APPROVE(id));

      // 更新本地列表
      setSuppliers((prev) =>
        prev.map((s) => (s.id === id ? { ...s, status: "approved" } : s))
      );

      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "批准供应商失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 拒绝供应商
   * @param {number} id - 供应商ID
   * @param {string} reason - 拒绝原因
   */
  const rejectSupplier = useCallback(async (id, reason = "") => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post(ENDPOINTS.SUPPLIER.REJECT(id), {
        reason,
      });

      // 更新本地列表
      setSuppliers((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, status: "rejected", reject_reason: reason } : s
        )
      );

      return response.data;
    } catch (err) {
      const errorMsg = err.response?.data?.message || "拒绝供应商失败";
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // 数据
    suppliers,
    loading,
    error,
    pagination,

    // 方法
    fetchList,
    fetchDetail,
    updateSupplier,
    deleteSupplier,
    freezeSupplier,
    blacklistSupplier,
    approveSupplier,
    rejectSupplier,

    // 辅助方法
    setError,
    setSuppliers,
  };
}

export default useSupplierAdmin;