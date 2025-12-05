// hooks/useSupplierStats.js
import { useState, useEffect } from 'react';
import { useAuth } from '../auth/AuthContext';
import { ENDPOINTS } from '../api/endpoints';

// 使用环境变量配置API地址
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5001";

export function useSupplierStats() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchStats = async () => {
    if (!user || !user.id) return;

    try {
      setLoading(true);
      setError("");

      const res = await fetch(`${API_BASE_URL}${ENDPOINTS.SUPPLIER.GET_STATISTICS}`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "Supplier-ID": user.id,
        },
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || "获取统计信息失败");
      }

      const data = await res.json();
      setStats(data?.data ?? data);
    } catch (e) {
      setError(e.message);
      console.error("获取统计信息错误:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [user?.id]);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
  };
}