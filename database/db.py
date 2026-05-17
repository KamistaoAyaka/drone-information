import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import os

class Database:
    def __init__(self, db_path: str = "data/drone_scout.db"):
        self.db_path = db_path
        self._ensure_db_dir()
        self._init_db()

    def _ensure_db_dir(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT,
                url TEXT UNIQUE,
                image_url TEXT,
                source TEXT,
                publish_date TEXT,
                collected_date TEXT,
                region TEXT,
                drone_type TEXT,
                company TEXT,
                keywords TEXT,
                summary TEXT,
                features TEXT,
                method TEXT,
                is_processed INTEGER DEFAULT 0,
                simhash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 检查新字段是否已存在，如果不存在则添加
        cursor.execute("PRAGMA table_info(articles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'title_translated' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN title_translated TEXT")
        if 'summary_translated' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN summary_translated TEXT")
        if 'content_translated' not in columns:
            cursor.execute("ALTER TABLE articles ADD COLUMN content_translated TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                country TEXT,
                region TEXT,
                description TEXT,
                article_count INTEGER DEFAULT 0,
                latest_article_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_region ON articles(region)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_type ON articles(drone_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_company ON articles(company)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(publish_date)
        """)

        conn.commit()
        conn.close()

    def _is_valid_title(self, title: str) -> bool:
        """检查标题是否有效（不是哈希值）"""
        if not title or len(title.strip()) < 5:
            return False
        
        # 检查是否是32位十六进制字符串（MD5格式）
        title = title.strip()
        if len(title) == 32:
            try:
                int(title, 16)  # 尝试解析为十六进制
                return False  # 如果成功，说明是哈希值，不是有效标题
            except ValueError:
                pass
        
        # 检查是否是36位UUID格式
        if len(title) == 36 and title.count('-') == 4:
            return False
        
        # 检查是否包含至少2个空格或中文字符（表示有实际内容）
        if title.count(' ') >= 2 or any('\u4e00' <= c <= '\u9fff' for c in title):
            return True
        
        # 检查是否包含足够的字母（至少4个连续字母）
        if any(len(word) >= 4 for word in title.split()):
            return True
        
        return False

    def insert_article(self, article: Dict) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            title = article.get('title', '').strip()
            
            # 验证标题是否有效
            if not self._is_valid_title(title):
                print(f"跳过无效标题: {title[:50]}...")
                conn.close()
                return False
            
            if 'id' not in article:
                article['id'] = str(uuid.uuid4())

            cursor.execute("""
                INSERT OR IGNORE INTO articles
                (id, title, content, url, image_url, source, publish_date, collected_date,
                 region, drone_type, company, keywords, summary, features, method, simhash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article.get('id'),
                article.get('title'),
                article.get('content'),
                article.get('url'),
                article.get('image_url'),
                article.get('source'),
                article.get('publish_date'),
                article.get('collected_date', datetime.now().strftime('%Y-%m-%d')),
                article.get('region'),
                article.get('drone_type'),
                article.get('company'),
                json.dumps(article.get('keywords', []), ensure_ascii=False),
                article.get('summary'),
                article.get('features'),
                article.get('method'),
                article.get('simhash')
            ))

            conn.commit()
            inserted = cursor.rowcount > 0

            if inserted and article.get('company'):
                self._update_company_stats(article.get('company'), article.get('region'))

            return inserted
        except Exception as e:
            print(f"Error inserting article: {e}")
            return False
        finally:
            conn.close()

    def _update_company_stats(self, company_name: str, region: Optional[str] = None):
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
            result = cursor.fetchone()

            if result:
                cursor.execute("""
                    UPDATE companies
                    SET article_count = article_count + 1,
                        latest_article_date = datetime('now')
                    WHERE name = ?
                """, (company_name,))
            else:
                cursor.execute("""
                    INSERT INTO companies (id, name, region, article_count, latest_article_date)
                    VALUES (?, ?, ?, 1, datetime('now'))
                """, (str(uuid.uuid4()), company_name, region))

            conn.commit()
        finally:
            conn.close()

    def article_exists_by_url(self, url: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM articles WHERE url = ?", (url,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def article_exists_by_simhash(self, simhash: str, threshold: float = 0.85) -> bool:
        if not simhash:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, simhash FROM articles WHERE simhash IS NOT NULL")
        results = cursor.fetchall()
        conn.close()

        for article_id, existing_hash in results:
            if existing_hash and self._calculate_similarity(simhash, existing_hash) >= threshold:
                return True

        return False

    def _calculate_similarity(self, hash1: str, hash2: str) -> float:
        if not hash1 or not hash2:
            return 0.0

        try:
            h1 = int(hash1, 16) if hash1.startswith('0x') else int(hash1, 16)
            h2 = int(hash2, 16) if hash2.startswith('0x') else int(hash2, 16)

            xor = h1 ^ h2
            distance = bin(xor).count('1')
            similarity = 1.0 - (distance / 64.0)
            return similarity
        except:
            return 0.0

    def get_articles(
        self,
        region: Optional[str] = None,
        drone_type: Optional[str] = None,
        company: Optional[str] = None,
        keyword: Optional[str] = None,
        days: int = 90,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM articles WHERE 1=1"
        params = []

        if region:
            query += " AND region = ?"
            params.append(region)

        if drone_type:
            query += " AND drone_type = ?"
            params.append(drone_type)

        if company:
            query += " AND company = ?"
            params.append(company)

        if keyword:
            query += " AND (title LIKE ? OR content LIKE ? OR keywords LIKE ?)"
            keyword_pattern = f"%{keyword}%"
            params.extend([keyword_pattern, keyword_pattern, keyword_pattern])

        if days > 0:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            query += " AND publish_date >= ?"
            params.append(start_date)

        query += " ORDER BY publish_date DESC, created_at DESC"
        query += f" LIMIT {limit} OFFSET {offset}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        articles = []
        for row in rows:
            article = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'url': row[3],
                'image_url': row[4],
                'source': row[5],
                'publish_date': row[6],
                'collected_date': row[7],
                'region': row[8],
                'drone_type': row[9],
                'company': row[10],
                'keywords': json.loads(row[11]) if row[11] else [],
                'summary': row[12],
                'features': row[13],
                'method': row[14],
                'is_processed': bool(row[15])
            }
            
            # 处理翻译后的字段（检查是否有额外的字段）
            if len(row) > 16:
                article['title_translated'] = row[16]
            if len(row) > 17:
                article['summary_translated'] = row[17]
            if len(row) > 18:
                article['content_translated'] = row[18]
            
            articles.append(article)

        return articles
    
    def update_translation(self, article_id: str, title_translated: str = None, 
                          summary_translated: str = None, content_translated: str = None):
        """更新文章的翻译内容"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title_translated is not None:
            updates.append("title_translated = ?")
            params.append(title_translated)
        if summary_translated is not None:
            updates.append("summary_translated = ?")
            params.append(summary_translated)
        if content_translated is not None:
            updates.append("content_translated = ?")
            params.append(content_translated)
        
        if updates:
            params.append(article_id)
            cursor.execute(f"UPDATE articles SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        
        conn.close()

    def get_company_stats(self, region: Optional[str] = None, limit: int = 20) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()

        if region:
            cursor.execute("""
                SELECT c.name, c.region, c.article_count, c.latest_article_date
                FROM companies c
                WHERE c.region = ?
                ORDER BY c.article_count DESC
                LIMIT ?
            """, (region, limit))
        else:
            cursor.execute("""
                SELECT name, region, article_count, latest_article_date
                FROM companies
                ORDER BY article_count DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        companies = []
        for row in rows:
            companies.append({
                'name': row[0],
                'region': row[1],
                'article_count': row[2],
                'latest_article_date': row[3]
            })

        return companies

    def get_statistics(self) -> Dict:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]

        cursor.execute("""
            SELECT region, COUNT(*) as count
            FROM articles
            GROUP BY region
        """)
        region_stats = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT drone_type, COUNT(*) as count
            FROM articles
            WHERE drone_type IS NOT NULL
            GROUP BY drone_type
        """)
        type_stats = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT publish_date, COUNT(*) as count
            FROM articles
            WHERE publish_date >= date('now', '-30 days')
            GROUP BY publish_date
            ORDER BY publish_date DESC
        """)
        daily_stats = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            'total_articles': total_articles,
            'total_companies': total_companies,
            'region_stats': region_stats,
            'type_stats': type_stats,
            'daily_stats': daily_stats
        }

    def export_to_json(self, filepath: str, **filters):
        articles = self.get_articles(**filters, limit=10000)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)

    def export_to_csv(self, filepath: str, **filters):
        articles = self.get_articles(**filters, limit=10000)
        if not articles:
            return

        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=articles[0].keys())
            writer.writeheader()
            writer.writerows(articles)

    def update_article_summary(self, article_id: str, summary: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE articles
                SET summary = ?
                WHERE id = ?
            """, (summary, article_id))

            conn.commit()
            updated = cursor.rowcount > 0
            return updated
        except Exception as e:
            print(f"Error updating article summary: {e}")
            return False
        finally:
            conn.close()

    def batch_update_summaries(self, summaries: List[Dict]) -> int:
        """批量更新文章摘要，传入列表格式: [{'id': ..., 'summary': ...}]"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            updated_count = 0
            for item in summaries:
                cursor.execute("""
                    UPDATE articles
                    SET summary = ?
                    WHERE id = ?
                """, (item.get('summary'), item.get('id')))
                updated_count += cursor.rowcount

            conn.commit()
            return updated_count
        except Exception as e:
            print(f"Error batch updating summaries: {e}")
            return 0
        finally:
            conn.close()

    def clear_old_articles(self, days: int = 90):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM articles
            WHERE publish_date < date('now', ?)
        """, (f'-{days} days',))
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return deleted

    def clear_all_data(self):
        """清空所有文章和公司数据"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM articles")
            articles_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM companies")
            companies_deleted = cursor.rowcount
            
            conn.commit()
            return {
                'articles_deleted': articles_deleted,
                'companies_deleted': companies_deleted
            }
        except Exception as e:
            print(f"Error clearing data: {e}")
            conn.rollback()
            return {
                'articles_deleted': 0,
                'companies_deleted': 0
            }
        finally:
            conn.close()
