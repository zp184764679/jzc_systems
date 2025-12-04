# 已知问题和解决方案

## 1. 负数limit参数500错误问题

### 问题描述
当调用 `/api/drawings?limit=-1` 等负数参数时，返回500错误而非预期的422验证错误。

### 根本原因
经过深入调试发现以下问题：
1. **PM2进程管理问题**: PM2无法正确重载Python模块，导致代码更新后不生效
2. **端口占用冲突**: 多个进程尝试绑定8001端口，导致PM2后端反复重启(119+次)
3. **FastAPI Query验证**: FastAPI 0.109.0版本的Query参数验证(`ge=1`)在某些情况下不生效

### 尝试的解决方案
- ✅ 添加Query验证参数 (`ge=1, le=1000`)
- ✅ 添加显式HTTPException验证
- ✅ 清除Python缓存(__pycache__)
- ✅ 使用venv Python替代系统Python
- ✅ 完全重启PM2进程
- ❌ 所有方案均因PM2进程管理问题未能生效

### 推荐解决方案

#### 方案1: 前端验证 (推荐)
在前端添加参数验证，防止发送无效请求：

```javascript
// 在API调用前验证参数
const fetchDrawings = async (skip, limit) => {
  if (limit < 1 || limit > 1000) {
    message.error('limit参数必须在1-1000之间');
    return;
  }
  if (skip < 0) {
    message.error('skip参数必须大于等于0');
    return;
  }

  return await api.get('/api/drawings', { params: { skip, limit } });
};
```

#### 方案2: 升级FastAPI版本
将FastAPI从0.109.0升级到最新版本(0.115.x)，新版本的参数验证更可靠。

#### 方案3: 使用Nginx反向代理
在Nginx层面添加参数验证，拦截无效请求。

### 影响评估
- **安全性**: ⚠️ 中等 - 用户可能发送无效参数导致数据库错误
- **用户体验**: ⚠️ 中等 - 错误信息不友好(500而非422)
- **系统稳定性**: ✅ 低 - 不影响系统正常功能

### 优先级
**中** - 建议优先实施方案1(前端验证)作为临时方案，长期考虑方案2(升级FastAPI)

---

## 2. 其他已知问题
(待补充)
