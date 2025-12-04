import React, { useEffect, useState } from "react";
import { ENDPOINTS } from "../../api/endpoints"

export default function UserSearchPanel({ onEdit }) {
  const [kw, setKw] = useState("");
  const [loading, setLoading] = useState(false);
  const [list, setList] = useState([]);
  const [error, setError] = useState("");

  const search = async (q) => {
    const keyword = (q ?? kw).trim();
    if (!keyword) {
      setList([]);
      setError("");
      return;
    }
    try {
      setLoading(true);
      setError("");
      const res = await fetch(ENDPOINTS.USER.SEARCH(keyword), {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status} ${res.statusText} - ${txt}`);
      }
      const data = await res.json();
      setList(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e.message);
      setList([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(() => search(kw), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kw]);

  const RoleBadge = ({ role }) => (
    <span className={`px-2 py-0.5 rounded-full text-xs ${role === "admin" ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-700"}`}>
      {role === "admin" ? "管理员" : "普通用户"}
    </span>
  );

  const StatusBadge = ({ status }) => {
    const mp = { approved: "bg-green-100 text-green-700", pending: "bg-blue-100 text-blue-700", rejected: "bg-red-100 text-red-700" };
    const label = { approved: "已批准", pending: "待审批", rejected: "已拒绝" }[status] || status;
    return <span className={`px-2 py-0.5 rounded-full text-xs ${mp[status] || "bg-gray-100 text-gray-700"}`}>{label}</span>;
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center gap-3">
        <input
          value={kw}
          onChange={(e) => setKw(e.target.value)}
          placeholder="搜索用户名 / 邮箱 / ID"
          className="flex-1 border rounded px-3 py-2 outline-none focus:ring focus:ring-blue-200"
        />
        <button onClick={() => search()} className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          搜索
        </button>
      </div>

      {loading && <div className="text-sm text-gray-500 mt-3">正在搜索...</div>}
      {error && <div className="text-sm text-red-600 mt-3">搜索失败：{error}</div>}

      {list.length > 0 && (
        <div className="mt-4 border rounded overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-4 py-2 text-left">ID</th>
                <th className="px-4 py-2 text-left">用户名</th>
                <th className="px-4 py-2 text-left">邮箱</th>
                <th className="px-4 py-2 text-left">角色</th>
                <th className="px-4 py-2 text-left">状态</th>
                <th className="px-4 py-2 text-left">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {list.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2 text-sm text-gray-600">{u.id}</td>
                  <td className="px-4 py-2 text-sm">{u.username}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{u.email}</td>
                  <td className="px-4 py-2 text-sm"><RoleBadge role={u.role} /></td>
                  <td className="px-4 py-2 text-sm"><StatusBadge status={u.status} /></td>
                  <td className="px-4 py-2 text-sm">
                    <button onClick={() => onEdit(u)} className="px-3 py-1 rounded bg-amber-500 text-white hover:bg-amber-600">
                      编辑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && kw.trim() && list.length === 0 && (
        <div className="text-sm text-gray-500 mt-3">未找到匹配用户</div>
      )}
    </div>
  );
}