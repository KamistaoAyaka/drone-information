
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'data', 'drone_scout.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*60)
print("为中文文章补充摘要")
print("="*60)

# 中文文章和对应的摘要
chinese_articles = [
    {
        "title": "大疆发布全新Mavic 4无人机:搭载1英寸传感器和智能避障3.0",
        "summary": "大疆创新今日正式发布Mavic 4无人机，该机型采用全新设计的1英寸CMOS传感器，支持8K视频录制，配备全新的智能避障3.0系统，续航时间达到45分钟。该产品主要面向专业摄影师和航拍爱好者。"
    },
    {
        "title": "极飞科技推出新一代农业植保无人机P100 Pro",
        "summary": "极飞科技发布了新一代农业植保无人机P100 Pro，该机型具有更大的药箱容量和更长的续航时间，配备精准喷洒系统，可实现变量施药。全新AI处方图功能可以根据作物生长情况自动调整施药方案。"
    },
    {
        "title": "Wing开始在澳大利亚部署新一代配送无人机",
        "summary": "Alphabet旗下的Wing公司宣布开始在澳大利亚部署新一代配送无人机，该机型具有更大的载重能力和更远的配送范围，可以在30分钟内完成5公里范围内的配送服务。"
    },
    {
        "title": "亿航智能获得eVTOL型号合格证",
        "summary": "亿航智能宣布其自主研发的EH216-S无人驾驶载人航空器获得中国民用航空局颁发的型号合格证，这是全球首个获得此认证的无人驾驶载人eVTOL机型，标志着无人驾驶航空器商业化迈出重要一步。"
    }
]

# 更新数据库
updated = 0
for article_info in chinese_articles:
    cursor.execute(
        "UPDATE articles SET summary = ? WHERE title = ?",
        (article_info["summary"], article_info["title"])
    )
    if cursor.rowcount > 0:
        updated += 1
        print(f"✅ 更新: {article_info['title'][:40]}...")
    else:
        print(f"⚠️  未找到: {article_info['title'][:40]}...")

conn.commit()
print(f"\n✅ 共更新了 {updated} 篇中文文章的摘要")

# 验证
print("\n" + "="*60)
print("验证更新结果:")
print("="*60)

cursor.execute("SELECT title, summary FROM articles WHERE title LIKE ? OR title LIKE ? OR title LIKE ? OR title LIKE ?",
               ('%大疆%', '%极飞%', '%Wing%', '%亿航%'))

results = cursor.fetchall()
for title, summary in results:
    print(f"\n标题: {title[:40]}...")
    if summary and len(summary) > 10:
        print(f"摘要: {summary[:80]}...")
    else:
        print(f"❌ 摘要异常: {summary}")

conn.close()

print("\n" + "="*60)
print("修复完成！请刷新浏览器查看")
print("="*60)
