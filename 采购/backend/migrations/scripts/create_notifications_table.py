# -*- coding: utf-8 -*-
"""
创建通知表
Create notifications table
"""
from app import app
from extensions import db
from sqlalchemy import text

def create_notifications_table():
    with app.app_context():
        try:
            # 创建notifications表
            print("开始创建notifications表...")

            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    recipient_id BIGINT UNSIGNED NOT NULL,
                    recipient_type VARCHAR(20) NOT NULL DEFAULT 'supplier',
                    notification_type VARCHAR(50) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    related_type VARCHAR(50) NULL,
                    related_id BIGINT UNSIGNED NULL,
                    data TEXT NULL,
                    is_read TINYINT(1) NOT NULL DEFAULT 0,
                    read_at DATETIME NULL,
                    is_sent TINYINT(1) NOT NULL DEFAULT 0,
                    sent_at DATETIME NULL,
                    send_method VARCHAR(20) NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    INDEX idx_notifications_recipient_id (recipient_id),
                    INDEX idx_notifications_type (notification_type),
                    INDEX idx_notifications_read (is_read),
                    INDEX idx_notifications_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))

            db.session.commit()
            print("✅ notifications表创建成功！")

            # 显示表结构
            result = db.session.execute(text("DESCRIBE notifications"))
            print("\n表结构：")
            for row in result:
                print(f"  {row[0]:20} {row[1]:30} {row[2]:10} {row[3]:10}")

            print("\n=== 通知系统数据库初始化完成 ===\n")

        except Exception as e:
            db.session.rollback()
            if "Table 'notifications' already exists" in str(e):
                print("ℹ️  notifications表已存在")
            else:
                print(f"❌ 创建表失败: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("通知系统数据库初始化")
    print("=" * 60)
    create_notifications_table()
