// src/api/http.js

// 从环境变量获取后端 API 地址
const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:5001";

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
    // eslint-disable-next-line no-underscore-dangle
    const viaGlobal = toIntId(window.SUPPLIER_ID || window.__SUPPLIER_ID__);
    if (viaGlobal) return viaGlobal;
  } catch {}

  return null;
}

// —— 如果是“供应商登录响应”，自动把 ID 与会话落库
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

    // 4) 控制台打印一次，方便确认已写入
    // eslint-disable-next-line no-console
    console.debug(
      "[http] supplier login persisted:",
      { supplierId, hasToken: !!sessionPayload.token }
    );
  } catch (e) {
    // eslint-disable-next-line no-console
    console.warn("[http] persist supplier session failed:", e);
  }
}

// 封装的请求函数，支持 GET、POST、PUT、DELETE 请求
async function req(path, { method = "GET", data, headers = {}, ...rest } = {}) {
  // 判断是否提供了完整的 URL 路径，否则拼接 BASE
  const url = path.startsWith("http") ? path : `${BASE}${path}`;

  // ✅ 获取用户信息，添加认证头（权限检查）
  const userStr = localStorage.getItem("user");
  const authHeaders = {};
  if (userStr) {
    try {
      const user = JSON.parse(userStr);
      if (user.id) authHeaders["User-ID"] = String(user.id);
      if (user.role) authHeaders["User-Role"] = user.role;
    } catch {
      /* ignore */
    }
  }

  // ✅ 自动注入 Supplier-ID（除非显式传入了同名头）
  const autoHeaders = {};
  if (!("Supplier-ID" in headers)) {
    const sid = resolveSupplierId();
    if (sid) autoHeaders["Supplier-ID"] = String(sid);
  }

  // 自动添加 Authorization 头（SSO token）
  const token = localStorage.getItem("token") || localStorage.getItem("supplierToken");
  if (token && !("Authorization" in headers)) {
    autoHeaders["Authorization"] = `Bearer ${token}`;
  }

  // 设置请求的初始化参数
  const init = {
    method,
    headers: {
      ...(data ? { "Content-Type": "application/json" } : {}), // 如果有数据，则设置 Content-Type 为 application/json
      ...authHeaders, // ✅ 添加用户认证头
      ...autoHeaders, // ✅ 自动注入 Supplier-ID（若存在）
      ...headers, // 可扩展的自定义 headers（显式传入优先级最高）
    },
    ...(data ? { body: JSON.stringify(data) } : {}), // 如果有数据，则设置请求体
    ...rest, // 其他传入的参数
  };

  // 发起请求
  const res = await fetch(url, init);

  // 获取返回的 Content-Type，并判断是否是 JSON 格式
  const ct = res.headers.get("content-type") || "";
  const isJSON = ct.includes("application/json");

  // 根据返回的格式，解析响应内容
  const payload = isJSON ? await res.json() : await res.text();

  // ✅ 如果是供应商登录响应，自动落库（无论调用方是谁）
  if (res.ok) {
    maybePersistSupplierSession(url, payload);
  }

  // 如果响应不正常，抛出错误（把更多上下文带出来）
  if (!res.ok) {
    const errorMessage =
      (isJSON && (payload?.error || payload?.message)) ||
      `HTTP ${res.status}`;
    const err = new Error(errorMessage);
    // 便于上层定位问题
    err.status = res.status;
    err.payload = payload;
    err.url = url;
    // eslint-disable-next-line no-console
    console.error("Request failed:", { url, status: res.status, payload });
    throw err;
  }

  return payload; // 返回解析后的响应数据
}

// 提供封装后的 API 请求方法
export const api = {
  get: (p, opt) => req(p, { ...opt, method: "GET" }),  // GET 请求
  post: (p, data, opt) => req(p, { ...opt, method: "POST", data }),  // POST 请求
  put: (p, data, opt) => req(p, { ...opt, method: "PUT", data }),  // PUT 请求
  delete: (p, opt) => req(p, { ...opt, method: "DELETE" }),  // DELETE 请求 ✅ 新增
  del: (p, opt) => req(p, { ...opt, method: "DELETE" }),  // DELETE 请求（别名）
  patch: (p, data, opt) => req(p, { ...opt, method: "PATCH", data }),  // PATCH 请求
};

// 导出 BASE URL，供其他模块使用
export const BASE_URL = BASE;

// 可选：默认导出，用于导入时写成 `import http from "../api/http.js"`
export default api;
