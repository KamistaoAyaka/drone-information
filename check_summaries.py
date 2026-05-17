
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'drone_scout.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*60)
print("检查文章摘要字段")
print("="*60)

cursor.execute("SELECT title, summary, summary_translated FROM articles")
rows = cursor.fetchall()

print("\n文章摘要情况:")
for i, (title, summary, summary_translated) in enumerate(rows, 1):
    print(f"\n{i}. 标题: {title[:40]}...")
    print(f"   原文摘要: {'有摘要' if summary else '无'}")
    print(f"   翻译摘要: {'有翻译' if summary_translated else '无'}")
    
    if summary:
        print(f"   摘要内容: {summary[:50]}...")

conn.close()
