import React, { useMemo, useState } from "react";
import { useAuth } from "../../auth/AuthContext";
import { ENDPOINTS } from "../../api/endpoints"

export default function UserEditModal({ open, user, onClose, onSaved }) {
  const { user: currentUser } = useAuth();
  const [form, setForm] = useState(() => user || null);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  React.useEffect(() => {
    setForm(user || null);
    setErr("");
  }, [user, open]);

  const canSave = useMemo(() => !!form && !!form.id, [form]);

  const saveProfile = async () => {
    if (!canSave) return;
    try {
      setSaving(true);
      setErr("");
      // 改资料：用户名 / 邮箱 / 状态
      const res = await fetch(ENDPOINTS.USER.UPDATE(form.id), {
        method: "PUT",
        credentials: "include",
        headers: { 
          "Content-Type": "application/json",
          "User-ID": currentUser?.id,
          "User-Role": currentUser?.role
        },
        body: JSON.stringify({
          username: form.username,
          email: form.email,
          status: form.status,
        }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status} ${res.statusText} - ${txt}`);
      }
      const updated = await res.json();
      onSaved?.(updated);
      onClose?.();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const saveRole = async () => {
    if (!canSave) return;
    try {
      setSaving(true);
      setErr("");
      // 改权限：role
      const res = await fetch(ENDPOINTS.USER.UPDATE_ROLE(form.id), {
        method: "POST",
        credentials: "include",
        headers: { 
          "Content-Type": "application/json",
          "User-ID": currentUser?.id,
          "User-Role": currentUser?.role
        },
        body: JSON.stringify({ role: form.role }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`${res.status} ${res.statusText} - ${txt}`);
      }
      // 成功后把 role 同步给上层
      onSaved?.({ ...form });
      onClose?.();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30" onClick={() => !saving && onClose?.()} />
      <div className="relative bg-white w-full max-w-lg rounded-xl shadow p-5 z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">编辑用户</h3>
          <button className="text-gray-500 hover:text-gray-700" onClick={() => !saving && onClose?.()}>
            ×
          </button>
        </div>

        {!form ? (
          <div className="text-sm text-gray-500">未选择用户</div>
        ) : (
          <div className="space-y-3">
            {err && <div className="text-sm text-red-600">保存失败：{err}</div>}

            <div>
              <label className="block text-sm text-gray-600 mb-1">用户ID</label>
              <input value={form.id} disabled className="w-full border rounded px-3 py-2 bg-gray-50" />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">用户名</label>
              <input
                value={form.username || ""}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-600 mb-1">邮箱</label>
              <input
                value={form.email || ""}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full border rounded px-3 py-2"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">角色</label>
                <select
                  value={form.role || "user"}
                  onChange={(e) => setForm({ ...form, role: e.target.value })}
                  className="w-full border rounded px-3 py-2 bg-white"
                >
                  <option value="user">普通用户</option>
                  <option value="admin">管理员</option>
                  <option value="super_admin">超级管理员</option>
                </select>
                <button
                  onClick={saveRole}
                  className="mt-2 px-3 py-2 rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-60"
                  disabled={saving}
                >
                  {saving ? "保存中..." : "保存权限"}
                </button>
              </div>

              <div>
                <label className="block text-sm text-gray-600 mb-1">状态</label>
                <select
                  value={form.status || "pending"}
                  onChange={(e) => setForm({ ...form, status: e.target.value })}
                  className="w-full border rounded px-3 py-2 bg-white"
                >
                  <option value="pending">待审批</option>
                  <option value="approved">已批准</option>
                  <option value="rejected">已拒绝</option>
                </select>
                <button
                  onClick={saveProfile}
                  className="mt-2 px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                  disabled={saving}
                >
                  {saving ? "保存中..." : "保存资料"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}