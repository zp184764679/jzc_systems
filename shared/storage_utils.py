# shared/storage_utils.py
# -*- coding: utf-8 -*-
"""
存储管理工具

功能:
    - 初始化存储目录结构
    - 归档过期项目
    - 清理临时文件
    - 存储统计报告
    - 数据库同步
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared.file_storage_v2 import (
    EnterpriseFileStorage,
    ENTITY_TYPES,
    FILE_CATEGORIES,
    DEFAULT_STORAGE_PATH
)

logger = logging.getLogger(__name__)


class StorageManager:
    """存储管理器"""

    def __init__(self, base_path: str = None):
        self.storage = EnterpriseFileStorage(base_path)
        self.base_path = self.storage.base_path

    def init_storage_structure(self):
        """
        初始化完整的存储目录结构

        创建:
            storage/
            ├── active/
            │   └── {system}/{YYYY}/{MM}/
            ├── archive/{YYYY}/
            ├── temp/
            └── quarantine/
        """
        print("=" * 60)
        print("初始化企业级文件存储结构")
        print("=" * 60)
        print(f"存储根目录: {self.base_path}")
        print()

        now = datetime.now()
        year = now.year
        month = now.month

        created_dirs = []

        # 1. 创建主目录
        main_dirs = ["active", "archive", "temp", "quarantine"]
        for d in main_dirs:
            path = os.path.join(self.base_path, d)
            Path(path).mkdir(parents=True, exist_ok=True)
            created_dirs.append(path)
            print(f"✓ 创建目录: {d}/")

        # 2. 创建各系统的活跃存储目录
        print("\n创建系统目录结构:")
        for system, entity_types in ENTITY_TYPES.items():
            system_path = os.path.join(self.base_path, "active", system, str(year), f"{month:02d}")
            Path(system_path).mkdir(parents=True, exist_ok=True)
            created_dirs.append(system_path)
            print(f"  ✓ {system}/")

            # 为每个实体类型创建示例目录结构
            for entity_type in entity_types[:2]:  # 只创建前两个作为示例
                entity_path = os.path.join(system_path, entity_type, "_template")
                Path(entity_path).mkdir(parents=True, exist_ok=True)

                # 创建文件分类目录
                for category in FILE_CATEGORIES[:5]:  # 创建主要分类
                    cat_path = os.path.join(entity_path, category)
                    Path(cat_path).mkdir(parents=True, exist_ok=True)

                print(f"      ✓ {entity_type}/_template/")

        # 3. 创建归档目录
        archive_path = os.path.join(self.base_path, "archive", str(year))
        Path(archive_path).mkdir(parents=True, exist_ok=True)
        print(f"\n✓ 创建归档目录: archive/{year}/")

        # 4. 创建 README 文件
        self._create_readme()

        print(f"\n{'=' * 60}")
        print(f"初始化完成! 共创建 {len(created_dirs)} 个目录")
        print("=" * 60)

        return created_dirs

    def _create_readme(self):
        """创建 README 文件说明目录结构"""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        readme_content = f"""# JZC 企业级文件存储系统

## 目录结构

```
storage/
├── active/                           # 活跃文件（当前使用）
│   └── {{system}}/{{YYYY}}/{{MM}}/{{entity_type}}/{{entity_id}}/
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
│       └── versions/{{file_id}}/v1.0/  # 历史版本
│
├── archive/                          # 归档文件（已完结项目）
│   └── {{YYYY}}/{{system}}/{{entity_type}}/{{entity_id}}.tar.gz
│
├── temp/                             # 临时文件（7天后自动清理）
│   └── {{date}}/{{session_id}}/
│
└── quarantine/                       # 隔离区（30天后清理）
    └── {{date}}/
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
{{YYYYMMDD}}_{{file_id}}_{{original_name}}.{{ext}}
```

示例: `20251218_a1b2c3d4_采购合同.pdf`

## 访问URL

```
/storage/active/{{system}}/{{YYYY}}/{{MM}}/{{entity_type}}/{{entity_id}}/{{category}}/{{filename}}
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
创建时间: {created_at}
"""

        readme_path = os.path.join(self.base_path, "README.md")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)

        print(f"✓ 创建 README.md")

    def cleanup_temp(self, days: int = 7) -> dict:
        """清理临时文件"""
        print(f"\n清理 {days} 天前的临时文件...")
        result = self.storage.cleanup_temp_files(days)
        print(f"删除 {result['deleted_files']} 个文件, 释放 {result['deleted_size'] / 1024 / 1024:.2f} MB")
        return result

    def cleanup_quarantine(self, days: int = 30) -> dict:
        """清理隔离文件"""
        print(f"\n清理 {days} 天前的隔离文件...")
        result = self.storage.cleanup_quarantine(days)
        print(f"删除 {result['deleted_files']} 个文件, 释放 {result['deleted_size'] / 1024 / 1024:.2f} MB")
        return result

    def get_stats(self, verbose: bool = True) -> dict:
        """获取存储统计"""
        stats = self.storage.get_storage_stats()

        if verbose:
            print("\n" + "=" * 60)
            print("存储统计报告")
            print("=" * 60)
            print(f"总文件数: {stats['total_files']:,}")
            print(f"总大小: {stats['total_size'] / 1024 / 1024 / 1024:.2f} GB")

            print("\n按状态统计:")
            for status, data in stats['by_status'].items():
                if data['files'] > 0:
                    print(f"  {status}: {data['files']:,} 文件, {data['size'] / 1024 / 1024:.2f} MB")

            print("\n按系统统计:")
            for system, data in stats['by_system'].items():
                print(f"  {system}: {data['files']:,} 文件, {data['size'] / 1024 / 1024:.2f} MB")

        return stats

    def generate_report(self, output_path: str = None) -> str:
        """生成存储报告"""
        stats = self.get_stats(verbose=False)

        report = {
            "generated_at": datetime.now().isoformat(),
            "storage_path": self.base_path,
            "summary": {
                "total_files": stats['total_files'],
                "total_size_bytes": stats['total_size'],
                "total_size_gb": round(stats['total_size'] / 1024 / 1024 / 1024, 2)
            },
            "by_status": stats['by_status'],
            "by_system": stats['by_system']
        }

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"报告已保存到: {output_path}")

        return json.dumps(report, ensure_ascii=False, indent=2)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='JZC 企业级文件存储管理工具')
    parser.add_argument('command', choices=['init', 'cleanup', 'stats', 'report'],
                        help='执行的命令')
    parser.add_argument('--path', default=DEFAULT_STORAGE_PATH,
                        help='存储根目录路径')
    parser.add_argument('--temp-days', type=int, default=7,
                        help='临时文件保留天数')
    parser.add_argument('--quarantine-days', type=int, default=30,
                        help='隔离文件保留天数')
    parser.add_argument('--output', help='报告输出路径')

    args = parser.parse_args()

    manager = StorageManager(args.path)

    if args.command == 'init':
        manager.init_storage_structure()

    elif args.command == 'cleanup':
        manager.cleanup_temp(args.temp_days)
        manager.cleanup_quarantine(args.quarantine_days)

    elif args.command == 'stats':
        manager.get_stats()

    elif args.command == 'report':
        output = args.output or os.path.join(
            args.path,
            f"storage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        manager.generate_report(output)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
