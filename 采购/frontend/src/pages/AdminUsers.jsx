import React, { useState, useEffect } from "react";
import { useAuth } from "../auth/AuthContext.jsx";
import UserSearchPanel from "../components/admin/UserSearchPanel.jsx";
import UserEditModal from "../components/admin/UserEditModal.jsx";

// 根据当前环境自动选择API地址
const getApiBaseURL = () => {
  return window.location.hostname === 'localhost'
    ? "http://localhost:5001"
    : "http://61.145.212.28:5001";  // 暂时使用IP+端口，等DNS配置后改为域名
};

const API_BASE_URL = getApiBaseURL() + "/api/v1";

export default function AdminUsers() {
  console.log("AdminUsers component rendered");

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState({});
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const { user } = useAuth();

  // 新增：编辑弹窗状态
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);

  // 获取用户列表
  const fetchUsers = async () => {
    try {
      console.log("开始获取用户列表...");
      setLoading(true);
      setError("");

      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        method: "GET",
        headers: { "Content-Type": "application/json", "User-ID": user?.id, "User-Role": user?.role},
        credentials: "include",
      });

      console.log("API响应状态:", response.status);
      console.log("API响应头:", Object.fromEntries(response.headers.entries()));

      if (response.ok) {
        const data = await response.json();
        console.log("获取到的用户数据:", data);
        setUsers(Array.isArray(data) ? data : []);
        setError("");
      } else {
        const errorText = await response.text();
        console.error("获取用户列表失败:", {
          status: response.status,
          statusText: response.statusText,
          error: errorText,
        });
        setError(`获取用户列表失败: ${response.status} - ${response.statusText}`);
      }
    } catch (error) {
      console.error("获取用户列表时发生网络错误:", error);
      setError(`网络错误: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 审批用户
  const approveUser = async (userId) => {
    try {
      console.log(`审批用户 ID: ${userId}`);
      setActionLoading((prev) => ({ ...prev, [userId]: "approving" }));
      setError("");

      const response = await fetch(`${API_BASE_URL}/approve/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "User-ID": user?.id, "User-Role": user?.role },
        credentials: "include",
      });

      console.log("审批响应状态:", response.status);

      if (response.ok) {
        await response.json().catch(() => ({}));
        setUsers((prev) =>
          prev.map((u) => (u.id === userId ? { ...u, status: "approved" } : u))
        );
        setSuccess("用户审批成功");
        setTimeout(() => setSuccess(""), 3000);
      } else {
        const errorText = await response.text();
        console.error("审批失败:", {
          status: response.status,
          statusText: response.statusText,
          error: errorText,
        });
        setError(`审批失败: ${response.status} - ${response.statusText}`);
      }
    } catch (error) {
      console.error("审批用户时发生网络错误:", error);
      setError(`网络错误: ${error.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [userId]: null }));
    }
  };

  // 拒绝用户
  const rejectUser = async (userId) => {
    try {
      console.log(`拒绝用户 ID: ${userId}`);
      setActionLoading((prev) => ({ ...prev, [userId]: "rejecting" }));
      setError("");

      const response = await fetch(`${API_BASE_URL}/reject/${userId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "User-ID": user?.id, "User-Role": user?.role },
        credentials: "include",
      });

      console.log("拒绝响应状态:", response.status);

      if (response.ok) {
        await response.json().catch(() => ({}));
        setUsers((prev) =>
          prev.map((u) => (u.id === userId ? { ...u, status: "rejected" } : u))
        );
        setSuccess("用户已拒绝");
        setTimeout(() => setSuccess(""), 3000);
      } else {
        const errorText = await response.text();
        console.error("拒绝失败:", {
          status: response.status,
          statusText: response.statusText,
          error: errorText,
        });
        setError(`拒绝失败: ${response.status} - ${response.statusText}`);
      }
    } catch (error) {
      console.error("拒绝用户时发生网络错误:", error);
      setError(`网络错误: ${error.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [userId]: null }));
    }
  };

  // 删除用户
  const deleteUser = async (userId) => {
    if (!window.confirm("确定要删除这个用户吗？此操作不可撤销。")) return;

    try {
      console.log(`删除用户 ID: ${userId}`);
      setActionLoading((prev) => ({ ...prev, [userId]: "deleting" }));
      setError("");

      const response = await fetch(`${API_BASE_URL}/delete/${userId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json", "User-ID": user?.id, "User-Role": user?.role },
        credentials: "include",
      });

      console.log("删除响应状态:", response.status);

      if (response.ok) {
        await response.json().catch(() => ({}));
        setUsers((prev) => prev.filter((u) => u.id !== userId));
        setSuccess("用户已删除");
        setTimeout(() => setSuccess(""), 3000);
      } else {
        const errorText = await response.text();
        console.error("删除失败:", {
          status: response.status,
          statusText: response.statusText,
          error: errorText,
        });
        setError(`删除失败: ${response.status} - ${response.statusText}`);
      }
    } catch (error) {
      console.error("删除用户时发生网络错误:", error);
      setError(`网络错误: ${error.message}`);
    } finally {
      setActionLoading((prev) => ({ ...prev, [userId]: null }));
    }
  };

  // 打开编辑弹窗
  const openEditor = (u) => {
    setEditingUser(u);
    setEditorOpen(true);
  };
  const closeEditor = () => {
    setEditorOpen(false);
    setEditingUser(null);
  };

  // 保存成功后的本地更新
  const handleSaved = (updated) => {
    if (!updated) return;
    console.log("用户已更新:", updated);
    setUsers((prev) => prev.map((x) => (x.id === updated.id ? { ...x, ...updated } : x)));
    setSuccess("用户信息已更新");
    setTimeout(() => setSuccess(""), 3000);
  };

  // 初始加载
  useEffect(() => {
    fetchUsers();
  }, []);

  // 分类用户
  const pendingUsers = users.filter((u) => u.status === "pending");
  const approvedUsers = users.filter((u) => u.status === "approved");
  const rejectedUsers = users.filter((u) => u.status === "rejected");

  // 加载状态
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">加载用户列表中...</p>
        </div>
      </div>
    );
  }

  // 操作按钮组件 - 优化移动端显示
  const ActionButton = ({ onClick, loading, disabled = false, className, children }) => (
    <button
      onClick={onClick}
      disabled={loading || disabled}
      className={`px-2 md:px-3 py-1 rounded text-xs md:text-sm font-medium transition-opacity ${className} ${
        loading || disabled ? "opacity-50 cursor-not-allowed" : "hover:opacity-90 cursor-pointer"
      }`}
    >
      {loading ? "..." : children}
    </button>
  );

  // 角色徽章
  const RoleBadge = ({ role }) => {
    const roleMap = {
      super_admin: { bg: "bg-red-100", text: "text-red-800", label: "超管" },
      admin: { bg: "bg-purple-100", text: "text-purple-800", label: "管理员" },
      user: { bg: "bg-blue-100", text: "text-blue-800", label: "用户" },
      guest: { bg: "bg-gray-100", text: "text-gray-800", label: "游客" },
    };
    const config = roleMap[role] || roleMap.user;
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  // 状态徽章
  const StatusBadge = ({ status }) => {
    const statusMap = {
      pending: { bg: "bg-yellow-100", text: "text-yellow-800", label: "待审批" },
      approved: { bg: "bg-green-100", text: "text-green-800", label: "已批准" },
      rejected: { bg: "bg-red-100", text: "text-red-800", label: "已拒绝" },
    };
    const config = statusMap[status] || statusMap.pending;
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  // 用户表格组件 - 添加移动端响应式
  const UserTable = ({ users: tableUsers, showApprovalActions = false }) => (
    <div className="bg-white shadow-md rounded-lg overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户名</th>
              <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden sm:table-cell">邮箱</th>
              <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">角色</th>
              <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider hidden lg:table-cell">注册时间</th>
              <th className="px-3 md:px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {tableUsers.map((u) => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-3 md:px-6 py-4 whitespace-nowrap text-xs md:text-sm text-gray-500">{u.id}</td>
                <td className="px-3 md:px-6 py-4 whitespace-nowrap text-xs md:text-sm font-medium text-gray-900">{u.username}</td>
                <td className="px-3 md:px-6 py-4 whitespace-nowrap text-xs md:text-sm text-gray-500 hidden sm:table-cell">{u.email}</td>
                <td className="px-3 md:px-6 py-4 whitespace-nowrap text-xs md:text-sm text-gray-500"><RoleBadge role={u.role} /></td>
                <td className="px-3 md:px-6 py-4 whitespace-nowrap text-xs md:text-sm text-gray-500 hidden lg:table-cell">
                  {u.created_at ? new Date(u.created_at).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit'
                  }) : "未知"}
                </td>
                <td className="px-3 md:px-6 py-4 whitespace-nowrap text-xs md:text-sm font-medium">
                  <div className="flex flex-wrap gap-1">
                    {showApprovalActions && (
                      <>
                        <ActionButton
                          onClick={() => approveUser(u.id)}
                          loading={actionLoading[u.id] === "approving"}
                          className="bg-green-500 text-white"
                        >
                          批准
                        </ActionButton>
                        <ActionButton
                          onClick={() => rejectUser(u.id)}
                          loading={actionLoading[u.id] === "rejecting"}
                          className="bg-yellow-500 text-white"
                        >
                          拒绝
                        </ActionButton>
                      </>
                    )}
                    {!showApprovalActions && <StatusBadge status={u.status} />}
                    <ActionButton
                      onClick={() => openEditor(u)}
                      loading={false}
                      className="bg-blue-500 text-white"
                    >
                      编辑
                    </ActionButton>
                    <ActionButton
                      onClick={() => deleteUser(u.id)}
                      loading={actionLoading[u.id] === "deleting"}
                      disabled={u.id === user?.id}
                      className="bg-red-500 text-white"
                    >
                      删除
                    </ActionButton>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* 标题 - 响应式 */}
      <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold text-gray-900 mb-2">用户管理</h1>
      <p className="text-sm md:text-base text-gray-600 mb-6">管理平台用户和权限</p>

      {/* 成功/错误消息 */}
      {success && (
        <div className="mb-4 p-3 md:p-4 bg-green-50 border border-green-200 rounded-lg text-green-800 text-sm md:text-base">
          {success}
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 md:p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm md:text-base">
          {error}
        </div>
      )}

      {/* 搜索面板 */}
      <UserSearchPanel onEdit={openEditor} />

      {/* 待审批用户 */}
      <div className="mb-8">
        <h2 className="text-lg md:text-xl font-semibold mb-4 text-gray-700 flex items-center gap-2">
          <span>待审批用户</span>
          <span className="text-yellow-600 text-base md:text-lg">({pendingUsers.length})</span>
        </h2>
        {pendingUsers.length > 0 ? (
          <UserTable users={pendingUsers} showApprovalActions={true} />
        ) : (
          <div className="bg-gray-100 p-6 md:p-8 rounded-lg text-center text-gray-500">
            <div className="text-3xl mb-2">📋</div>
            <p className="text-sm md:text-base">暂无待审批用户</p>
          </div>
        )}
      </div>

      {/* 已批准用户 */}
      <div className="mb-8">
        <h2 className="text-lg md:text-xl font-semibold mb-4 text-gray-700 flex items-center gap-2">
          <span>已批准用户</span>
          <span className="text-green-600 text-base md:text-lg">({approvedUsers.length})</span>
        </h2>
        {approvedUsers.length > 0 ? (
          <UserTable users={approvedUsers} showApprovalActions={false} />
        ) : (
          <div className="bg-gray-100 p-6 md:p-8 rounded-lg text-center text-gray-500">
            <div className="text-3xl mb-2">✅</div>
            <p className="text-sm md:text-base">暂无已批准用户</p>
          </div>
        )}
      </div>

      {/* 已拒绝用户 */}
      <div className="mb-8">
        <h2 className="text-lg md:text-xl font-semibold mb-4 text-gray-700 flex items-center gap-2">
          <span>已拒绝用户</span>
          <span className="text-red-600 text-base md:text-lg">({rejectedUsers.length})</span>
        </h2>
        {rejectedUsers.length > 0 ? (
          <UserTable users={rejectedUsers} showApprovalActions={false} />
        ) : (
          <div className="bg-gray-100 p-6 md:p-8 rounded-lg text-center text-gray-500">
            <div className="text-3xl mb-2">❌</div>
            <p className="text-sm md:text-base">暂无已拒绝用户</p>
          </div>
        )}
      </div>

      {/* 编辑弹窗 */}
      <UserEditModal
        open={editorOpen}
        user={editingUser}
        onClose={closeEditor}
        onSaved={handleSaved}
      />
    </div>
  );
}
