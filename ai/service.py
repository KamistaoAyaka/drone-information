"""
AI服务配置模块 - 支持多种AI服务商
注意：这些AI服务需要安装对应的Python包才能使用
"""
import requests
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

class AIService:
    """AI服务基类"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
    
    def call_api(self, prompt, model="default"):
        """调用AI API"""
        raise NotImplementedError
    
    def analyze_websites(self, query):
        """分析网站 - 返回相关网站列表"""
        prompt = f"""
        请帮我找出与无人机研究相关的网站，包括：
        1. 无人机研究公司官网
        2. 国内外科技媒体
        3. 行业资讯网站
        4. 学术研究机构
        
        请按照以下JSON格式输出：
        {{
            "websites": [
                {{
                    "name": "网站名称",
                    "url": "网站URL",
                    "type": "类型（公司/媒体/资讯/学术）",
                    "region": "地区（国内/国外）"
                }}
            ]
        }}
        
        查询主题：{query}
        """
        response = self.call_api(prompt)
        try:
            return json.loads(response)
        except:
            return {"websites": []}
    
    def classify_content(self, articles):
        """分类整理内容"""
        articles_json = json.dumps(articles, ensure_ascii=False)
        prompt = f"""
        请帮我分析以下无人机相关文章，进行分类整理：
        
        要求：
        1. 提取标题、内容、发布时间
        2. 智能分类：无人机类型（多旋翼/固定翼/VTOL/eVTOL等）
        3. 确定来源地区（国内/国外）
        4. 判断时间范围（一周内/一个月内/三个月内/一年内）
        5. 判断是否为前沿研究资讯
        6. 提取关键词
        
        请按照以下JSON格式输出：
        {{
            "results": [
                {{
                    "title": "标题",
                    "content": "内容摘要",
                    "publish_time": "发布时间",
                    "source": "来源网站",
                    "region": "国内/国外",
                    "drone_type": "无人机类型",
                    "time_range": "时间范围",
                    "is_cutting_edge": true/false,
                    "keywords": ["关键词1", "关键词2"]
                }}
            ]
        }}
        
        文章数据：
        {articles_json}
        """
        response = self.call_api(prompt)
        try:
            return json.loads(response)
        except:
            return {"results": []}
    
    def translate_text(self, text, target_lang="zh"):
        """翻译文本"""
        prompt = f"请将以下英文文本翻译成中文：\n\n{text}"
        return self.call_api(prompt)

    def _detect_language(self, text):
        """检测文本语言"""
        if not text:
            return 'zh'
        
        # 统计中文字符比例
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
        
        total_chars = len(text.strip())
        if total_chars == 0:
            return 'zh'
        
        chinese_ratio = chinese_chars / total_chars
        english_ratio = english_chars / total_chars
        
        # 如果中文字符超过30%，认为是中文
        if chinese_ratio > 0.3:
            return 'zh'
        # 如果英文字符超过50%，认为是英文
        elif english_ratio > 0.5:
            return 'en'
        # 默认中文
        return 'zh'
    
    def generate_summary(self, content, title=None):
        """为文章生成摘要（与原文语言保持一致）"""
        title_part = f"标题：{title}\n\n" if title else ""
        
        # 检测语言
        full_text = (title or "") + " " + (content or "")
        detected_lang = self._detect_language(full_text)
        lang_instruction = "使用中文" if detected_lang == 'zh' else "使用英文"
        
        # 根据内容长度调整提示词
        if len(content.strip()) < 100:
            if detected_lang == 'zh':
                prompt = f"""{title_part}请根据以下标题或简短内容，生成一个更详细的中文摘要（100-200字），要求：
1. 用合理的语言扩展内容
2. 保持原文核心信息
3. 必须使用中文输出
4. 准确客观

标题/内容：
{content}

请直接输出摘要，不要有其他说明。"""
            else:
                prompt = f"""{title_part}Generate a detailed English summary (100-200 words) based on the following title or brief content, requirements:
1. Expand content with reasonable language
2. Maintain core information from the original text
3. Must output in English
4. Accurate and objective

Title/Content:
{content}

Please output the summary directly without additional explanations."""
        else:
            if detected_lang == 'zh':
                prompt = f"""{title_part}请为以下文章生成一个简明扼要的中文摘要（100-200字），要求：
1. 概括文章的主要内容
2. 突出重点信息
3. 必须使用中文输出
4. 准确客观，不添加主观内容

文章内容：
{content}

请直接输出摘要，不要有其他说明。"""
            else:
                prompt = f"""{title_part}Generate a concise English summary (100-200 words) for the following article, requirements:
1. Summarize the main content of the article
2. Highlight key information
3. Must output in English
4. Accurate and objective, no subjective content

Article content:
{content}

Please output the summary directly without additional explanations."""
        
        return self.call_api(prompt)


class OpenAIService(AIService):
    """OpenAI服务"""
    
    def __init__(self, api_key):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI模块未安装。请运行: pip install openai")
        super().__init__(api_key)
        self.client = openai.OpenAI(api_key=api_key)
    
    def call_api(self, prompt, model="gpt-4o-mini"):
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的数据分析助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            result = response.choices[0].message.content.strip()
            if not result:
                raise Exception("OpenAI返回空内容")
            return result
        except openai.AuthenticationError:
            raise Exception("OpenAI API Key无效或认证失败")
        except openai.RateLimitError:
            raise Exception("OpenAI API调用超限，请稍后重试")
        except openai.APIError as e:
            raise Exception(f"OpenAI API错误: {str(e)}")
        except Exception as e:
            raise Exception(f"OpenAI请求失败: {str(e)}")


class DeepSeekService(AIService):
    """DeepSeek服务 - 国产大模型"""
    
    def __init__(self, api_key):
        super().__init__(api_key)
        self.base_url = "https://api.deepseek.com"
    
    def call_api(self, prompt, model="deepseek-chat"):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的数据分析助手。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        try:
            print(f"[DeepSeek] 请求URL: {url}")
            print(f"[DeepSeek] 模型: {model}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"[DeepSeek] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    content = message.get('content', '').strip()
                    if content:
                        print(f"[DeepSeek] 翻译成功")
                        return content
                raise Exception("DeepSeek返回空内容")
            
            error_msg = f"DeepSeek API错误 {response.status_code}"
            try:
                result = response.json()
                error_info = result.get('error', {})
                error_msg = error_info.get('message', error_msg)
            except:
                pass
                
            print(f"[DeepSeek] 错误: {error_msg}")
            
            if 'invalid' in error_msg.lower() or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                raise Exception(f"DeepSeek API Key无效: {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"DeepSeek网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"DeepSeek错误: {str(e)}")


class ClaudeService(AIService):
    """Anthropic Claude服务"""
    
    def __init__(self, api_key):
        super().__init__(api_key)
    
    def call_api(self, prompt, model="claude-3-sonnet-20240229"):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": model,
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            print(f"[Claude] 请求URL: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"[Claude] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('content', [])
                if content and len(content) > 0:
                    text = content[0].get('text', '').strip()
                    if text:
                        return text
                raise Exception("Claude返回空内容")
            
            error_msg = f"Claude API错误 {response.status_code}"
            try:
                result = response.json()
                error_info = result.get('error', {})
                error_msg = error_info.get('message', error_msg)
            except:
                pass
                
            if 'invalid' in error_msg.lower() or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                raise Exception(f"Claude API Key无效: {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Claude网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"Claude错误: {str(e)}")


class GeminiService(AIService):
    """Google Gemini服务"""
    
    def __init__(self, api_key):
        super().__init__(api_key)
    
    def call_api(self, prompt, model="gemini-1.5-flash"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params = {"key": self.api_key}
        data = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        
        try:
            print(f"[Gemini] 请求URL: {url}")
            response = requests.post(url, params=params, json=data, timeout=30)
            
            print(f"[Gemini] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get('candidates', [])
                if candidates and len(candidates) > 0:
                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if parts and len(parts) > 0:
                        text = parts[0].get('text', '').strip()
                        if text:
                            return text
                raise Exception("Gemini返回空内容")
            
            error_msg = f"Gemini API错误 {response.status_code}"
            try:
                result = response.json()
                error_info = result.get('error', {})
                error_msg = error_info.get('message', error_msg)
            except:
                pass
                
            if 'invalid' in error_msg.lower() or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                raise Exception(f"Gemini API Key无效: {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gemini网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"Gemini错误: {str(e)}")


class QwenService(AIService):
    """阿里云通义千问服务"""
    
    def __init__(self, api_key):
        super().__init__(api_key)
    
    def call_api(self, prompt, model="qwen-turbo"):
        # 使用OpenAI兼容模式
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        try:
            print(f"[Qwen] 请求URL: {url}")
            print(f"[Qwen] 模型: {model}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"[Qwen] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    text = message.get('content', '').strip()
                    if text:
                        return text
                raise Exception("通义千问返回空内容")
            
            error_msg = f"通义千问API错误 {response.status_code}"
            try:
                result = response.json()
                error_msg = result.get('error', {}).get('message', error_msg)
            except:
                pass
                
            if 'invalid' in error_msg.lower() or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                raise Exception(f"通义千问API Key无效: {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"通义千问网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"通义千问错误: {str(e)}")


class SparkService(AIService):
    """科大讯飞星火服务"""
    
    def __init__(self, api_key, api_secret=None):
        super().__init__(api_key)
        self.api_secret = api_secret
    
    def call_api(self, prompt, model="generalv3.5"):
        url = "https://spark-api-open.xf-yun.com/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4096
        }
        
        try:
            print(f"[Spark] 请求URL: {url}")
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"[Spark] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    content = message.get('content', '').strip()
                    if content:
                        return content
                raise Exception("星火API返回空内容")
            
            error_msg = f"星火API错误 {response.status_code}"
            try:
                result = response.json()
                error_info = result.get('error', {})
                error_msg = error_info.get('message', error_msg)
            except:
                pass
                
            if 'invalid' in error_msg.lower() or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                raise Exception(f"星火API Key无效: {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"星火网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"星火错误: {str(e)}")


class ZhipuService(AIService):
    """智谱AI服务"""
    
    def __init__(self, api_key):
        super().__init__(api_key)
    
    def call_api(self, prompt, model="glm-4-flash"):
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        
        try:
            print(f"[Zhipu] 请求URL: {url}")
            print(f"[Zhipu] 模型: {model}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            print(f"[Zhipu] 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get('choices', [])
                if choices and len(choices) > 0:
                    message = choices[0].get('message', {})
                    content = message.get('content', '').strip()
                    if content:
                        return content
                raise Exception("智谱AI返回空内容")
            
            error_msg = f"智谱AI错误 {response.status_code}"
            try:
                result = response.json()
                error_info = result.get('error', {})
                error_msg = error_info.get('message', error_msg)
            except:
                pass
                
            if 'invalid' in error_msg.lower() or 'key' in error_msg.lower() or 'auth' in error_msg.lower():
                raise Exception(f"智谱AI API Key无效: {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            raise Exception(f"智谱AI网络请求失败: {str(e)}")
        except Exception as e:
            raise Exception(f"智谱AI错误: {str(e)}")


class AIConfig:
    """AI服务配置"""
    
    providers = {
        'deepseek': {
            'name': 'DeepSeek',
            'service': DeepSeekService,
            'description': '深度求索，国产优秀大模型，性价比高',
            'type': 'paid',
            'models': ['deepseek-chat', 'deepseek-reasoner']
        },
        'openai': {
            'name': 'OpenAI',
            'service': OpenAIService,
            'description': 'GPT系列模型，功能强大',
            'type': 'paid',
            'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']
        },
        'claude': {
            'name': 'Claude',
            'service': ClaudeService,
            'description': 'Anthropic Claude，擅长长文本处理',
            'type': 'paid',
            'models': ['claude-3-sonnet', 'claude-3-opus', 'claude-3-haiku']
        },
        'gemini': {
            'name': 'Gemini',
            'service': GeminiService,
            'description': 'Google Gemini，多模态能力强',
            'type': 'paid',
            'models': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        },
        'qwen': {
            'name': '通义千问',
            'service': QwenService,
            'description': '阿里云AI，国内访问稳定',
            'type': 'paid',
            'models': ['qwen-turbo', 'qwen-plus', 'qwen-max']
        },
        'spark': {
            'name': '星火认知',
            'service': SparkService,
            'description': '科大讯飞AI，语音能力强',
            'type': 'paid',
            'models': ['generalv3.5', 'general']
        },
        'zhipu': {
            'name': '智谱AI',
            'service': ZhipuService,
            'description': 'GLM系列模型，性价比高',
            'type': 'paid',
            'models': ['glm-4', 'glm-4-flash', 'glm-3-turbo']
        }
    }
    
    @staticmethod
    def get_provider(provider_id):
        """获取AI服务商配置"""
        return AIConfig.providers.get(provider_id)
    
    @staticmethod
    def create_service(provider_id, api_key):
        """创建AI服务实例"""
        provider = AIConfig.providers.get(provider_id)
        if not provider:
            raise ValueError(f"未知的AI服务商: {provider_id}")
        
        service_class = provider['service']
        return service_class(api_key)
    
    @staticmethod
    def list_providers():
        """列出所有可用的AI服务商"""
        return [
            {'id': key, 'name': value['name'], 'description': value['description'], 'type': value['type']}
            for key, value in AIConfig.providers.items()
        ]
