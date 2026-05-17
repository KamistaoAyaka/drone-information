import hashlib
from typing import List, Dict, Set, Tuple
from difflib import SequenceMatcher

class Deduplicator:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.seen_hashes = set()
        self.seen_urls = set()

    def generate_hash(self, text: str) -> str:
        if not text:
            return ""
        clean_text = ' '.join(text.lower().split())
        return hashlib.md5(clean_text.encode('utf-8')).hexdigest()

    def calculate_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def is_duplicate(self, article: Dict, existing_articles: List[Dict] = None) -> Tuple[bool, str]:
        url = article.get('url', '')
        title = article.get('title', '')
        content = article.get('content', '')

        if url and url in self.seen_urls:
            return True, 'URL已存在'

        title_hash = self.generate_hash(title)
        if title_hash in self.seen_hashes:
            return True, '标题重复'

        if existing_articles:
            for existing in existing_articles:
                if self.calculate_similarity(title, existing.get('title', '')) >= self.similarity_threshold:
                    return True, '标题相似度超过阈值'

                combined_text = title + ' ' + content
                existing_combined = existing.get('title', '') + ' ' + existing.get('content', '')
                if self.calculate_similarity(combined_text, existing_combined) >= self.similarity_threshold:
                    return True, '内容相似度超过阈值'

        content_hash = self.generate_hash(content[:200])
        if content_hash in self.seen_hashes:
            return True, '内容前200字重复'

        return False, ''

    def add_to_seen(self, article: Dict):
        url = article.get('url', '')
        title = article.get('title', '')
        content = article.get('content', '')

        if url:
            self.seen_urls.add(url)

        if title:
            self.seen_hashes.add(self.generate_hash(title))

        if content:
            self.seen_hashes.add(self.generate_hash(content[:200]))

    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        unique_articles = []
        duplicates_count = 0

        for article in articles:
            is_dup, reason = self.is_duplicate(article, unique_articles)
            if not is_dup:
                unique_articles.append(article)
                self.add_to_seen(article)
            else:
                duplicates_count += 1
                print(f"跳过重复文章: {article.get('title', '')[:50]}... 原因: {reason}")

        print(f"去重完成: {len(unique_articles)} 篇唯一文章, {duplicates_count} 篇重复文章被移除")
        return unique_articles

    def find_similar_groups(self, articles: List[Dict]) -> List[List[Dict]]:
        groups = []
        used_indices = set()

        for i, article in enumerate(articles):
            if i in used_indices:
                continue

            group = [article]
            used_indices.add(i)

            for j in range(i + 1, len(articles)):
                if j in used_indices:
                    continue

                similarity = self.calculate_similarity(
                    article.get('title', ''),
                    articles[j].get('title', '')
                )

                if similarity >= self.similarity_threshold:
                    group.append(articles[j])
                    used_indices.add(j)

            groups.append(group)

        return groups

    def get_similarity_report(self, article1: Dict, article2: Dict) -> Dict:
        title_sim = self.calculate_similarity(
            article1.get('title', ''),
            article2.get('title', '')
        )

        content_sim = self.calculate_similarity(
            article1.get('content', ''),
            article2.get('content', '')
        )

        return {
            'title_similarity': round(title_sim, 3),
            'content_similarity': round(content_sim, 3),
            'is_duplicate': title_sim >= self.similarity_threshold or content_sim >= self.similarity_threshold
        }

    def clear_cache(self):
        self.seen_hashes.clear()
        self.seen_urls.clear()

    def load_from_database(self, articles: List[Dict]):
        for article in articles:
            self.add_to_seen(article)
