
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'drone_scout.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*60)
print("重置摘要 - 清除错误翻译的摘要")
print("="*60)

# 统计当前摘要情况
cursor.execute("SELECT COUNT(*) FROM articles WHERE summary IS NOT NULL AND summary != ''")
has_summary = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM articles")
total = cursor.fetchone()[0]

print(f"\n当前状态:")
print(f"  总文章数: {total}")
print(f"  有摘要的文章数: {has_summary}")

# 查看部分摘要
print("\n部分现有摘要示例:")
cursor.execute("SELECT title, summary FROM articles WHERE summary IS NOT NULL LIMIT 5")
for title, summary in cursor.fetchall():
    # 检测摘要语言
    has_chinese = any('\u4e00' <= c <= '\u9fff' for c in summary)
    has_english = any('a' <= c.lower() <= 'z' for c in summary)
    
    print(f"\n标题: {title[:40]}...")
    print(f"摘要: {summary[:60]}...")
    print(f"语言: {'中文' if has_chinese else '英文'}")

# 确认是否重置
confirm = input("\n确定要清除所有摘要并重新生成吗？(y/n): ").strip().lower()
if confirm == 'y':
    # 清除所有摘要
    cursor.execute("UPDATE articles SET summary = NULL")
    cursor.execute("UPDATE articles SET summary_translated = NULL")
    conn.commit()
    print(f"\n✅ 已清除所有摘要")
    
    print("\n现在请：")
    print("1. 启动服务器: python drone_scout.py web")
    print("2. 在网页上点击'生成摘要'按钮重新生成")
else:
    print("\n已取消操作")

conn.close()
