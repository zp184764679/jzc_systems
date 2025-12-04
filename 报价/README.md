# 机加工精密零件报价系统

## 📋 项目概述

这是一个智能化的机加工零件报价系统，实现从图纸识别到报价单生成的全流程自动化。

### 核心功能
- ✅ **图纸OCR识别**：基于Ollama + Qwen3-VL实现图纸自动识别
- ✅ **信息提取**：自动提取尺寸、材质、公差、工艺要求等
- ⏳ **智能报价**：基于工艺库和报价公式自动计算
- ⏳ **报价单生成**：一键生成专业报价单（PDF/Excel）

---

## 🚀 快速开始

### 环境要求
- Python 3.10+
- Node.js 18+
- Ollama (用于Vision OCR)

### 1. 安装Ollama和模型

```bash
# 安装Ollama（如果还没有）
# Windows: 从 https://ollama.com 下载安装

# 拉取Qwen3-VL模型
ollama pull qwen3-vl:7b

# 启动Ollama服务
ollama serve
```

### 2. 后端安装和启动

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python main.py
```

后端服务将运行在 http://localhost:8000

### 3. 测试OCR识别功能

```bash
# 测试OCR服务
python -c "from services.drawing_ocr_service import get_ocr_service; service = get_ocr_service(); print('OCR服务状态:', 'ready' if service.ollama_available else 'not ready')"
```

---

## 📁 项目结构

```
报价/
├── backend/                    # 后端代码
│   ├── api/                   # API路由
│   ├── config/                # 配置文件
│   │   ├── settings.py        # 系统设置
│   │   └── database.py        # 数据库配置
│   ├── models/                # 数据库模型
│   │   ├── material.py        # 材料库模型
│   │   ├── process.py         # 工艺库模型
│   │   ├── drawing.py         # 图纸模型
│   │   └── quote.py           # 报价模型
│   ├── services/              # 业务逻辑
│   │   └── drawing_ocr_service.py  # OCR识别服务
│   ├── utils/                 # 工具函数
│   ├── main.py               # FastAPI入口
│   ├── requirements.txt      # Python依赖
│   └── .env                  # 环境变量
│
├── frontend/                  # 前端代码（待创建）
│   ├── src/
│   └── package.json
│
├── 系统架构设计.md            # 技术架构设计文档
├── 报价公式.xls               # 报价公式（创怡兴tab为准）
└── README.md                  # 本文件
```

---

## 🎯 当前进度

### ✅ 已完成
1. **系统架构设计** - 详见 `系统架构设计.md`
2. **后端基础框架搭建**
   - FastAPI框架配置
   - SQLAlchemy数据库模型
   - 配置管理系统
3. **数据库模型设计**
   - 材料库表 (materials)
   - 工艺库表 (processes, cutting_parameters)
   - 图纸表 (drawings)
   - 报价表 (quotes, quote_items, process_routes)
4. **OCR识别服务**
   - 集成Ollama Vision API
   - 支持PDF和图片识别
   - 智能提取图纸信息

### ⏳ 进行中
1. **图纸管理API** - 创建上传、识别、编辑API
2. **工艺库数据导入** - 导入常见材料和工艺数据

### 📝 待开发
1. 材料库和工艺库管理API
2. 报价计算引擎（解析Excel公式）
3. 智能工艺路线推荐
4. 报价单生成和导出
5. 前端界面开发
6. 完整流程测试

---

## 📊 数据库设计

### 核心表结构

#### 1. 图纸表 (drawings)
- drawing_number: 图号
- customer_name: 客户名称
- material: 材质
- ocr_data: OCR识别数据（JSON）
- file_path: 文件路径

#### 2. 材料库 (materials)
- material_code: 材料代码
- material_name: 材料名称
- density: 密度
- price_per_kg: 价格/kg

#### 3. 工艺库 (processes)
- process_code: 工艺代码
- process_name: 工艺名称
- hourly_rate: 工时费率
- setup_time: 装夹时间

#### 4. 报价表 (quotes)
- quote_number: 报价单号
- total_amount: 报价总额
- details: 报价明细（JSON）
- status: 状态

---

## 🔧 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy 2.0
- **OCR引擎**: Ollama + Qwen3-VL
- **数据验证**: Pydantic V2

### 前端（待开发）
- **框架**: React 18
- **UI库**: Ant Design 5.x
- **状态管理**: Zustand / React Query

---

## 📖 API文档

启动后端服务后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🔍 测试案例

项目包含一个真实的客户案例：
- 文件: `8001-0003095捻钞辊轴CPN01802-不锈钢材质.pdf`
- 产品: 捻钞辊轴
- 材质: SUS303不锈钢
- 客户: 永州雅力德科技有限公司

可用于测试OCR识别和报价计算功能。

---

## 🛠️ 开发指南

### 添加新的API端点

1. 在 `api/` 目录下创建路由文件
2. 在 `services/` 目录下创建业务逻辑
3. 在 `main.py` 中注册路由

### 添加新的数据库模型

1. 在 `models/` 目录下创建模型文件
2. 在 `models/__init__.py` 中导出
3. 运行数据库初始化

### 报价公式配置

报价公式位于 `报价公式.xls`，以"创怡兴"工作表为准：
- 材料成本 = 重量 × 材料单价 × (1 + 不良率) × (1 + 材管率)
- 加工成本 = Σ(各工序成本)
- 总价 = 材料成本 + 加工成本 + 管理费 + 利润

---

## 📝 环境变量配置

复制 `.env.example` 为 `.env` 并配置：

```env
# 数据库配置
DATABASE_URL=sqlite:///./quote_system.db

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_VISION_MODEL=qwen3-vl:7b

# JWT配置
SECRET_KEY=your-secret-key-change-in-production

# 文件上传配置
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=50
```

---

## 🤝 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

---

## 📮 联系方式

如有问题或建议，请联系项目维护者。

---

## 📄 许可证

本项目仅供内部使用。

---

## 🎉 致谢

- Ollama团队提供的Vision模型支持
- FastAPI社区的优秀框架
- Qwen团队的开源多模态模型

---

**Last Updated**: 2025-01-10
**Version**: 0.1.0 (Alpha)
