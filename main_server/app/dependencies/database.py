import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import logging  

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = str(os.getenv(
    "DATABASE_URL"
))

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
ViewBase = declarative_base()

# DB 세션 의존성 (Router에서 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_fields():
    """FIELDS 테이블에 기본 데이터를 삽입합니다."""
    try:
        with engine.begin() as conn:
            # FIELDS 테이블에 데이터가 있는지 확인
            result = conn.execute(text('SELECT COUNT(*) FROM "FIELDS";'))
            count = result.scalar()
            
            if count == 0:
                logger.info("FIELDS table is empty, inserting default data...")
                conn.execute(text("""
                    INSERT INTO "FIELDS" (field_id, field_name) VALUES
                    (1, 'Tech'),
                    (2, 'AI/Data'),
                    (3, 'Industry'),
                    (4, 'Daily'),
                    (5, 'Humanities'),
                    (6, 'Social');
                """))
                logger.info("Default fields inserted successfully")
            else:
                logger.info(f"FIELDS table already has {count} records, skipping initialization")
                
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize FIELDS table: {e}")
        raise

def init_view():
    with engine.connect() as conn:
        # POST_AGG Materialized View
        conn.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS "POST_AGG" AS 
            SELECT category,
                date,
                user_id,
                count(url) AS count
            FROM "POSTS"
            GROUP BY category, date, user_id
            ORDER BY date;
        """))
        
        # USER_STAT Materialized View
        conn.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS "USER_STAT" AS 
            SELECT u.user_id,
                p.category,
                u.created_at,
                count(p.url) AS count
            FROM "USER" u
            LEFT JOIN "POSTS" p ON u.user_id = p.user_id
            GROUP BY u.user_id, p.category, u.created_at
            ORDER BY (count(p.url)) DESC;
        """))
        
        # TRENDING_KEYWORDS_VIEW Materialized View
        conn.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS "TRENDING_KEYWORDS_VIEW" AS 
            SELECT map.keyword_id, k.keyword, count(post_id) AS count, p.field_id
            FROM "EXTERNAL_POSTS" AS p, "EXTERNAL_POSTS_KEYWORDS" AS map, "KEYWORDS" AS k
            WHERE p.id = map.post_id AND map.keyword_id = k.id 
            AND p.published_at >= DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '3 weeks' 
            GROUP BY map.keyword_id, k.keyword, p.field_id
            HAVING count(p.id) >= 2
            ORDER BY count DESC;
        """))
        
        # ARTICLES_MENTIONING_KEYWORDS_VIEW Materialized View
        conn.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS "ARTICLES_MENTIONING_KEYWORDS_VIEW" AS 
            SELECT p.id, p.title, p.source, p.url, p.summary, p.published_at, k.keyword, p.field_id
            FROM "EXTERNAL_POSTS" AS p, "EXTERNAL_POSTS_KEYWORDS" AS map, "KEYWORDS" AS k
            WHERE p.id = map.post_id AND map.keyword_id = k.id 
            AND map.keyword_id IN (SELECT keyword_id FROM "TRENDING_KEYWORDS_VIEW")
            AND p.published_at >= DATE_TRUNC('week', CURRENT_DATE) - INTERVAL '3 weeks' 
            ORDER BY p.id;
        """))
        
        # USERS_MENTIONING_KEYWORDS_VIEW Materialized View
        conn.execute(text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS "USERS_MENTIONING_KEYWORDS_VIEW" AS 
            SELECT p.field_id, pk_map.user_id, count(pk_map.url) AS count, u.name
            FROM "POST_KEYWORDS" AS pk_map, "TRENDING_KEYWORDS_VIEW" AS tk, "USER" AS u, "POSTS" AS p
            WHERE pk_map.keyword_id = tk.keyword_id
            AND pk_map.user_id = u.user_id
            AND p.url = pk_map.url
            GROUP BY p.field_id, pk_map.user_id, u.name
            ORDER BY count(pk_map.url) DESC;
        """))
        
        # USER_LEVEL View
        conn.execute(text("""
            CREATE OR REPLACE VIEW "USER_LEVEL" AS 
            SELECT stat.user_id AS user_id, 
                SUM(stat.count) AS total_count, 
                (SELECT level_name
                FROM "LEVEL_THRESHOLDS"
                WHERE min_post <= SUM(stat.count)
                ORDER BY min_post DESC LIMIT 1) AS level, 
                (SELECT message
                FROM "LEVEL_THRESHOLDS"
                WHERE min_post <= SUM(stat.count)
                ORDER BY min_post DESC LIMIT 1) AS message
            FROM "USER_STAT" AS stat
            GROUP BY stat.user_id;
        """))
        
        conn.commit()