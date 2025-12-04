# 机加工报价系统 - 前端

基于 React 18 + Vite + Ant Design 5 的现代化前端界面。

## 技术栈

- **React 18** - 用户界面库
- **Vite** - 快速构建工具
- **Ant Design 5.x** - UI组件库
- **React Router DOM** - 路由管理
- **Zustand** - 状态管理
- **React Query** - 数据获取和缓存
- **Axios** - HTTP客户端
- **Day.js** - 日期处理

## 项目结构

```
frontend/
├── src/
│   ├── components/          # 公共组件
│   │   ├── AppHeader.jsx    # 顶部导航栏
│   │   └── AppSider.jsx     # 侧边栏菜单
│   ├── pages/               # 页面组件
│   │   ├── DrawingUpload.jsx      # 图纸上传页面
│   │   ├── DrawingList.jsx        # 图纸列表页面
│   │   ├── QuoteCreate.jsx        # 创建报价页面
│   │   ├── QuoteList.jsx          # 报价列表页面
│   │   ├── QuoteDetail.jsx        # 报价详情页面
│   │   ├── MaterialLibrary.jsx    # 材料库页面
│   │   └── ProcessLibrary.jsx     # 工艺库页面
│   ├── services/            # API服务
│   │   └── api.js           # 后端API接口封装
│   ├── styles/              # 样式文件
│   │   └── index.css        # 全局样式
│   ├── App.jsx              # 主应用组件
│   └── main.jsx             # 应用入口
├── index.html               # HTML模板
├── vite.config.js           # Vite配置
└── package.json             # 项目依赖

```

## 核心功能

### 1. 图纸管理
- **上传图纸**: 支持拖拽上传 PDF/图片格式
- **OCR识别**: 自动识别图纸信息
- **图纸列表**: 查看所有上传的图纸
- **信息编辑**: 修正OCR识别结果

### 2. 报价管理
- **创建报价**: 三步流程创建报价单
  - 步骤1: 输入批量参数
  - 步骤2: 查看报价明细
  - 步骤3: 保存并导出
- **报价列表**: 查看所有报价单
- **报价详情**: 查看完整报价信息
- **导出功能**: 导出Excel和PDF格式报价单

### 3. 数据库管理
- **材料库**: 查看和搜索材料信息
- **工艺库**: 查看和搜索加工工艺

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

### 预览生产构建

```bash
npm run preview
```

## API代理配置

开发环境下，Vite配置了代理将API请求转发到后端:

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
  '/uploads': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/drawings/upload` | 上传图纸 | 拖拽上传并OCR识别 |
| `/drawings/list` | 图纸列表 | 查看所有图纸 |
| `/quotes/create/:drawingId?` | 创建报价 | 创建新报价单 |
| `/quotes/list` | 报价列表 | 查看所有报价 |
| `/quotes/:quoteId` | 报价详情 | 查看报价详情 |
| `/library/materials` | 材料库 | 浏览材料数据 |
| `/library/processes` | 工艺库 | 浏览工艺数据 |

## 使用流程

### 完整报价流程

1. **上传图纸**
   - 访问"上传图纸"页面
   - 拖拽或点击上传PDF/图片
   - 等待上传完成

2. **OCR识别**
   - 点击"OCR识别"按钮
   - 等待10-30秒识别完成
   - 查看识别结果

3. **创建报价**
   - 点击"创建报价"按钮
   - 输入批量数量
   - 查看报价明细
   - 确认并保存

4. **导出报价单**
   - 导出Excel格式
   - 导出PDF格式
   - 发送给客户

## 特色功能

### 1. 实时上传进度
使用Progress组件显示文件上传进度，提升用户体验。

### 2. 异步数据缓存
使用React Query缓存API数据，减少不必要的请求。

### 3. 响应式设计
适配不同屏幕尺寸，移动端也能流畅使用。

### 4. 专业报价展示
- 成本卡片可视化
- 工序明细表格
- 总价突出显示
- 导出一键操作

## 环境变量

可以在`.env`文件中配置:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## 代码规范

- 使用ESLint进行代码检查
- 遵循React Hooks最佳实践
- 组件功能单一，便于维护
- API调用统一管理

## 性能优化

- Vite快速热更新
- React Query数据缓存
- 懒加载组件(可扩展)
- 生产构建代码压缩

## 浏览器兼容

支持现代浏览器:
- Chrome >= 87
- Firefox >= 78
- Safari >= 14
- Edge >= 88

## 后续优化方向

1. **用户认证**: 添加登录/注册功能
2. **权限管理**: 不同角色不同权限
3. **批量操作**: 批量上传、批量报价
4. **数据可视化**: 成本分析图表
5. **实时通知**: WebSocket推送OCR结果
6. **离线支持**: PWA离线访问
7. **主题切换**: 亮色/暗色模式
8. **国际化**: 多语言支持

## 故障排查

### 无法连接后端
- 确认后端服务已启动 (http://localhost:8000)
- 检查CORS配置
- 查看浏览器控制台错误

### OCR识别失败
- 确认Ollama服务运行正常
- 检查qwen3-vl模型已安装
- 查看后端日志

### 导出失败
- 确认后端PDF/Excel生成库已安装
- 检查浏览器下载权限
- 查看Network面板响应

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

私有项目，仅供内部使用。

---

**版本**: v0.2.0
**最后更新**: 2025-01-10
