from flask import Flask, request, jsonify, render_template
from database.db import Database
from scraper.classifier import DroneClassifier
import json
import requests
import time

try:
    from ai.service import AIConfig
    AI_CONFIG_AVAILABLE = True
except ImportError as e:
    AI_CONFIG_AVAILABLE = False
    AIConfig = None

try:
    import argostranslate.translate
    LOCAL_TRANSLATION_AVAILABLE = True
except ImportError:
    LOCAL_TRANSLATION_AVAILABLE = False

# AI服务实例缓存
ai_services = {
    'website': None,
    'classify': None,
    'translate': None
}

def get_ai_service(service_type, provider_id, api_key):
    """获取或创建AI服务实例"""
    if not AI_CONFIG_AVAILABLE:
        raise ValueError("AI模块未安装，请先安装AI依赖")
    
    global ai_services
    
    key = f"{service_type}_{provider_id}"
    if ai_services.get(key) is None:
        try:
            ai_services[key] = AIConfig.create_service(provider_id, api_key)
        except Exception as e:
            raise ValueError(f"创建AI服务失败: {str(e)}")
    
    return ai_services[key]

def translate_via_proxy(text, api_name):
    apis = {
        'youdao': {
            'url': f'https://fanyi.youdao.com/translate?&i={requests.utils.quote(text)}&doctype=json&version=2.1&keyfrom=fanyi.web',
            'parse': lambda data: data.get('translateResult', [])[0][0].get('tgt') if data.get('translateResult') else None
        },
        'baidu': {
            'url': f'https://fanyi-api.baidu.com/api/trans/vip/translate?q={requests.utils.quote(text)}&from=en&to=zh&appid=20210322000742361&salt=1435660288&sign=',
            'parse': lambda data: data.get('trans_result', [])[0].get('dst') if data.get('trans_result') else None
        },
        'tencent': {
            'url': f'https://fanyi.qq.com/api/translate?source=en&target=zh&sourceText={requests.utils.quote(text)}',
            'parse': lambda data: data.get('ret', [])[0].get('targetText') if data.get('ret') else None
        },
        'sogou': {
            'url': f'https://fanyi.sogou.com/api/translate?from=en&to=zh-CHS&text={requests.utils.quote(text)}',
            'parse': lambda data: data.get('data', {}).get('translation') if data.get('errorCode') == '0' else None
        },
        'google': {
            'url': f'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={requests.utils.quote(text)}',
            'parse': lambda data: ''.join([item[0] for item in data[0] if item[0]]) if data and data[0] else None
        },
        'mymemory': {
            'url': f'https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|zh-CN',
            'parse': lambda data: data.get('responseData', {}).get('translatedText') if data.get('responseStatus') == 200 else None
        },
        'argos': {
            'url': f'https://translate.argosopentech.com/translate?source=en&target=zh&text={requests.utils.quote(text)}',
            'parse': lambda data: data.get('translatedText') if data else None
        },
        'libre': {
            'url': f'https://libretranslate.com/translate?q={requests.utils.quote(text)}&source=en&target=zh',
            'parse': lambda data: data.get('translatedText') if data else None
        },
        'deepl': {
            'url': f'https://api-free.deepl.com/v1/translate?auth_key=&text={requests.utils.quote(text)}&source_lang=EN&target_lang=ZH',
            'parse': lambda data: data.get('translations', [])[0].get('text') if data and data.get('translations') else None
        }
    }
    
    api = apis.get(api_name)
    if not api:
        return None, '未知的API'
    
    try:
        response = requests.get(api['url'], timeout=5)
        response.encoding = 'utf-8'
        try:
            data = response.json()
        except:
            return None, '解析失败'
        
        result = api['parse'](data)
        if result:
            return result, api_name
        return None, '无结果'
    except requests.exceptions.Timeout:
        return None, '请求超时'
    except Exception as e:
        return None, str(e)


def translate_via_web(text, web_type):
    """通过网页抓取方式翻译"""
    from bs4 import BeautifulSoup
    import re
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        if web_type == 'youdao':
            # 有道翻译网页版
            url = f'https://fanyi.youdao.com/result?keyword={requests.utils.quote(text)}&lang=EN2ZH_CN'
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种选择器
            selectors = [
                '.gt .text',
                '.output .text',
                '#fanyi',
                '.trans-container',
            ]
            
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text_content = elem.get_text(strip=True)
                    if text_content and len(text_content) > 2:
                        return text_content, '有道词典'
            
            return None, '有道词典(解析失败)'
        
        elif web_type == 'baidu':
            # 百度翻译网页版
            url = f'https://fanyi.baidu.com/mtpeportal/web?query={requests.utils.quote(text)}&from=en&to=zh'
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种选择器
            selectors = [
                '.target-output',
                '.trans-right',
                '#original-trans',
            ]
            
            for selector in selectors:
                elem = soup.select_one(selector)
                if elem:
                    text_content = elem.get_text(strip=True)
                    if text_content and len(text_content) > 2:
                        return text_content, '百度翻译'
            
            return None, '百度翻译(解析失败)'
        
        elif web_type == 'google':
            # Google翻译网页版
            url = f'https://translate.google.com/?sl=en&tl=zh-CN&text={requests.utils.quote(text)}&op=translate'
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            elem = soup.select_one('.translation')
            if elem:
                text_content = elem.get_text(strip=True)
                if text_content:
                    return text_content, 'Google翻译'
            
            return None, 'Google翻译(解析失败)'
        
        return None, '未知的网页翻译类型'
    
    except requests.exceptions.Timeout:
        return None, '请求超时'
    except Exception as e:
        return None, f'错误: {str(e)[:50]}'

def create_app():
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, static_folder=os.path.join(base_dir, 'web'), template_folder=os.path.join(base_dir, 'web'))
    app.config['JSON_AS_ASCII'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # 启用模板自动重载

    db = Database()
    classifier = DroneClassifier()

    @app.route('/')
    def index():
        import hashlib
        import os
        html_path = os.path.join(base_dir, 'web', 'index.html')
        with open(html_path, 'rb') as f:
            content = f.read()
        etag = hashlib.md5(content).hexdigest()
        return render_template('index.html', v=etag)

    @app.route('/v2')
    def index_v2():
        return render_template('index.html', v=20260511)

    @app.route('/api_test')
    def api_test():
        return render_template('api_test.html')
    
    @app.route('/debug')
    def debug_page():
        return render_template('debug.html')

    @app.route('/api/articles')
    def get_articles():
        region = request.args.get('region', '')
        drone_type = request.args.get('type', '')
        company = request.args.get('company', '')
        keyword = request.args.get('keyword', '')
        days = int(request.args.get('days', 90))
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))

        filters = {
            'region': region if region and region != 'all' else None,
            'drone_type': drone_type if drone_type and drone_type != 'all' else None,
            'company': company if company else None,
            'keyword': keyword if keyword else None,
            'days': days,
            'limit': limit,
            'offset': offset
        }

        filters = {k: v for k, v in filters.items() if v is not None and v != ''}

        articles = db.get_articles(**filters)

        for article in articles:
            if isinstance(article.get('keywords'), str):
                try:
                    article['keywords'] = json.loads(article['keywords'])
                except:
                    article['keywords'] = []

        return jsonify({
            'success': True,
            'data': articles,
            'count': len(articles)
        })

    @app.route('/api/debug/articles')
    def debug_articles():
        """调试用：查看文章数据结构"""
        articles = db.get_articles(limit=5)
        return jsonify({
            'success': True,
            'count': len(articles),
            'articles': articles
        })
    
    @app.route('/api/debug/raw-articles')
    def debug_raw_articles():
        """调试用：查看数据库原始内容"""
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, LEFT(content, 200) as content_preview, length(content) as content_len, summary FROM articles LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'id': row[0],
                'title': row[1],
                'content_preview': row[2],
                'content_length': row[3],
                'summary': row[4]
            })
        
        return jsonify({
            'success': True,
            'count': len(results),
            'raw_articles': results
        })
    
    @app.route('/api/statistics')
    def get_statistics():
        stats = db.get_statistics()
        return jsonify({
            'success': True,
            'data': stats
        })
    
    @app.route('/api/articles/translation', methods=['POST'])
    def save_article_translation():
        try:
            data = request.get_json()
            
            article_id = data.get('article_id')
            title_translated = data.get('title_translated')
            summary_translated = data.get('summary_translated')
            content_translated = data.get('content_translated')
            
            if not article_id:
                return jsonify({
                    'success': False,
                    'error': '缺少文章ID'
                }), 400
            
            db.update_translation(
                article_id,
                title_translated=title_translated,
                summary_translated=summary_translated,
                content_translated=content_translated
            )
            
            return jsonify({
                'success': True,
                'message': '翻译保存成功'
            })
        except Exception as e:
            print(f"保存翻译错误: {e}")
            import traceback
            print(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/companies')
    def get_companies():
        region = request.args.get('region', '')
        limit = int(request.args.get('limit', 20))

        filters = {
            'region': region if region and region != 'all' else None,
            'limit': limit
        }

        companies = db.get_company_stats(**{k: v for k, v in filters.items() if v is not None and v != ''})

        for company in companies:
            articles = db.get_articles(company=company['name'], limit=3)
            company['recent_articles'] = [
                {
                    'title': a['title'],
                    'url': a['url'],
                    'date': a['publish_date']
                }
                for a in articles
            ]

        return jsonify({
            'success': True,
            'data': companies
        })

    @app.route('/api/classify')
    def classify_articles():
        filters = {
            'days': 90,
            'limit': 100
        }

        articles = db.get_articles(**filters)

        classified = classifier.batch_classify(articles)

        grouped = {
            'by_type': classifier.group_by_type(classified),
            'by_company': classifier.group_by_company(classified),
            'by_region': classifier.group_by_region(classified),
            'statistics': classifier.get_statistics(classified)
        }

        return jsonify({
            'success': True,
            'data': grouped
        })

    @app.route('/api/keywords')
    def get_keywords():
        filters = {
            'days': 90,
            'limit': 500
        }

        articles = db.get_articles(**filters)
        keywords = classifier.extract_keywords(articles, top_n=30)

        return jsonify({
            'success': True,
            'data': keywords
        })

    @app.route('/api/ai/providers', methods=['GET'])
    def get_ai_providers():
        """获取所有可用的AI服务商"""
        providers = AIConfig.list_providers()
        return jsonify({
            'success': True,
            'data': providers
        })

    @app.route('/api/ai/analyze_websites', methods=['POST'])
    def ai_analyze_websites():
        """使用AI分析相关网站"""
        data = request.get_json()
        query = data.get('query', '无人机研究')
        provider_id = data.get('provider', 'openai')
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请输入API Key'
            })
        
        try:
            service = get_ai_service('website', provider_id, api_key)
            result = service.analyze_websites(query)
            
            return jsonify({
                'success': True,
                'data': result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    @app.route('/api/ai/classify_content', methods=['POST'])
    def ai_classify_content():
        """使用AI分类整理内容"""
        data = request.get_json()
        articles = data.get('articles', [])
        provider_id = data.get('provider', 'openai')
        api_key = data.get('api_key', '')
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请输入API Key'
            })
        
        if not articles:
            return jsonify({
                'success': False,
                'error': '请提供文章数据'
            })
        
        try:
            service = get_ai_service('classify', provider_id, api_key)
            result = service.classify_content(articles)
            
            return jsonify({
                'success': True,
                'data': result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    @app.route('/api/ai/translate', methods=['POST'])
    def ai_translate():
        """使用AI翻译文本"""
        data = request.get_json()
        text = data.get('text', '')
        provider_id = data.get('provider', 'openai')
        api_key = data.get('api_key', '')
        
        print(f"[DEBUG] 开始翻译 - 服务商: {provider_id}")
        print(f"[DEBUG] API Key前10位: {api_key[:10] if api_key else '空'}")
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': '请输入API Key'
            })
        
        if not text:
            return jsonify({
                'success': False,
                'error': '请提供要翻译的文本'
            })
        
        try:
            print(f"[DEBUG] 创建服务实例...")
            provider = AIConfig.get_provider(provider_id)
            print(f"[DEBUG] 服务商信息: {provider['name'] if provider else '未知'}")
            
            service = get_ai_service('translate', provider_id, api_key)
            
            print(f"[DEBUG] 调用翻译API...")
            result = service.translate_text(text)
            
            print(f"[DEBUG] 翻译成功！")
            
            return jsonify({
                'success': True,
                'text': result,
                'api': provider['name']
            })
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] {str(e)}")
            print(f"[ERROR] 堆栈:\n{error_trace}")
            
            return jsonify({
                'success': False,
                'error': str(e),
                'trace': error_trace
            })

    @app.route('/api/ai/generate_summaries', methods=['POST'])
    def generate_summaries():
        """为没有摘要的文章批量生成摘要"""
        data = request.get_json()
        articles = data.get('articles', [])
        provider_id = data.get('provider')
        api_key = data.get('api_key', '')
        
        if not articles or len(articles) == 0:
            return jsonify({
                'success': True,
                'summaries': [],
                'message': '没有文章需要处理'
            })
        
        if not provider_id or not api_key:
            return jsonify({
                'success': False,
                'error': '请选择AI服务商并提供API Key'
            })
        
        try:
            print(f"[DEBUG] 开始为 {len(articles)} 篇文章生成摘要...")
            print(f"[DEBUG] AI Provider: {provider_id}")
            
            # 获取AI服务
            print(f"[DEBUG] 获取AI服务实例...")
            service = get_ai_service('classify', provider_id, api_key)
            print(f"[DEBUG] AI服务获取成功")
            
            # 遍历文章，为没有摘要的文章生成摘要
            results = []
            success_count = 0
            skip_count_summary = 0
            skip_count_content = 0
            error_count = 0
            
            for i, article in enumerate(articles):
                article_id = article.get('id')
                title = article.get('title', '')
                content = article.get('content', '')
                current_summary = article.get('summary', '')
                
                print(f"\n[DEBUG] 处理文章 {i+1}/{len(articles)}:")
                print(f"[DEBUG]   - ID: {article_id}")
                print(f"[DEBUG]   - 标题: {title[:50]}...")
                print(f"[DEBUG]   - 现有摘要: {'有' if current_summary else '无'} (长度: {len(current_summary) if current_summary else 0})")
                print(f"[DEBUG]   - 内容长度: {len(content) if content else 0}")
                
                # 如果已有摘要，跳过
                if current_summary and len(current_summary.strip()) > 10:
                    print(f"[DEBUG]   - 跳过: 已有有效摘要")
                    skip_count_summary += 1
                    results.append({
                        'id': article_id,
                        'summary': current_summary,
                        'generated': False
                    })
                    continue
                
                # 如果没有内容，尝试用标题生成；如果内容过短，也尝试处理
                if not content or len(content.strip()) < 20:
                    if not title or len(title.strip()) < 10:
                        print(f"[DEBUG]   - 跳过: 标题和内容都过短")
                        skip_count_content += 1
                        results.append({
                            'id': article_id,
                            'summary': title or '内容过短无法生成摘要',
                            'generated': False
                        })
                        continue
                    else:
                        # 用标题作为输入生成摘要
                        print(f"[DEBUG]   - 内容过短，尝试用标题生成摘要")
                        prompt_content = title
                else:
                    # 限制内容长度
                    prompt_content = content
                    if len(prompt_content) > 5000:
                        prompt_content = prompt_content[:5000]
                
                try:
                    print(f"[DEBUG]   - 调用AI生成摘要...")
                    summary = service.generate_summary(prompt_content, title)
                    
                    print(f"[DEBUG]   - AI返回: {summary[:50] if summary else '无内容'}...")
                    
                    if summary and len(summary.strip()) > 10:
                        print(f"[DEBUG]   - 成功！摘要长度: {len(summary.strip())}")
                        results.append({
                            'id': article_id,
                            'summary': summary.strip(),
                            'generated': True
                        })
                        success_count += 1
                        # 更新数据库
                        db.update_article_summary(article_id, summary.strip())
                    else:
                        print(f"[DEBUG]   - 失败：返回内容太短或为空")
                        error_count += 1
                        results.append({
                            'id': article_id,
                            'summary': title or '内容过短无法生成摘要',
                            'generated': False
                        })
                except Exception as e:
                    print(f"[WARNING]   - 生成摘要失败: {str(e)}")
                    import traceback
                    print(f"[DEBUG]   - 堆栈: {traceback.format_exc()}")
                    error_count += 1
                    results.append({
                        'id': article_id,
                        'summary': title or '内容过短无法生成摘要',
                        'generated': False,
                        'error': str(e)
                    })
            
            print(f"\n[DEBUG] ========================================")
            print(f"[DEBUG] 摘要生成完成统计:")
            print(f"[DEBUG]   - 总数: {len(articles)}")
            print(f"[DEBUG]   - 成功: {success_count}")
            print(f"[DEBUG]   - 跳过(已有摘要): {skip_count_summary}")
            print(f"[DEBUG]   - 跳过(内容过短): {skip_count_content}")
            print(f"[DEBUG]   - 错误: {error_count}")
            print(f"[DEBUG] ========================================")
            
            return jsonify({
                'success': True,
                'summaries': results,
                'generated_count': success_count,
                'total_count': len(articles)
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] {str(e)}")
            print(f"[ERROR] 堆栈:\n{error_trace}")
            
            return jsonify({
                'success': False,
                'error': str(e),
                'trace': error_trace
            })

    @app.route('/api/translate/proxy', methods=['POST'])
    def translate_proxy():
        data = request.get_json()
        text = data.get('text', '')
        api_name = data.get('api', 'auto')
        use_web_mode = data.get('web_mode', False)
        
        if not text:
            return jsonify({
                'success': False,
                'error': '文本不能为空'
            })
        
        if len(text) > 1000:
            text = text[:1000]
        
        # 如果指定了网页抓取模式
        if use_web_mode:
            web_order = ['youdao', 'baidu', 'google']
            for web_type in web_order:
                result, used_api = translate_via_web(text, web_type)
                if result:
                    return jsonify({
                        'success': True,
                        'text': result,
                        'api': used_api,
                        'mode': 'web'
                    })
            return jsonify({
                'success': False,
                'error': '网页抓取模式也失败了'
            })
        
        # 正常API模式
        apis_order = []
        if api_name == 'auto':
            apis_order = ['youdao', 'baidu', 'sogou', 'google', 'mymemory', 'argos', 'libre', 'deepl']
        else:
            apis_order = [api_name]
        
        for api in apis_order:
            result, used_api = translate_via_proxy(text, api)
            if result:
                return jsonify({
                    'success': True,
                    'text': result,
                    'api': used_api,
                    'mode': 'api'
                })
        
        # API模式失败，尝试网页抓取模式
        if api_name == 'auto':
            web_order = ['youdao', 'baidu', 'google']
            for web_type in web_order:
                result, used_api = translate_via_web(text, web_type)
                if result:
                    return jsonify({
                        'success': True,
                        'text': result,
                        'api': used_api,
                        'mode': 'web'
                    })
        
        return jsonify({
            'success': False,
            'error': '所有翻译方式均不可用'
        })

    @app.route('/api/translate/test', methods=['GET'])
    def translate_test():
        test_text = request.args.get('text', 'drone')
        api_name = request.args.get('api', 'auto')
        
        apis_order = []
        if api_name == 'auto':
            apis_order = ['youdao', 'baidu', 'sogou', 'google', 'mymemory', 'argos', 'libre', 'deepl']
        else:
            apis_order = [api_name]
        
        results = []
        for api in apis_order:
            result, used_api = translate_via_proxy(test_text, api)
            results.append({
                'api': used_api,
                'success': result is not None,
                'result': result,
                'error': None if result else used_api
            })
        
        return jsonify({
            'success': True,
            'results': results
        })

    @app.route('/api/translate', methods=['POST'])
    def translate_articles():
        if not LOCAL_TRANSLATION_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Local translation not available. Please install argostranslategui.'
            })

        data = request.get_json()
        articles = data.get('articles', [])

        translated = []
        success_count = 0
        fail_count = 0

        for article in articles:
            try:
                if article.get('title'):
                    article['translated_title'] = argostranslate.translate.translate(
                        article['title'], 'en', 'zh'
                    )
                    success_count += 1
                else:
                    article['translated_title'] = ''
            except Exception as e:
                article['translated_title'] = article.get('title', '')
                fail_count += 1

            try:
                if article.get('summary'):
                    article['translated_summary'] = argostranslate.translate.translate(
                        article['summary'], 'en', 'zh'
                    )
                else:
                    article['translated_summary'] = ''
            except Exception as e:
                article['translated_summary'] = article.get('summary', '')

            translated.append(article)

        return jsonify({
            'success': True,
            'data': translated,
            'stats': {
                'total': len(articles),
                'success': success_count,
                'failed': fail_count
            }
        })

    @app.route('/api/collect', methods=['POST'])
    def collect_data():
        from scraper.collector import DataCollector
        from config.sources import SOURCES, RSS_FEEDS, API_SOURCES
        from config.default_sources import get_default_sources

        collector = DataCollector(db)
        
        # 获取请求中的自定义网站（AI发现的）
        data = request.get_json() or {}
        custom_websites = data.get('custom_websites', [])
        
        # 获取默认数据源（NASA、俄罗斯航天局、欧空局等）
        default_sources = get_default_sources()
        
        # 合并所有数据源：默认数据源 + AI发现的网站 + 原有配置
        all_sources = default_sources + custom_websites + SOURCES + RSS_FEEDS + API_SOURCES
        
        # 去重（根据URL）
        seen_urls = set()
        unique_sources = []
        for source in all_sources:
            url = source.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        results = collector.collect_all(unique_sources)
        
        # 获取最近采集的文章（最后100篇）
        recent_articles = db.get_articles(limit=100)

        return jsonify({
            'success': True,
            'message': 'Data collection completed',
            'results': results,
            'articles': recent_articles,
            'sources_count': {
                'default': len(default_sources),
                'ai_discovered': len(custom_websites),
                'config': len(SOURCES) + len(RSS_FEEDS) + len(API_SOURCES),
                'total': len(unique_sources)
            }
        })
    


    @app.route('/api/export')
    def export_data():
        export_format = request.args.get('format', 'json')
        region = request.args.get('region', '')
        drone_type = request.args.get('type', '')
        keyword = request.args.get('keyword', '')
        days = int(request.args.get('days', 90))

        filters = {
            'region': region if region and region != 'all' else None,
            'drone_type': drone_type if drone_type and drone_type != 'all' else None,
            'keyword': keyword if keyword else None,
            'days': days,
            'limit': 1000
        }

        filters = {k: v for k, v in filters.items() if v is not None and v != ''}

        articles = db.get_articles(**filters)

        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': articles,
                'format': 'json'
            })
        elif export_format == 'csv':
            csv_data = []
            csv_data.append('标题,来源,公司,区域,类型,日期,URL')
            for article in articles:
                csv_data.append(f'"{article["title"]}","{article["source"]}","{article["company"]}","{article["region"]}","{article["drone_type"]}","{article["publish_date"]}","{article["url"]}"')

            return jsonify({
                'success': True,
                'data': '\n'.join(csv_data),
                'format': 'csv'
            })
        else:
            return jsonify({
                'success': True,
                'data': articles,
                'format': export_format
            })

    @app.route('/api/default_sources', methods=['GET'])
    def get_default_sources():
        """获取默认数据源列表"""
        try:
            from config.default_sources import get_default_sources
            sources = get_default_sources()
            return jsonify({
                'success': True,
                'data': sources
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/default_sources', methods=['POST'])
    def add_default_source():
        """添加默认数据源"""
        try:
            from config.default_sources import add_default_source
            data = request.get_json()
            
            if not data or 'name' not in data or 'url' not in data:
                return jsonify({
                    'success': False,
                    'message': '缺少必要字段：name 和 url'
                }), 400
            
            source = {
                'name': data['name'],
                'url': data['url'],
                'type': data.get('type', 'web'),
                'region': data.get('region', '国外'),
                'selectors': data.get('selectors', {
                    'list': 'article, .news-item, .post',
                    'title': 'h2, h3, .title',
                    'link': 'a',
                    'date': 'time, .date',
                    'content': '.content, .summary, p'
                }),
                'keywords': data.get('keywords', ['UAV', 'drone', 'unmanned'])
            }
            
            add_default_source(source)
            
            return jsonify({
                'success': True,
                'message': '数据源添加成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/default_sources/<source_name>', methods=['PUT'])
    def update_default_source(source_name):
        """更新默认数据源"""
        try:
            from config.default_sources import update_default_source
            data = request.get_json()
            
            update_default_source(source_name, data)
            
            return jsonify({
                'success': True,
                'message': '数据源更新成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    @app.route('/api/default_sources/<source_name>', methods=['DELETE'])
    def remove_default_source(source_name):
        """删除默认数据源"""
        try:
            from config.default_sources import remove_default_source
            
            remove_default_source(source_name)
            
            return jsonify({
                'success': True,
                'message': '数据源删除成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 500

    return app
