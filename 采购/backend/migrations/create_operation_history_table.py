# migrations/create_operation_history_table.py
# -*- coding: utf-8 -*-
r"""
创建操作历史记录表

运行方法:
    cd C:\Users\Admin\Desktop\采购\backend
    .venv\Scripts\python.exe migrations\create_operation_history_table.py
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db


def create_table():
    """创建operation_history表"""
    from sqlalchemy import text

    sql = """
    CREATE TABLE IF NOT EXISTS operation_history (
        id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
        system VARCHAR(50) NOT NULL COMMENT '系统标识',
        module VARCHAR(100) NOT NULL COMMENT '模块名称',
        action VARCHAR(100) NOT NULL COMMENT '操作类型',
        target_type VARCHAR(100) DEFAULT NULL COMMENT '目标类型',
        target_id VARCHAR(100) DEFAULT NULL COMMENT '目标ID',
        target_name VARCHAR(255) DEFAULT NULL COMMENT '目标名称',
        operator_id BIGINT UNSIGNED DEFAULT NULL COMMENT '操作人ID',
        operator_name VARCHAR(100) DEFAULT NULL COMMENT '操作人姓名',
        operator_role VARCHAR(50) DEFAULT NULL COMMENT '操作人角色',
        ip_address VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
        old_value TEXT DEFAULT NULL COMMENT '旧值（JSON）',
        new_value TEXT DEFAULT NULL COMMENT '新值（JSON）',
        description TEXT DEFAULT NULL COMMENT '操作描述',
        extra_data TEXT DEFAULT NULL COMMENT '附加数据（JSON）',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        INDEX idx_system (system),
        INDEX idx_module (module),
        INDEX idx_action (action),
        INDEX idx_target (target_type, target_id),
        INDEX idx_operator (operator_id),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作历史记录';
    """

    try:
        from app import app
        with app.app_context():
            db.session.execute(text(sql))
            db.session.commit()
            print("✅ operation_history 表创建成功")
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        raise


def check_table_exists():
    """检查表是否存在"""
    from sqlalchemy import text

    sql = """
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_schema = DATABASE()
    AND table_name = 'operation_history';
    """

    try:
        from app import app
        with app.app_context():
            result = db.session.execute(text(sql)).scalar()
            return result > 0
    except Exception as e:
        print(f"检查表存在性失败: {str(e)}")
        return False


if __name__ == '__main__':
    if check_table_exists():
        print("operation_history 表已存在")
    else:
        create_table()
