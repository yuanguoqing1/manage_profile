"""手动添加 email 和 phone 字段到用户表"""

from sqlalchemy import text
from app.db.session import engine

def add_user_fields():
    """添加 email 和 phone 字段"""
    with engine.connect() as conn:
        try:
            # 添加 email 字段
            conn.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(255) NULL"))
            print("✓ 添加 email 字段成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ email 字段已存在")
            else:
                print(f"✗ 添加 email 字段失败: {e}")
        
        try:
            # 添加 phone 字段
            conn.execute(text("ALTER TABLE user ADD COLUMN phone VARCHAR(255) NULL"))
            print("✓ 添加 phone 字段成功")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✓ phone 字段已存在")
            else:
                print(f"✗ 添加 phone 字段失败: {e}")
        
        try:
            # 为 email 创建索引
            conn.execute(text("CREATE INDEX ix_user_email ON user(email)"))
            print("✓ 创建 email 索引成功")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print("✓ email 索引已存在")
            else:
                print(f"✗ 创建 email 索引失败: {e}")
        
        conn.commit()
        print("\n数据库字段添加完成！")

if __name__ == "__main__":
    add_user_fields()
