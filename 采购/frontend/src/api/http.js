// src/api/http.js
import axios from 'axios';
import { authEvents, AUTH_EVENTS } from './authEvents';

// 从环境变量获取后端 API 地址
const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5001";
const PORTAL_URL = import.meta.env.VITE_PORTAL_URL || "/";

// —— 工具：安全取整
function toIntId(v) {
  if (v === null || v === undefined) return null;
  const n = Number(String(v).trim());
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : null;
}

// —— 从 token（如 "supplier_5"）解析 id
function extractIdFromToken(token) {
  if (!token) return null;
  const m = String(token).match(/supplier_(\d+)/i);
  return m ? toIntId(m[1]) : null;
}

// —— 解析 Supplier-ID 的集中逻辑（有顺序）
function resolveSupplierId() {
  // 1) 登录会话对象（登录页已写入）
  try {
    const session = JSON.parse(localStorage.getItem("supplier_session") || "{}");
    const viaSession = toIntId(session?.supplier_id);
    if (viaSession) return viaSession;
  } catch {}

  // 2) token: "supplier_5"
  try {
    const viaToken = extractIdFromToken(localStorage.getItem("supplierToken"));
    if (viaToken) return viaToken;
  } catch {}

  // 3) localStorage
  try {
    const viaLS =
      toIntId(localStorage.getItem("supplierId")) ||
      toIntId(localStorage.getItem("Supplier-ID"));
    if (viaLS) return viaLS;
  } catch {}

  // 4) sessionStorage
  try {
    const viaSS = toIntId(sessionStorage.getItem("supplierId"));
    if (viaSS) return viaSS;
  } catch {}

  // 5) 全局（极端兜底）
  try {
    const viaGlobal = toIntId(window.SUPPLIER_ID || window.__SUPPLIER_ID__);
    if (viaGlobal) return viaGlobal;
  } catch {}

  return null;
}

// —— 如果是"供应商登录响应"，自动把 ID 与会话落库
function maybePersistSupplierSession(url, payload) {
  try {
    const isSupplierLogin =
      /\/suppliers\/login\b/i.test(url) || /\/api\/v1\/suppliers\/login\b/i.test(url);
    if (!isSupplierLogin || !payload || typeof payload !== "object") return;

    const idFromPayload = toIntId(payload?.supplier?.id);
    const idFromToken = extractIdFromToken(payload?.token);
    const supplierId = idFromPayload || idFromToken;
    if (!supplierId) return;

    // 1) 单值 ID
    localStorage.setItem("supplierId", String(supplierId));
    localStorage.setItem("Supplier-ID", String(supplierId));
    sessionStorage.setItem("supplierId", String(supplierId));

    // 2) 会话对象
    const sessionPayload = {
      supplier_id: supplierId,
      company_name: payload?.supplier?.company_name || "",
      email: payload?.supplier?.email || payload?.supplier?.contact_email || "",
      status: payload?.supplier?.status || "approved",
      role: "supplier",
      token: payload?.token || "",
      login_at: Date.now(),
    };
    localStorage.setItem("supplier_session", JSON.stringify(sessionPayload));

    // 3) token（若有）
    if (sessionPayload.token) {
      localStorage.setItem("supplierToken", sessionPayload.token);
    }

    console.debug("[http] supplier login persisted:", { supplierId, hasToken: !!sessionPayload.token });
  } catch (e) {
    console.warn("[http] persist supplier session failed:", e);
  }
}

// 创建 axios 实例
const axiosInstance = axios.create({
  baseURL: BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加认证头
axiosInstance.interceptors.request.use(
  (config) => {
    // 添加 JWT token
    const token = localStorage.getItem("token") || localStorage.getItem("supplierToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 添加用户信息头
    const userStr = localStorage.getItem("user");
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user.id) config.headers["User-ID"] = String(user.id);
        if (user.role) config.headers["User-Role"] = user.role;
      } catch {}
    }

    // 添加 Supplier-ID 头
    const sid = resolveSupplierId();
    if (sid) {
      config.headers["Supplier-ID"] = String(sid);
    }

    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理401和供应商会话
axiosInstance.interceptors.response.use(
  (response) => {
    // 如果是供应商登录响应，自动落库
    maybePersistSupplierSession(response.config.url, response.data);
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      authEvents.emit(AUTH_EVENTS.UNAUTHORIZED, {
        url: error.config?.url,
        status: 401,
      });
      return Promise.reject(error);
    }
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// 提供封装后的 API 请求方法（保持与原有接口一致）
export const api = {
  get: (p, opt) => axiosInstance.get(p, opt),
  post: (p, data, opt) => axiosInstance.post(p, data, opt),
  put: (p, data, opt) => axiosInstance.put(p, data, opt),
  delete: (p, opt) => axiosInstance.delete(p, opt),
  del: (p, opt) => axiosInstance.delete(p, opt),
  patch: (p, data, opt) => axiosInstance.patch(p, data, opt),
};

// 导出 BASE URL，供其他模块使用
export const BASE_URL = BASE;

// 默认导出
export default api;
