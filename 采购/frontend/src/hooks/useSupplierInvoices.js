// hooks/useSupplierInvoices.js
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { ENDPOINTS } from '../api/endpoints';

// 使用环境变量配置API地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5001";

export function useSupplierInvoices(page = 1, status = null, keyword = '') {
  const { user } = useAuth();
  const [invoices, setInvoices] = useState([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchInvoices = async (pageNum = page) => {
    if (!user || !user.id) return;

    try {
      setLoading(true);
      setError("");

      let url = API_BASE_URL + ENDPOINTS.SUPPLIER.GET_INVOICES(pageNum, 10);
      if (status) url += `&status=${status}`;
      if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;

      const res = await fetch(url, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "Supplier-ID": user.id,
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "获取发票列表失败");
      }

      const data = await res.json();
      setInvoices(data.invoices || []);
      setTotal(data.total || 0);
      setPages(data.pages || 0);
    } catch (e) {
      setError(e.message);
      console.error("获取发票列表错误:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices(page);
  }, [user?.id, page, status, keyword]);

  const uploadInvoice = async (invoiceData) => {
    if (!user || !user.id) return;

    try {
      const res = await fetch(API_BASE_URL + ENDPOINTS.SUPPLIER.UPLOAD_INVOICE, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Supplier-ID": user.id,
        },
        body: JSON.stringify(invoiceData),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "上传发票失败");
      }

      const data = await res.json();
      // 刷新列表
      await fetchInvoices(page);
      return data;
    } catch (e) {
      console.error("上传发票错误:", e);
      throw e;
    }
  };

  const updateInvoice = async (invoiceId, updateData) => {
    if (!user || !user.id) return;

    try {
      const res = await fetch(API_BASE_URL + ENDPOINTS.SUPPLIER.UPDATE_INVOICE(invoiceId), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          "Supplier-ID": user.id,
        },
        body: JSON.stringify(updateData),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "编辑发票失败");
      }

      const data = await res.json();
      await fetchInvoices(page);
      return data;
    } catch (e) {
      console.error("编辑发票错误:", e);
      throw e;
    }
  };

  const deleteInvoice = async (invoiceId) => {
    if (!user || !user.id) return;

    try {
      const res = await fetch(API_BASE_URL + ENDPOINTS.SUPPLIER.DELETE_INVOICE(invoiceId), {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "Supplier-ID": user.id,
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "删除发票失败");
      }

      await fetchInvoices(page);
    } catch (e) {
      console.error("删除发票错误:", e);
      throw e;
    }
  };

  return {
    invoices,
    total,
    pages,
    loading,
    error,
    refetch: () => fetchInvoices(page),
    uploadInvoice,
    updateInvoice,
    deleteInvoice,
  };
}