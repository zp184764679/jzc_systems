# 采购系统模块化重构指南

## 📋 概述

本文档说明了采购系统前端代码的模块化重构工作，包括新创建的工具函数和UI组件的使用方法。

## 🎯 重构目标

1. **消除代码重复** - 将15+处重复的格式化函数统一为工具模块
2. **提高可维护性** - 统一的组件和工具便于修改和维护
3. **改善代码质量** - 减少代码量，提高可读性

## 📁 新增文件结构

```
src/
├── utils/
│   └── formatters.js      # 格式化工具函数
└── components/
    └── ui/
        ├── Badge.jsx       # 徽章组件
        └── Modal.jsx       # 模态框组件
```

## 🛠️ 工具函数文档

### formatters.js

**位置**: `src/utils/formatters.js`

#### 1. formatDate(dateString, options = {})
日期时间格式化

**参数**:
- `dateString`: 日期字符串或Date对象
- `options`: 可选的格式化选项

**示例**:
```javascript
import { formatDate } from '../utils/formatters';

formatDate('2024-11-18T10:30:00')  // → '2024-11-18 10:30'
formatDate('2024-11-18', { hour: undefined })  // → '2024-11-18'
```

#### 2. formatSimpleCurrency(amount)
简单货币格式化（推荐）

**参数**:
- `amount`: 金额数字

**示例**:
```javascript
formatSimpleCurrency(1234.56)  // → '¥1,234.56'
formatSimpleCurrency(1000000)  // → '¥1,000,000.00'
```

#### 3. formatNumber(num, decimals = 0)
数字格式化（带千分位）

**示例**:
```javascript
formatNumber(1234567)  // → '1,234,567'
formatNumber(1234.567, 2)  // → '1,234.57'
```

#### 其他函数
- `formatCurrency(amount, currency, showSymbol)` - 完整货币格式化
- `formatDateOnly(dateString)` - 仅日期格式化
- `formatPercent(value, decimals)` - 百分比格式化
- `formatFileSize(bytes)` - 文件大小格式化
- `formatRelativeTime(dateString)` - 相对时间（如"2小时前"）
- `truncateText(text, maxLength, suffix)` - 文本截断

## 🎨 UI组件文档

### Badge组件

**位置**: `src/components/ui/Badge.jsx`

#### 基础用法
```javascript
import { Badge, StatusBadge } from '../components/ui/Badge';

// 基础徽章
<Badge variant="success" size="md">已批准</Badge>

// 状态徽章
<StatusBadge status="pending">待处理</StatusBadge>
```

**Props**:
- `variant`: default | success | warning | error | danger | info | primary
- `size`: sm | md | lg
- `status`: pending | approved | rejected
- `className`: 自定义CSS类名

### Modal组件

**位置**: `src/components/ui/Modal.jsx`

#### 基础模态框
```javascript
import { Modal } from '../components/ui/Modal';

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="标题"
  size="md"
>
  内容...
</Modal>
```

#### 确认对话框
```javascript
import { ConfirmModal } from '../components/ui/Modal';

<ConfirmModal
  isOpen={confirmOpen}
  onClose={() => setConfirmOpen(false)}
  onConfirm={handleConfirm}
  title="确认操作"
  message="您确定要执行此操作吗？"
  confirmText="确认"
  cancelText="取消"
  confirmVariant="danger"
/>
```

**Props**:
- `size`: sm | md | lg
- `confirmVariant`: danger | primary | success
- `closable`: boolean - 是否可关闭

## 📝 重构示例

### POApprovalPage.jsx (已完成)

#### 重构前
```javascript
// 本地定义的重复函数
const formatDate = (dateString) => {
  if (!dateString) return '-';
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatCurrency = (amount) => {
  return `¥${parseFloat(amount || 0).toFixed(2)}`;
};

// 使用
{formatDate(po.created_at)}
{formatCurrency(po.total_price)}

// window.confirm
if (!window.confirm('确定要确认这个采购订单吗？')) {
  return;
}
```

#### 重构后
```javascript
// 导入统一工具
import { formatDate, formatSimpleCurrency } from '../utils/formatters';
import { StatusBadge } from '../components/ui/Badge';
import { ConfirmModal } from '../components/ui/Modal';

// 直接使用
{formatDate(po.created_at)}
{formatSimpleCurrency(po.total_price)}

// 使用ConfirmModal组件
const [confirmModalOpen, setConfirmModalOpen] = useState(false);

<button onClick={() => setConfirmModalOpen(true)}>确认</button>

<ConfirmModal
  isOpen={confirmModalOpen}
  onClose={() => setConfirmModalOpen(false)}
  onConfirm={handleConfirm}
  title="管理员确认"
  message="确定要确认这个采购订单吗？"
/>
```

**效果**:
- 代码行数: ~350行 → 323行 (减少27行)
- 移除了3个重复函数定义
- 提高了可维护性和一致性

## 🚀 如何重构现有页面

### 步骤1: 分析页面
找出页面中的重复代码:
- 日期格式化: `toLocaleString`, `new Date().format()`
- 货币格式化: `toFixed(2)`, `toLocaleString`
- 模态框: `window.confirm`, `window.alert`

### 步骤2: 添加导入
```javascript
import { formatDate, formatSimpleCurrency } from '../utils/formatters';
import { StatusBadge } from '../components/ui/Badge';
import { ConfirmModal } from '../components/ui/Modal';
```

### 步骤3: 替换本地函数
删除本地定义的格式化函数，使用导入的工具函数替代。

### 步骤4: 测试和构建
```bash
cd ~/caigou-prod/frontend
npm run build
```

确保构建成功且功能正常。

## 📊 重构进度

### ✅ 已完成
- [x] 创建工具函数 `formatters.js`
- [x] 创建UI组件 `Badge.jsx`
- [x] 创建UI组件 `Modal.jsx`
- [x] 重构 `POApprovalPage.jsx`

### 🔜 待重构
建议按以下优先级重构:

1. **TransactionConfirmPage.jsx** (792行)
   - 9处货币格式化
   - 2处日期格式化

2. **SendPurchasePage.jsx** (816行)
   - 大量重复代码

3. **RequestDetail.jsx** (405行)
   - 格式化逻辑重复

## ⚠️ 注意事项

1. **保持功能一致** - 重构不应改变任何功能行为
2. **逐步进行** - 一次重构一个页面，便于测试和回滚
3. **测试完整性** - 重构后必须测试所有相关功能
4. **备份文件** - 重构前建议备份原始文件（.backup后缀）

## 🔗 相关文件

- 工具函数: `src/utils/formatters.js`
- UI组件: `src/components/ui/Badge.jsx`, `Modal.jsx`
- 重构示例: `src/pages/POApprovalPage.jsx`
- 本文档: `frontend/REFACTORING_GUIDE.md`

## 📞 支持

如有问题或建议，请联系开发团队。

---

**最后更新**: 2024-11-18  
**版本**: 1.0.0  
**作者**: Claude AI
