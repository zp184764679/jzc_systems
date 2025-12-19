# JZC 企业级文件存储系统

## 目录结构

```
storage/
├── active/                           # 活跃文件（当前使用）
│   └── {system}/{YYYY}/{MM}/{entity_type}/{entity_id}/
│       ├── _meta.json                # 元数据索引
│       ├── documents/                # 文档
│       ├── drawings/                 # 图纸
│       ├── contracts/                # 合同
│       ├── invoices/                 # 发票
│       ├── photos/                   # 照片
│       ├── certificates/             # 证书/资质
│       ├── reports/                  # 报告
│       ├── exports/                  # 导出文件
│       ├── attachments/              # 附件
│       └── versions/{file_id}/v1.0/  # 历史版本
│
├── archive/                          # 归档文件（已完结项目）
│   └── {YYYY}/{system}/{entity_type}/{entity_id}.tar.gz
│
├── temp/                             # 临时文件（7天后自动清理）
│   └── {date}/{session_id}/
│
└── quarantine/                       # 隔离区（30天后清理）
    └── {date}/
```

## 系统代码

| 代码 | 系统名称 | 实体类型 |
|------|----------|----------|
| portal | 门户系统 | projects, announcements, documents |
| caigou | 采购系统 | suppliers, purchase_orders, rfq, contracts, invoices |
| quotation | 报价系统 | quotes, drawings, customers |
| hr | 人事系统 | employees, contracts, training, performance |
| crm | CRM系统 | customers, contacts, opportunities |
| scm | 仓库系统 | inventory, warehouses, shipments |
| shm | 出货系统 | shipments, deliveries, returns |
| eam | 设备系统 | equipment, maintenance, inspections |
| mes | 生产系统 | work_orders, production, quality |
| account | 账户系统 | users, roles, settings |
| shared | 共享资源 | templates, logos, exports |

## 文件命名规范

```
{YYYYMMDD}_{file_id}_{original_name}.{ext}
```

示例: `20251218_a1b2c3d4_采购合同.pdf`

## 访问URL

```
/storage/active/{system}/{YYYY}/{MM}/{entity_type}/{entity_id}/{category}/{filename}
```

## 自动维护

- 临时文件: 7天后自动删除
- 隔离文件: 30天后自动删除
- 项目归档: 完结6个月后可归档

## 注意事项

1. 请勿手动修改 `_meta.json` 文件
2. 版本文件存储在 `versions/` 目录下
3. 删除文件会先移动到 `quarantine/`
4. 归档后的文件为 `.tar.gz` 格式

---
创建时间: 2025-12-18 16:17:07
