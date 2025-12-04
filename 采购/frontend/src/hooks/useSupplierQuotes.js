// src/hooks/useSupplierQuotes.js
// 供应商报价库 Hook（强化版）：精准解析 supplierId 并注入 Supplier-ID 请求头
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/http";

// —— 工具：把任意输入转成合法的正整数 ID
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

// —— 从多个来源解析 supplierId（有顺序）
function resolveSupplierId(paramId) {
  const viaProp = toIntId(paramId);
  if (viaProp) return { id: viaProp, source: "prop" };
  try {
    const usp = new URLSearchParams(window.location.search || "");
    const viaQuery = toIntId(usp.get("supplier_id"));
    if (viaQuery) return { id: viaQuery, source: "query" };
  } catch {}
  try {
    const session = JSON.parse(localStorage.getItem("supplier_session") || "{}");
    const viaSession = toIntId(session?.supplier_id);
    if (viaSession) return { id: viaSession, source: "supplier_session" };
  } catch {}
  try {
    const token = localStorage.getItem("supplierToken");
    const viaToken = extractIdFromToken(token);
    if (viaToken) return { id: viaToken, source: "supplierToken" };
  } catch {}
  try {
    const viaLS = toIntId(
      localStorage.getItem("supplierId") || localStorage.getItem("Supplier-ID")
    );
    if (viaLS) return { id: viaLS, source: "localStorage" };
  } catch {}
  try {
    const viaSS = toIntId(sessionStorage.getItem("supplierId"));
    if (viaSS) return { id: viaSS, source: "sessionStorage" };
  } catch {}
  try {
    // eslint-disable-next-line no-underscore-dangle
    const viaGlobal = toIntId(window.SUPPLIER_ID || window.__SUPPLIER_ID__);
    if (viaGlobal) return { id: viaGlobal, source: "global" };
  } catch {}
  return { id: null, source: "none" };
}

// —— 登录成功后调用，固化 supplierId
export function rememberSupplierId(id) {
  const n = toIntId(id);
  if (!n) return false;
  try {
    localStorage.setItem("supplierId", String(n));
    sessionStorage.setItem("supplierId", String(n));
    localStorage.setItem("Supplier-ID", String(n));
    return true;
  } catch {
    return false;
  }
}

/**
 * useSupplierQuotes
 */
export default function useSupplierQuotes({
  supplierId: supplierIdParam,
  perPage = 10,
  initialStatus = "",
  initialKeyword = "",
} = {}) {
  const { id: resolvedId, source } = resolveSupplierId(supplierIdParam);
  const supplierId = resolvedId;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState(initialStatus);
  const [keyword, setKeyword] = useState(initialKeyword);
  const [data, setData] = useState({ quotes: [], page: 1, pages: 0, total: 0 });

  const loggedRef = useRef(false);
  useEffect(() => {
    if (!loggedRef.current) {
      console.debug(
        "[useSupplierQuotes] supplierId =",
        supplierId,
        "(source:",
        source + ")"
      );
      loggedRef.current = true;
    }
  }, [supplierId, source]);

  useEffect(() => {
    if (supplierId && (source === "supplier_session" || source === "supplierToken")) {
      try {
        if (!localStorage.getItem("supplierId")) {
          localStorage.setItem("supplierId", String(supplierId));
        }
        if (!localStorage.getItem("Supplier-ID")) {
          localStorage.setItem("Supplier-ID", String(supplierId));
        }
        console.debug(
          "[useSupplierQuotes] 回填 supplierId 到 localStorage：",
          supplierId,
          "(source:",
          source + ")"
        );
      } catch {}
    }
  }, [supplierId, source]);

  const fetchList = useCallback(
    async (opts = {}) => {
      if (!supplierId) {
        setError("缺少 Supplier-ID（请先完成供应商登录并写入 supplierId）");
        return;
      }

      const p = opts.page ?? page;
      const st = opts.status ?? status;
      const kw = opts.keyword ?? keyword;

      setLoading(true);
      setError("");
      try {
        const resp = await api.get("/api/v1/suppliers/me/quotes", {
          headers: { "Supplier-ID": supplierId },
          params: {
            page: p,
            per_page: perPage,
            status: st || undefined,
            keyword: kw || undefined,
          },
        });

        // 重要：你的 http.js 返回的是“纯 payload”，不是 { data: ... }
        const payload = resp || {};
        const quotes = Array.isArray(payload.quotes) ? payload.quotes : [];

        setData({
          quotes,
          page: Number(payload.page || p),
          pages: Number(payload.pages || 0),
          total: Number(payload.total || 0),
        });
        setPage(Number(payload.page || p));
      } catch (e) {
        const msg =
          e?.payload?.error ||
          e?.payload?.message ||
          e?.message ||
          "获取报价库失败";
        console.error("[useSupplierQuotes] 获取报价库失败:", e);
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    [supplierId, page, status, keyword, perPage]
  );

  useEffect(() => {
    fetchList({ page: 1 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supplierId, status, keyword, perPage]);

  const setStatusAndReload = useCallback((st) => {
    setStatus(st);
    setPage(1);
  }, []);

  const setKeywordAndReload = useCallback((kw) => {
    setKeyword(kw);
    setPage(1);
  }, []);

  const goPage = useCallback((p) => {
    fetchList({ page: p });
  }, [fetchList]);

  const quotes = useMemo(() => {
    const decorate = (q) => {
      // ✅ 1) 首选后端返回的新格式：YYMMDD-供应商-序号
      //    后端字段名是 display_no，例如 "251101-0001-001"
      const displayNoBackend = q?.display_no;

      // ✅ 2) 兜底：沿用旧规则 Q{rfq_id}-{id}
      const displayNoFallback =
        q?.rfq_id && q?.id ? `Q${q.rfq_id}-${q.id}` : `${q?.id ?? ""}`;

      return {
        ...q,
        displayNo: displayNoBackend || displayNoFallback,
      };
    };
    return (data.quotes || []).map(decorate);
  }, [data.quotes]);

  return {
    loading,
    error,
    data: { ...data, quotes },
    status,
    setStatus: setStatusAndReload,
    keyword,
    setKeyword: setKeywordAndReload,
    page,
    setPage: goPage,
    reload: () => fetchList({ page }),
    supplierId,
    supplierIdSource: source,
  };
}
