# 🚀 机加工报价系统 - GUI启动器

## 功能特点

✨ **一键启动**
- 同时启动前端（React）和后端（FastAPI）服务
- 自动检测并显示服务状态
- 支持单独控制每个服务

🔍 **实时监控**
- Redis 数据库状态
- Celery 任务队列状态
- Ollama 大模型状态
- 后端 API 状态（端口 8000）
- 前端界面状态（端口 5173）

📊 **可视化界面**
- 状态指示灯实时更新
- 运行日志实时显示
- 快捷访问按钮（前端页面、API文档）

## 使用方法

### 方法一：双击启动（推荐）
直接双击 `启动器.bat` 文件

### 方法二：命令行启动
```bash
# 1. 安装依赖（首次使用）
pip install -r requirements.txt

# 2. 启动 GUI
python launcher.py
```

## 依赖服务说明

启动器会检测以下服务状态：

| 服务 | 端口 | 说明 | 必需 |
|------|------|------|------|
| **Ollama** | 11434 | 大模型服务，用于OCR识别 | ⚠️ 推荐 |
| **Redis** | 6379 | 缓存和任务队列 | ⚠️ 推荐 |
| **Celery** | - | 异步任务处理 | 可选 |
| **后端** | 8000 | FastAPI 服务 | ✅ 必需 |
| **前端** | 5173 | React 前端界面 | ✅ 必需 |

### 启动依赖服务

#### 1. 启动 Ollama
```bash
# 启动 Ollama 服务
ollama serve

# 确认模型已安装
ollama list

# 如果没有，拉取模型
ollama pull qwen3-vl:7b
```

#### 2. 启动 Redis
```bash
# Windows (使用 WSL 或 Docker)
docker run -d -p 6379:6379 redis

# 或者安装 Redis for Windows
# 下载: https://github.com/microsoftarchive/redis/releases
```

#### 3. 启动 Celery（可选）
```bash
cd C:\Users\Admin\Desktop\报价\backend
venv\Scripts\activate
celery -A celery_app worker --loglevel=info
```

## 界面说明

### 状态指示器
- 🟢 绿色：服务在线/运行中
- 🔴 红色：服务离线/已停止
- 🟡 橙色：状态未知/启动中
- ⚪ 灰色：服务已停止

### 控制按钮
- **启动所有服务**：一键启动前后端
- **停止所有服务**：一键停止所有服务
- **刷新状态**：手动刷新服务状态
- **启动/停止后端**：单独控制后端服务
- **启动/停止前端**：单独控制前端服务

### 快捷访问
- **前端页面**：http://localhost:5173
- **API文档**：http://localhost:8000/docs

## 注意事项

1. **首次使用前**
   - 确保后端虚拟环境已创建：`python -m venv venv`
   - 确保后端依赖已安装：`pip install -r requirements.txt`
   - 确保前端依赖已安装：`npm install`

2. **端口占用**
   - 如果提示端口被占用，请检查是否有其他程序使用了 5173 或 8000 端口
   - 使用 `netstat -ano | findstr "5173"` 检查端口占用

3. **服务启动顺序**
   - 建议先启动依赖服务（Ollama、Redis）
   - 然后启动后端
   - 最后启动前端

4. **关闭启动器**
   - 关闭启动器窗口时，会自动停止所有正在运行的服务

## 故障排查

### 问题：后端启动失败
**解决方案**：
```bash
# 检查虚拟环境
cd C:\Users\Admin\Desktop\报价\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 问题：前端启动失败
**解决方案**：
```bash
# 检查依赖
cd C:\Users\Admin\Desktop\报价\frontend
npm install
```

### 问题：Ollama 无法连接
**解决方案**：
```bash
# 确保 Ollama 服务运行
ollama serve

# 检查端口
netstat -ano | findstr "11434"
```

### 问题：Redis 无法连接
**解决方案**：
```bash
# 使用 Docker 启动 Redis
docker run -d -p 6379:6379 redis

# 或安装 Redis for Windows
```

## 技术栈

- **GUI框架**：Tkinter（Python 标准库）
- **进程管理**：subprocess、psutil
- **网络检测**：socket、requests
- **多线程**：threading

## 开发信息

- **版本**：v1.0.0
- **Python 要求**：3.8+
- **开发日期**：2025-11

---

**祝您使用愉快！** 🎉
