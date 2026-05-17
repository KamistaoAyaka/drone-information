"""
静态网站自动化部署脚本
配合 GitHub Actions 使用，每日自动更新网站内容
"""
import os
import sys
import sqlite3
from datetime import datetime
from static_site_generator import StaticSiteGenerator

def main():
    print("=" * 60)
    print("🚀 无人机资讯静态网站自动部署")
    print("=" * 60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 检查数据库
    db_path = "data/drone_scout.db"
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在！")
        print(f"   路径: {os.path.abspath(db_path)}")
        return False
    
    # 检查文章数量
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM articles")
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"📊 数据库文章总数: {count}")
    
    if count == 0:
        print("⚠️ 数据库中没有文章！")
        return False
    
    # 生成静态网站
    print()
    print("🔄 正在生成静态网站...")
    generator = StaticSiteGenerator(
        db_path=db_path,
        output_dir="static_site"
    )
    generator.generate_all()
    
    # 检查输出
    output_dir = "static_site"
    if not os.path.exists(output_dir):
        print("❌ 静态网站生成失败！")
        return False
    
    # 统计文件数
    html_files = []
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    print()
    print("📈 生成统计:")
    print(f"   HTML文件总数: {len(html_files)}")
    print(f"   输出目录: {os.path.abspath(output_dir)}")
    
    # 检查关键文件
    required_files = [
        "index.html",
        "list.html",
        "assets/css/style.css"
    ]
    
    missing_files = []
    for file in required_files:
        path = os.path.join(output_dir, file)
        if not os.path.exists(path):
            missing_files.append(file)
    
    if missing_files:
        print()
        print("❌ 关键文件缺失:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print()
    print("✅ 静态网站生成成功！")
    print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("📋 下一步操作:")
    print("   1. 将 static_site 目录推送到 GitHub")
    print("   2. 在 Vercel/Netlify 连接 GitHub 仓库")
    print("   3. 设置自动部署")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
