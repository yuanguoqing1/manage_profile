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
            
            # 检查 diary 表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'diary'
            """, (DB_NAME,))
            
            diary_exists = cursor.fetchone()[0] > 0
            
            if not diary_exists:
                print("创建 diary 表...")
                cursor.execute("""
                    CREATE TABLE diary (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        title VARCHAR(200) DEFAULT '',
                        content TEXT,
                        mood VARCHAR(10) DEFAULT '😊',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX ix_diary_user_id (user_id),
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                print("✓ diary 表创建成功")
            else:
                print("✓ diary 表已存在，跳过创建")
            
            # 检查 album 表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'album'
            """, (DB_NAME,))
            
            album_exists = cursor.fetchone()[0] > 0
            
            if not album_exists:
                print("创建 album 表...")
                cursor.execute("""
                    CREATE TABLE album (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description VARCHAR(500) DEFAULT '',
                        cover_url VARCHAR(500) DEFAULT '',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX ix_album_user_id (user_id),
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                print("✓ album 表创建成功")
            else:
                print("✓ album 表已存在，跳过创建")
            
            # 检查 photo 表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'photo'
            """, (DB_NAME,))
            
            photo_exists = cursor.fetchone()[0] > 0
            
            if not photo_exists:
                print("创建 photo 表...")
                cursor.execute("""
                    CREATE TABLE photo (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        album_id INT NOT NULL,
                        user_id INT NOT NULL,
                        url VARCHAR(500) NOT NULL,
                        caption VARCHAR(200) DEFAULT '',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX ix_photo_album_id (album_id),
                        INDEX ix_photo_user_id (user_id),
                        FOREIGN KEY (album_id) REFERENCES album(id) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """)
                conn.commit()
                print("✓ photo 表创建成功")
            else:
                print("✓ photo 表已存在，跳过创建")
            
            # 检查 LDC 列是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'user' 
                AND COLUMN_NAME = 'LDC'
            """, (DB_NAME,))
            
            ldc_exists = cursor.fetchone()[0] > 0
            
            if not ldc_exists:
                print("添加 LDC 字段...")
                cursor.execute("ALTER TABLE user ADD COLUMN LDC INT DEFAULT 0")
                conn.commit()
                print("✓ LDC 字段添加成功")
            else:
                print("✓ LDC 字段已存在，跳过")
            
            # 检查 last_check_in 列是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'user' 
                AND COLUMN_NAME = 'last_check_in'
            """, (DB_NAME,))
            
            last_check_in_exists = cursor.fetchone()[0] > 0
            
            if not last_check_in_exists:
                print("添加 last_check_in 字段...")
                cursor.execute("ALTER TABLE user ADD COLUMN last_check_in DATE NULL")
                conn.commit()
                print("✓ last_check_in 字段添加成功")
            else:
                print("✓ last_check_in 字段已存在，跳过")
                
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
