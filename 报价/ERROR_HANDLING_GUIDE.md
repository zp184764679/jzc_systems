# 🛠️ 错误处理和日志记录优化指南

## 📋 概述

本文档说明如何在报价系统中使用统一的错误处理和日志记录。

---

## 🔧 错误处理

### 1. 使用自定义异常类

```python
from utils.error_handler import (
    BusinessException,
    NotFoundException,
    ValidationException,
    DatabaseException
)

# 示例：资源未找到
if not drawing:
    raise NotFoundException("图纸", drawing_id)

# 示例：业务逻辑错误
if price < 0:
    raise ValidationException("价格不能为负数")
```

### 2. 在main.py中注册异常处理器

```python
from utils.error_handler import (
    business_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    general_exception_handler
)
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

app = FastAPI()

# 注册异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(IntegrityError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
```

### 3. API错误响应格式

所有错误统一返回以下格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "用户友好的错误消息",
    "details": {
      "额外信息": "可选"
    }
  }
}
```

---

## 📝 日志记录

### 1. 初始化日志系统

在 `main.py` 启动时：

```python
from utils.logging_config import setup_logging

setup_logging(
    app_name="quotation",
    log_level="INFO",  # 生产环境使用INFO，开发环境可用DEBUG
    log_dir="logs",
    enable_file_logging=True,
    enable_console_logging=True
)
```

### 2. 在代码中使用日志

```python
from utils.logging_config import get_logger

logger = get_logger(__name__)

# 不同级别的日志
logger.debug("调试信息 - 详细的运行状态")
logger.info("✅ 操作成功完成")
logger.warning("⚠️  潜在问题，需要注意")
logger.error("❌ 操作失败")
logger.critical("🔥 严重错误，系统可能无法继续")
```

### 3. 记录安全事件

```python
from utils.logging_config import log_security_event

# 登录失败
log_security_event(
    event_type="login_failed",
    details={
        "username": username,
        "ip": request.client.host,
        "reason": "invalid_password"
    },
    severity="WARNING"
)

# 未授权访问
log_security_event(
    event_type="unauthorized_access",
    details={
        "user_id": user_id,
        "resource": "/api/admin/users",
        "action": "DELETE"
    },
    severity="ERROR"
)
```

### 4. 记录业务事件

```python
from utils.logging_config import log_business_event

# 创建报价单
log_business_event(
    event_type="quote_created",
    user_id=current_user.id,
    details={
        "quote_id": quote.id,
        "drawing_id": drawing.id,
        "total_price": quote.total_price
    }
)

# 图纸上传
log_business_event(
    event_type="drawing_uploaded",
    user_id=current_user.id,
    details={
        "drawing_id": drawing.id,
        "file_size": drawing.file_size,
        "file_type": drawing.file_type
    }
)
```

---

## 📂 日志文件说明

日志文件存储在 `logs/` 目录：

| 文件 | 说明 | 保留策略 |
|------|------|----------|
| `quotation.log` | 所有级别日志 | 10MB/文件，保留5个 |
| `quotation_error.log` | 仅ERROR及以上 | 10MB/文件，保留5个 |
| `security.log` | 安全相关事件 | 单独配置 |
| `business.log` | 业务事件审计 | 单独配置 |

---

## 🎯 最佳实践

### DO ✅

1. **使用结构化日志**
   ```python
   logger.info(f"用户登录成功: user_id={user.id}, ip={ip}")
   ```

2. **记录上下文信息**
   ```python
   logger.error(
       f"文件上传失败: file={filename}, size={size}, "
       f"user={user_id}, error={str(e)}"
   )
   ```

3. **使用适当的日志级别**
   - DEBUG: 开发调试信息
   - INFO: 正常业务流程
   - WARNING: 需要注意的情况
   - ERROR: 操作失败
   - CRITICAL: 系统级严重错误

4. **敏感信息脱敏**
   ```python
   # 错误示例
   logger.info(f"User password: {password}")  # ❌

   # 正确示例
   logger.info(f"User login: username={username}")  # ✅
   ```

### DON'T ❌

1. **不要记录敏感信息**
   - 密码
   - Token
   - 信用卡号
   - 私钥

2. **不要在循环中使用DEBUG日志**
   ```python
   # 错误示例
   for item in large_list:
       logger.debug(f"Processing {item}")  # ❌ 可能产生大量日志

   # 正确示例
   logger.info(f"开始处理 {len(large_list)} 个项目")  # ✅
   for item in large_list:
       process(item)
   logger.info("处理完成")
   ```

3. **不要吞掉异常**
   ```python
   # 错误示例
   try:
       risky_operation()
   except Exception:
       pass  # ❌ 悄悄吞掉异常

   # 正确示例
   try:
       risky_operation()
   except Exception as e:
       logger.error(f"操作失败: {e}", exc_info=True)  # ✅
       raise
   ```

---

## 🔍 监控和告警

### 建议配置

1. **实时监控**
   - 监控ERROR和CRITICAL级别日志
   - 设置告警阈值（如：5分钟内10个ERROR）

2. **日志聚合**
   - 考虑使用ELK Stack（Elasticsearch, Logstash, Kibana）
   - 或使用云服务（如：CloudWatch, Datadog）

3. **定期审计**
   - 每周审查安全日志
   - 每月分析业务日志趋势

---

## 📊 性能考虑

1. **异步日志写入**（当前配置已支持）
2. **日志轮转**（自动清理旧日志）
3. **避免过度日志**（生产环境关闭DEBUG）

---

## 🚀 快速开始

1. 复制 `utils/error_handler.py` 和 `utils/logging_config.py`
2. 在 `main.py` 中初始化
3. 在API中使用自定义异常
4. 运行测试验证

---

**更新时间**: 2025-12-01
