"""
数据库迁移脚本：为 projects 表添加 part_number 字段
运行方式: python migrations/add_part_number.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import SessionLocal, engine
from sqlalchemy import text


def upgrade():
    """添加 part_number 字段"""
    session = SessionLocal()
    try:
        # 检查字段是否已存在
        result = session.execute(text("""
            SELECT COUNT(*) as cnt FROM information_schema.columns
            WHERE table_schema = DATABASE()
            AND table_name = 'projects'
            AND column_name = 'part_number'
        """))
        row = result.fetchone()

        if row[0] > 0:
            print("字段 part_number 已存在，跳过迁移")
            return

        # 添加字段
        session.execute(text("""
            ALTER TABLE projects
            ADD COLUMN part_number VARCHAR(100) NULL COMMENT '部件番号'
        """))

        # 添加索引
        session.execute(text("""
            CREATE INDEX ix_projects_part_number ON projects (part_number)
        """))

        session.commit()
        print("成功添加 part_number 字段和索引")

    except Exception as e:
        session.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        session.close()


def downgrade():
    """回滚：删除 part_number 字段"""
    session = SessionLocal()
    try:
        # 删除索引
        try:
            session.execute(text("DROP INDEX ix_projects_part_number ON projects"))
        except:
            pass

        # 删除字段
        session.execute(text("ALTER TABLE projects DROP COLUMN part_number"))
        session.commit()
        print("成功删除 part_number 字段")

    except Exception as e:
        session.rollback()
        print(f"回滚失败: {e}")
        raise
    finally:
        session.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()
