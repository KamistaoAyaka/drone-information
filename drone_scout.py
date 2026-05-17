import argparse
import sys
import json
import os
from datetime import datetime, timedelta
from database.db import Database
from scraper.collector import DataCollector
from scraper.cleaner import DataCleaner
from scraper.deduplicator import Deduplicator
from scraper.classifier import DroneClassifier
from config.sources import SOURCES, RSS_FEEDS, SEARCH_KEYWORDS

class DroneScoutCLI:
    def __init__(self):
        self.db = Database()
        self.collector = DataCollector(self.db)
        self.cleaner = DataCleaner()
        self.deduplicator = Deduplicator()
        self.classifier = DroneClassifier()

    def collect_all(self, args):
        print("=" * 60)
        print("无人机前沿情报采集系统")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        all_sources = SOURCES + RSS_FEEDS

        print(f"准备从 {len(all_sources)} 个数据源采集数据...")
        print()

        results = self.collector.collect_all(all_sources)

        if args.keyword:
            print(f"\n关键词搜索: {args.keyword}")
            keyword_results = self.collector.search_and_collect(args.keyword, max_results=20)
            results['keyword_search'] = keyword_results

        print()
        print("=" * 60)
        print("采集完成!")
        print(f"总计采集: {results.get('total', 0)} 篇文章")
        print("=" * 60)

        self._process_data()

    def search_data(self, args):
        print("=" * 60)
        print("数据检索")
        print("=" * 60)

        filters = {
            'region': args.region if hasattr(args, 'region') and args.region != 'all' else None,
            'drone_type': args.type if hasattr(args, 'type') and args.type != 'all' else None,
            'company': args.company if hasattr(args, 'company') else None,
            'keyword': args.keyword if hasattr(args, 'keyword') else None,
            'days': args.days if hasattr(args, 'days') else 90,
            'limit': args.limit if hasattr(args, 'limit') else 50
        }

        filters = {k: v for k, v in filters.items() if v is not None and v != ''}

        articles = self.db.get_articles(**filters)

        print(f"找到 {len(articles)} 篇相关文章\n")

        if articles:
            for i, article in enumerate(articles[:args.limit if hasattr(args, 'limit') else 50], 1):
                print(f"{i}. {article['title']}")
                print(f"   来源: {article['source']} | 公司: {article['company']} | 日期: {article['publish_date']}")
                print(f"   区域: {article['region']} | 类型: {article['drone_type'] or '未分类'}")
                if article['content']:
                    print(f"   摘要: {article['content'][:150]}...")
                print()

        return articles

    def export_data(self, args):
        print("=" * 60)
        print("数据导出")
        print("=" * 60)

        filters = {
            'region': args.region if args.region != 'all' else None,
            'drone_type': args.type if args.type != 'all' else None,
            'keyword': args.keyword,
            'days': args.days
        }
        filters = {k: v for k, v in filters.items() if v is not None and v != ''}

        output_file = args.output or f"drone_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{args.format}"

        if args.format == 'json':
            self.db.export_to_json(output_file, **filters)
        elif args.format == 'csv':
            self.db.export_to_csv(output_file, **filters)
        else:
            articles = self.db.get_articles(**filters, limit=10000)
            with open(output_file, 'w', encoding='utf-8') as f:
                for article in articles:
                    f.write(f"# {article['title']}\n")
                    f.write(f"来源: {article['source']}\n")
                    f.write(f"日期: {article['publish_date']}\n")
                    f.write(f"公司: {article['company']}\n")
                    f.write(f"区域: {article['region']}\n")
                    f.write(f"类型: {article['drone_type']}\n")
                    f.write(f"链接: {article['url']}\n")
                    f.write(f"内容: {article['content']}\n")
                    f.write("\n---\n\n")

        print(f"数据已导出至: {output_file}")
        print(f"导出格式: {args.format}")

    def show_statistics(self, args):
        print("=" * 60)
        print("数据统计")
        print("=" * 60)

        stats = self.db.get_statistics()

        print(f"\n总文章数: {stats['total_articles']}")
        print(f"涉及公司: {stats['total_companies']}")

        print("\n按区域分布:")
        for region, count in stats['region_stats'].items():
            percentage = (count / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
            print(f"  {region}: {count} 篇 ({percentage:.1f}%)")

        print("\n按无人机类型分布:")
        for drone_type, count in stats['type_stats'].items():
            percentage = (count / stats['total_articles'] * 100) if stats['total_articles'] > 0 else 0
            print(f"  {drone_type}: {count} 篇 ({percentage:.1f}%)")

        print("\n热门公司:")
        company_stats = self.db.get_company_stats(limit=10)
        for i, company in enumerate(company_stats, 1):
            print(f"  {i}. {company['name']} ({company['region']}): {company['article_count']} 篇")

    def show_companies(self, args):
        print("=" * 60)
        print("公司研究分类")
        print("=" * 60)

        region = args.region if args.region != 'all' else None
        companies = self.db.get_company_stats(region=region, limit=args.limit)

        if not companies:
            print("暂无数据")
            return

        for company in companies:
            print(f"\n{company['name']} ({company['region']})")
            print(f"  文章数量: {company['article_count']}")
            print(f"  最新文章: {company['latest_article_date'] or '未知'}")

            articles = self.db.get_articles(company=company['name'], limit=3)
            if articles:
                print(f"  最新文章:")
                for article in articles[:3]:
                    print(f"    - {article['title']}")

    def _process_data(self):
        print("\n开始数据处理...")

        articles = self.db.get_articles(limit=10000)
        print(f"待处理: {len(articles)} 篇文章")

        cleaned_articles = self.cleaner.batch_clean(articles)

        unique_articles = self.deduplicator.deduplicate_articles(cleaned_articles)

        classified_articles = self.classifier.batch_classify(unique_articles)

        for article in classified_articles:
            if article.get('is_processed'):
                continue

            self.db.insert_article(article)

        print("数据处理完成!")

    def init_sample_data(self):
        print("初始化示例数据...")
        
        # 1. 清空数据库
        print("正在清空数据库...")
        clear_result = self.db.clear_all_data()
        print(f"已删除 {clear_result['articles_deleted']} 篇文章，{clear_result['companies_deleted']} 个公司记录")
        
        # 2. 清理 Python 缓存文件
        print("正在清理缓存文件...")
        cache_cleaned = self._clean_pycache()
        if cache_cleaned > 0:
            print(f"已清理 {cache_cleaned} 个缓存目录")
        
        # 3. 添加示例数据
        print("\n正在添加示例数据...")
        sample_articles = [
            {
                'title': '大疆发布全新Mavic 4无人机:搭载1英寸传感器和智能避障3.0',
                'content': '大疆创新今日正式发布Mavic 4无人机,该机型采用全新设计的1英寸CMOS传感器,支持8K视频录制,配备全新的智能避障3.0系统,续航时间达到45分钟。该产品主要面向专业摄影师和航拍爱好者。',
                'url': 'https://www.dji.com/news/mavic-4',
                'source': '大疆官网',
                'publish_date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
                'region': '国内',
                'drone_type': '多旋翼',
                'company': '大疆创新',
                'keywords': json.dumps(['Mavic 4', '1英寸传感器', '智能避障', '8K视频'], ensure_ascii=False),
                'summary': '大疆创新今日正式发布Mavic 4无人机，该机型采用全新设计的1英寸CMOS传感器，支持8K视频录制，配备全新的智能避障3.0系统，续航时间达到45分钟。',
                'features': '1英寸传感器、智能避障3.0、45分钟续航、8K视频',
                'method': '全新光学设计,搭载AI芯片,机器视觉算法'
            },
            {
                'title': '极飞科技推出新一代农业植保无人机P100 Pro',
                'content': '极飞科技发布了新一代农业植保无人机P100 Pro,该机型具有更大的药箱容量和更长的续航时间,配备精准喷洒系统,可实现变量施药。全新AI处方图功能可以根据作物生长情况自动调整施药方案。',
                'url': 'https://www.xag.com/news/p100-pro',
                'source': '极飞官网',
                'publish_date': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'),
                'region': '国内',
                'drone_type': '多旋翼',
                'company': '极飞科技',
                'keywords': json.dumps(['P100 Pro', '农业植保', '精准喷洒', 'AI处方图'], ensure_ascii=False),
                'summary': '极飞科技发布了新一代农业植保无人机P100 Pro，该机型具有更大的药箱容量和更长的续航时间，配备精准喷洒系统，可实现变量施药。',
                'features': '大容量药箱、长续航、精准喷洒、变量施药',
                'method': 'AI处方图、精准农业技术、自动驾驶'
            },
            {
                'title': 'Wing开始在澳大利亚部署新一代配送无人机',
                'content': 'Alphabet旗下的Wing公司宣布开始在澳大利亚部署新一代配送无人机,该机型具有更大的载重能力和更远的配送范围,可以在30分钟内完成5公里范围内的配送服务。',
                'url': 'https://wing.com/news/new-drone-australia',
                'source': 'Wing官网',
                'publish_date': (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'),
                'region': '国外',
                'drone_type': '垂直起降',
                'company': 'Wing',
                'keywords': json.dumps(['配送无人机', 'Wing', '澳大利亚', '物流配送'], ensure_ascii=False),
                'summary': 'Alphabet旗下的Wing公司宣布开始在澳大利亚部署新一代配送无人机，该机型具有更大的载重能力和更远的配送范围，可以在30分钟内完成5公里范围内的配送服务。',
                'features': '大载重、远距离配送、30分钟配送',
                'method': '垂直起降技术、自动导航、路径规划'
            },
            {
                'title': 'DJI Announces New Mavic 3 Pro with Triple Camera System',
                'content': 'DJI unveiled the Mavic 3 Pro featuring a revolutionary triple camera system with Hasselblad main camera, providing unprecedented image quality. The drone features obstacle avoidance in all directions and 46-minute flight time.',
                'url': 'https://www.dji.com/news/mavic-3-pro',
                'source': 'DJI Official',
                'publish_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'region': '国外',
                'drone_type': '多旋翼',
                'company': '大疆创新',
                'keywords': json.dumps(['Mavic 3 Pro', 'Triple Camera', 'Hasselblad', 'obstacle avoidance'], ensure_ascii=False),
                'summary': 'DJI unveiled the Mavic 3 Pro featuring a revolutionary triple camera system with Hasselblad main camera, providing unprecedented image quality. The drone features obstacle avoidance in all directions and 46-minute flight time.',
                'features': '三摄系统、哈苏主摄、全向避障、46分钟续航',
                'method': '哈苏色彩科学、多摄像头协同、AI算法'
            },
            {
                'title': '亿航智能获得eVTOL型号合格证',
                'content': '亿航智能宣布其自主研发的EH216-S无人驾驶载人航空器获得中国民用航空局颁发的型号合格证,这是全球首个获得此认证的无人驾驶载人eVTOL机型,标志着无人驾驶航空器商业化迈出重要一步。',
                'url': 'https://www.ehang.com/news/eh216-sc',
                'source': '亿航官网',
                'publish_date': (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
                'region': '国内',
                'drone_type': '垂直起降',
                'company': '亿航智能',
                'keywords': json.dumps(['EH216-S', '型号合格证', 'eVTOL', '无人驾驶载人'], ensure_ascii=False),
                'summary': '亿航智能宣布其自主研发的EH216-S无人驾驶载人航空器获得中国民用航空局颁发的型号合格证，这是全球首个获得此认证的无人驾驶载人eVTOL机型。',
                'features': '无人驾驶、载人飞行、型号合格证',
                'method': 'eVTOL技术、自动驾驶、适航认证'
            },
        ]

        for article in sample_articles:
            article['collected_date'] = datetime.now().strftime('%Y-%m-%d')
            article['simhash'] = self.collector.generate_simhash(article['title'] + article['content'])
            self.db.insert_article(article)

        print(f"\n已添加 {len(sample_articles)} 篇示例文章")
        print("\n示例数据已初始化完成!")
    
    def _clean_pycache(self):
        """清理所有 __pycache__ 目录和 .pyc 文件"""
        import shutil
        count = 0
        
        # 遍历项目目录查找所有 __pycache__ 目录
        for root, dirs, files in os.walk('.'):
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(pycache_path)
                    count += 1
                except Exception as e:
                    print(f"无法删除 {pycache_path}: {e}")
        
        # 查找并删除所有 .pyc 文件
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.pyc'):
                    try:
                        os.remove(os.path.join(root, file))
                    except Exception as e:
                        pass
        
        return count


def main():
    cli = DroneScoutCLI()

    parser = argparse.ArgumentParser(
        description='无人机前沿情报采集系统',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    collect_parser = subparsers.add_parser('collect', help='采集数据')
    collect_parser.add_argument('--all', action='store_true', help='采集所有数据源')
    collect_parser.add_argument('--keyword', type=str, help='关键词搜索')
    collect_parser.add_argument('--source', type=str, help='指定数据源')

    search_parser = subparsers.add_parser('search', help='搜索数据')
    search_parser.add_argument('--region', type=str, default='all', choices=['all', '国内', '国外'], help='区域筛选')
    search_parser.add_argument('--type', type=str, default='all', help='无人机类型')
    search_parser.add_argument('--company', type=str, help='公司名称')
    search_parser.add_argument('--keyword', type=str, help='关键词')
    search_parser.add_argument('--days', type=int, default=90, help='时间范围(天)')
    search_parser.add_argument('--limit', type=int, default=50, help='结果数量限制')

    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('--format', type=str, default='json', choices=['json', 'csv', 'markdown'], help='导出格式')
    export_parser.add_argument('--output', type=str, help='输出文件路径')
    export_parser.add_argument('--region', type=str, default='all', help='区域筛选')
    export_parser.add_argument('--type', type=str, default='all', help='无人机类型')
    export_parser.add_argument('--keyword', type=str, help='关键词')
    export_parser.add_argument('--days', type=int, default=90, help='时间范围(天)')

    stats_parser = subparsers.add_parser('stats', help='显示统计信息')

    companies_parser = subparsers.add_parser('companies', help='显示公司分类')
    companies_parser.add_argument('--region', type=str, default='all', help='区域筛选')
    companies_parser.add_argument('--limit', type=int, default=20, help='显示数量')

    web_parser = subparsers.add_parser('web', help='启动Web服务')
    web_parser.add_argument('--host', type=str, default='0.0.0.0', help='监听地址')
    web_parser.add_argument('--port', type=int, default=5000, help='监听端口')

    init_parser = subparsers.add_parser('init', help='初始化示例数据')

    args = parser.parse_args()

    if not args.command:
        print("无人机前沿情报采集系统 v1.0")
        print("\n使用方法:")
        print("  python drone_scout.py collect --all       # 采集所有数据")
        print("  python drone_scout.py search              # 搜索数据")
        print("  python drone_scout.py export              # 导出数据")
        print("  python drone_scout.py stats               # 显示统计")
        print("  python drone_scout.py companies           # 显示公司分类")
        print("  python drone_scout.py web                 # 启动Web服务")
        print("  python drone_scout.py init                # 初始化示例数据")
        print("\n使用 --help 查看详细帮助")
        return

    if args.command == 'collect':
        cli.collect_all(args)
    elif args.command == 'search':
        cli.search_data(args)
    elif args.command == 'export':
        cli.export_data(args)
    elif args.command == 'stats':
        cli.show_statistics(args)
    elif args.command == 'companies':
        cli.show_companies(args)
    elif args.command == 'web':
        from api.routes import create_app
        app = create_app()
        print(f"\n启动Web服务: http://{args.host}:{args.port}")
        print("按 Ctrl+C 停止服务")
        app.run(host=args.host, port=args.port, debug=True)
    elif args.command == 'init':
        cli.init_sample_data()


if __name__ == '__main__':
    main()
