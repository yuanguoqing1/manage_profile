"""手动执行数据库迁移脚本"""
import pymysql
import os

# 从环境变量或直接配置数据库连接
DB_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "manage_profile")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "123456")
DB_NAME = os.getenv("MYSQL_DB", "manage_profile")

def migrate():
    """执行迁移"""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    
    try:
        with conn.cursor() as cursor:
            # 检查 email 列是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'user' 
                AND COLUMN_NAME = 'email'
            """, (DB_NAME,))
            
            email_exists = cursor.fetchone()[0] > 0
            
            if not email_exists:
                print("添加 email 和 phone 字段...")
                cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(255) NULL")
                cursor.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(255) NULL")
                cursor.execute("CREATE INDEX ix_user_email ON user(email)")
                conn.commit()
                print("✓ 字段添加成功")
            else:
                print("✓ email 和 phone 字段已存在，跳过迁移")
                
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
