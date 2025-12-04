"""
企业管理系统集成平台 - Portal Server
运行在端口 80 (需要管理员权限) 或 8080
"""
import http.server
import socketserver
import os
import sys

# 设置端口
PORT = 80  # 如果80端口需要管理员权限，会自动切换到8080

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 添加CORS头，允许跨域访问
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def log_message(self, format, *args):
        # 自定义日志格式
        sys.stdout.write("%s - %s\n" % (self.address_string(), format % args))

def start_server(port):
    """启动HTTP服务器"""
    # 切换到Portal目录
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    Handler = MyHTTPRequestHandler

    try:
        with socketserver.TCPServer(("", port), Handler) as httpd:
            print("=" * 60)
            print("企业管理系统集成平台 Portal Server")
            print("=" * 60)
            print(f"服务器运行在: http://localhost:{port}")
            print(f"请在浏览器中访问: http://localhost:{port}")
            print("-" * 60)
            print("集成的子系统:")
            print("  1. PDM系统     - http://localhost:8000")
            print("  2. PM系统      - http://localhost:5175")
            print("  3. CRM系统     - http://localhost:3000")
            print("  4. HR系统      - http://localhost:6000")
            print("  5. SCM系统     - http://localhost:7000")
            print("  6. EAM系统     - http://localhost:7200")
            print("  7. SHM系统     - http://localhost:7500")
            print("-" * 60)
            print("按 Ctrl+C 停止服务器")
            print("=" * 60)
            httpd.serve_forever()
    except PermissionError:
        if port == 80:
            print(f"端口 {port} 需要管理员权限，尝试使用端口 8080...")
            return start_server(8080)
        else:
            print(f"无法绑定端口 {port}，请检查端口是否被占用")
            sys.exit(1)
    except OSError as e:
        if port == 80:
            print(f"端口 {port} 被占用或需要管理员权限，尝试使用端口 8080...")
            return start_server(8080)
        else:
            print(f"无法启动服务器: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n服务器已停止")
        sys.exit(0)

if __name__ == "__main__":
    start_server(PORT)
