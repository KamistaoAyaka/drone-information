import re
from typing import Dict, List, Optional, Tuple
from collections import Counter
import jieba

class DroneClassifier:
    def __init__(self):
        self.drone_type_keywords = {
            '多旋翼': [
                '四旋翼', '六旋翼', '八旋翼', '多旋翼', '四轴', '六轴', '八轴',
                'quadcopter', 'multirotor', 'multicopter', 'tricopter', 'octocopter',
                '消费级', '航拍无人机', '自拍无人机', 'mini drone', 'Mavic', 'Phantom', 'Inspire',
                '农业无人机', '植保无人机', '喷雾无人机', '喷洒', '打药'
            ],
            '固定翼': [
                '固定翼', 'fixed-wing', '固定翼无人机', '飞翼', '机翼',
                '长航时', '测绘', '遥感', '巡逻', '侦察机', 'spy plane',
                '高空长航时', 'HALE', 'MALE', '边境巡逻'
            ],
            '垂直起降': [
                '垂直起降', 'VTOL', '复合翼', '倾转旋翼', 'eVTOL', '垂直起降固定翼',
                '倾转双旋翼', '倾转式', '复合式', 'lift+cruise', 'lift and cruise',
                '空中出租车', 'UAM', '城市空中交通', 'urban air mobility'
            ],
            '无人直升机': [
                '无人直升机', 'helicopter', '旋翼机', '单旋翼', '双旋翼',
                '共轴双旋翼', '纵列式', '横列式', '无人旋翼机'
            ],
            '仿生无人机': [
                '仿生', '仿鸟', '仿昆虫', '扑翼', 'bird-inspired', 'bio-inspired',
                '扑翼机', '机器鸟', '机器昆虫', 'flapping wing', 'ornithopter',
                '仿生扑翼', '微型无人机', 'MAV'
            ],
            '巡飞弹': [
                '巡飞弹', '游荡弹药', 'loitering', 'suicide drone', '游荡无人机',
                '自杀式无人机', '攻击无人机', '神风无人机', 'kamikaze drone',
                '巡飞武器', '猎杀无人机', 'loitering munition'
            ],
            '水下无人机': [
                '水下', 'UUV', 'ROV', '无人潜航器', 'AUV', '潜航器',
                '水下机器人', '水下探测', '海洋机器人', 'submersible', 'underwater drone',
                '水下航行器', '江河机器人'
            ],
            '蜂群/集群': [
                '蜂群', '集群', 'swarm', '编队', '集群飞行', '多机协同',
                '协同作战', '集群智能', '无人机群', 'drone swarm', 'formation',
                '分布式', '协作无人机', '编队飞行'
            ],
            '特种无人机': [
                '太阳能', '氢燃料', '混合动力', '飞艇', '平流层',
                '高空平台', 'HAPS', '系留', 'tethered', '太阳能无人机',
                '平流层无人机', '高空伪卫星', '伪卫星', '气球无人机',
                '交通无人机', '反无人机', '拦截', '检测', 'recce'
            ],
        }

        self.application_keywords = {
            '军事国防': ['军事', '国防', '军用', '察打一体', '武装', '侦察', '攻击', 'military', 'defense'],
            '民用消费': ['消费级', '民用', '航拍', '自拍', '爱好者', 'consumer'],
            '商业应用': ['物流', '快递', '配送', '农业', '植保', '测绘', '巡检', '物流配送'],
            '科研教育': ['科研', '教育', '实验', '大学', '研究', '学术'],
        }

        self.feature_keywords = [
            '续航', '载重', '智能避障', '自主飞行', '自动返航', '精准悬停',
            'RTK定位', '机器视觉', 'AI飞行', '障碍物感知', '自动跟踪',
            '一键起飞', '自动降落', '图传距离', '抗风能力', '防水',
            '折叠设计', '轻量化', '高性能', '长航时', '高精度'
        ]

        self.method_keywords = [
            'AI算法', '深度学习', '机器视觉', '计算机视觉', '5G通信',
            '边缘计算', '集群控制', '协同飞行', '自主导航', '路径规划',
            '避障算法', '姿态控制', '动力系统', '材料创新', '结构优化'
        ]

    def classify_drone_type(self, text: str) -> str:
        if not text:
            return '其他'

        text_lower = text.lower()
        scores = {}

        for drone_type, keywords in self.drone_type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            if score > 0:
                scores[drone_type] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return '其他'

    def classify_application(self, text: str) -> Optional[str]:
        if not text:
            return None

        text_lower = text.lower()
        scores = {}

        for app_type, keywords in self.application_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1
            if score > 0:
                scores[app_type] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]

        return None

    def extract_features(self, text: str) -> List[str]:
        if not text:
            return []

        features = []
        text_lower = text.lower()

        for feature in self.feature_keywords:
            if feature.lower() in text_lower:
                features.append(feature)

        return features[:5]

    def extract_methods(self, text: str) -> List[str]:
        if not text:
            return []

        methods = []
        text_lower = text.lower()

        for method in self.method_keywords:
            if method.lower() in text_lower:
                methods.append(method)

        return methods[:5]

    def extract_company(self, text: str) -> Optional[str]:
        if not text:
            return None

        companies = {
            '大疆创新': ['大疆', 'DJI', '大疆创新', 'dji.com'],
            '极飞科技': ['极飞', 'XAG', '极飞科技'],
            '亿航智能': ['亿航', 'EHang', '亿航智能'],
            '道通智能': ['道通', 'Autel', 'Autel Robotics'],
            '派诺特': ['Parrot', '派诺特'],
            'Skydio': ['Skydio'],
            'Wing': ['Wing', 'Alphabet'],
            'Amazon': ['Amazon', 'Prime Air'],
        }

        text_lower = text.lower()
        for company_name, aliases in companies.items():
            for alias in aliases:
                if alias.lower() in text_lower:
                    return company_name

        return None

    def classify_article(self, article: Dict) -> Dict:
        text = f"{article.get('title', '')} {article.get('content', '')}"

        classified = article.copy()
        classified['drone_type'] = self.classify_drone_type(text)
        classified['application'] = self.classify_application(text)
        classified['features'] = ', '.join(self.extract_features(text))
        classified['method'] = ', '.join(self.extract_methods(text))

        if not classified.get('company'):
            classified['company'] = self.extract_company(text)

        return classified

    def batch_classify(self, articles: List[Dict]) -> List[Dict]:
        return [self.classify_article(article) for article in articles]

    def group_by_company(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        groups = {}

        for article in articles:
            company = article.get('company')
            if company:
                if company not in groups:
                    groups[company] = []
                groups[company].append(article)

        return groups

    def group_by_type(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        groups = {}

        for article in articles:
            drone_type = article.get('drone_type', '未分类')
            if drone_type:
                if drone_type not in groups:
                    groups[drone_type] = []
                groups[drone_type].append(article)

        return groups

    def group_by_region(self, articles: List[Dict]) -> Dict[str, List[Dict]]:
        groups = {}

        for article in articles:
            region = article.get('region', '未知')
            if region:
                if region not in groups:
                    groups[region] = []
                groups[region].append(article)

        return groups

    def get_statistics(self, articles: List[Dict]) -> Dict:
        total = len(articles)

        drone_types = Counter([a.get('drone_type', '未分类') for a in articles if a.get('drone_type')])
        regions = Counter([a.get('region', '未知') for a in articles])
        companies = Counter([a.get('company', '未知') for a in articles if a.get('company')])

        return {
            'total': total,
            'by_type': dict(drone_types),
            'by_region': dict(regions),
            'by_company': dict(companies.most_common(10)),
        }

    def extract_keywords(self, articles: List[Dict], top_n: int = 20) -> List[Tuple[str, int]]:
        all_text = ' '.join([
            f"{a.get('title', '')} {a.get('content', '')}"
            for a in articles
        ])

        words = jieba.cut(all_text)
        word_freq = Counter()

        stopwords = {'的', '是', '在', '和', '了', '有', '个', '人', '这', '上', '下', '中', '为', '与', '或', '等', '着', '把', '被', '让', '给', '对', '向', '到', '从', '以', '及', '而', '但', '却', '也', '都', '还', '很', '要', '会', '能', '可', '将', '并', '于', '之'}

        for word in words:
            if len(word) >= 2 and word not in stopwords:
                word_freq[word] += 1

        return word_freq.most_common(top_n)
