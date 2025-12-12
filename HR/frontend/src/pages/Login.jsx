import { useState } from "react";

export default function Login({ onLoginSuccess, onShowRegister }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await fetch("/hr/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (response.ok) {
        // 登录成功，调用回调函数
        if (onLoginSuccess) {
          onLoginSuccess();
        }
      } else {
        setError(data.error || "登录失败");
      }
    } catch (err) {
      setError("网络错误，请重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, #2196F3 0%, #1976D2 100%)",
      padding: isMobile ? "16px" : "20px",
    }}>
      <div style={{
        background: "white",
        padding: isMobile ? "24px 20px" : "40px",
        borderRadius: isMobile ? "12px" : "10px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.2)",
        width: "100%",
        maxWidth: "400px",
      }}>
        <h2 style={{
          textAlign: "center",
          marginBottom: isMobile ? "24px" : "30px",
          color: "#333",
          fontSize: isMobile ? "22px" : "24px",
        }}>
          HR系统登录
        </h2>
        
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: "20px" }}>
            <label style={{ 
              display: "block", 
              marginBottom: "8px",
              color: "#555",
              fontWeight: "500",
            }}>
              用户名
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "12px",
                border: "1px solid #ddd",
                borderRadius: "5px",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
              placeholder="请输入用户名"
            />
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label style={{ 
              display: "block", 
              marginBottom: "8px",
              color: "#555",
              fontWeight: "500",
            }}>
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{
                width: "100%",
                padding: "12px",
                border: "1px solid #ddd",
                borderRadius: "5px",
                fontSize: "14px",
                boxSizing: "border-box",
              }}
              placeholder="请输入密码"
            />
          </div>

          {error && (
            <div style={{
              padding: "12px",
              marginBottom: "20px",
              background: "#fee",
              color: "#c33",
              borderRadius: "5px",
              fontSize: "14px",
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "14px",
              background: loading ? "#999" : "#2196F3",
              color: "white",
              border: "none",
              borderRadius: "5px",
              fontSize: "16px",
              fontWeight: "600",
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.3s",
            }}
          >
            {loading ? "登录中..." : "登录"}
          </button>
        </form>

        <div style={{
          marginTop: "20px",
          textAlign: "center",
          fontSize: "14px",
        }}>
          <button
            onClick={onShowRegister}
            style={{
              background: "none",
              border: "none",
              color: "#2196F3",
              cursor: "pointer",
              textDecoration: "underline",
              fontSize: "14px",
            }}
          >
            没有账户？立即注册
          </button>
        </div>

{/* 安全修复：移除默认账户显示，避免暴露凭证 */}
      </div>
    </div>
  );
}
