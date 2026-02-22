"""
知识库注入模块
支持三种方式：收件箱监听、URL抓取、文本直接注入
"""
import os
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import chardet
from docx import Document
import PyPDF2

from modules.generator.claude_client import ClaudeClient
from modules.publisher.notion_client import NotionClient
from modules.generator.openclaw_bridge import OpenClawBridge
from modules.utils import setup_logger, load_json, DATA_DIR
from modules.config import BOOK_STRUCTURE_PATH

logger = setup_logger('knowledge_feed', 'knowledge_feed.log')


class KnowledgeFeed:
    """知识库注入管理器"""

    def __init__(self):
        self.inbox_dir = DATA_DIR / 'inbox'
        self.imported_dir = DATA_DIR / 'imported'
        self.inbox_dir.mkdir(exist_ok=True)
        self.imported_dir.mkdir(exist_ok=True)

        try:
            self.claude = ClaudeClient()
            self.claude_available = True
        except:
            self.claude_available = False
            logger.warning("Claude 客户端不可用")

        try:
            self.notion = NotionClient()
            self.notion_available = True
        except:
            self.notion_available = False
            logger.warning("Notion 客户端不可用")

        self.openclaw = OpenClawBridge()
        self.book_structure = load_json(BOOK_STRUCTURE_PATH)

        self.observer = None
        self.is_watching = False

    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.claude_available or self.openclaw.available

    def start_inbox_watcher(self):
        """启动收件箱监听"""
        if self.is_watching:
            logger.warning("收件箱监听已在运行")
            return

        event_handler = InboxEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.inbox_dir), recursive=False)
        self.observer.start()
        self.is_watching = True
        logger.info(f"收件箱监听已启动: {self.inbox_dir}")

    def stop_inbox_watcher(self):
        """停止收件箱监听"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            logger.info("收件箱监听已停止")

    def process_single_file(self, filepath: Path) -> Dict:
        """处理单个文件"""
        logger.info(f"处理文件: {filepath.name}")

        try:
            # 读取文件内容
            content = self._read_file(filepath)
            if not content:
                return {'success': False, 'error': '无法读取文件内容'}

            # 提取标题
            title = filepath.stem

            # 检查是否包含提示词
            has_prompts = any(kw in content.lower() for kw in ['提示词', 'prompt', '模板'])

            if has_prompts:
                # 提取提示词
                prompts = self.extract_prompts(content)
                result = {
                    'success': True,
                    'title': title,
                    'content': content,
                    'prompts': prompts,
                    'needs_confirmation': True
                }
            else:
                # 直接处理
                result = self.process_text(
                    text=content,
                    title=title,
                    source_type='file',
                    tags=[filepath.suffix[1:]]
                )

            # 移动到已导入目录
            date_str = datetime.now().strftime('%Y-%m-%d')
            target_dir = self.imported_dir / date_str
            target_dir.mkdir(exist_ok=True)
            target_path = target_dir / filepath.name

            shutil.move(str(filepath), str(target_path))
            logger.info(f"文件已移动到: {target_path}")

            return result

        except Exception as e:
            logger.error(f"处理文件失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _read_file(self, filepath: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            suffix = filepath.suffix.lower()

            if suffix == '.txt' or suffix == '.md':
                # 检测编码
                with open(filepath, 'rb') as f:
                    raw = f.read()
                    detected = chardet.detect(raw)
                    encoding = detected['encoding'] or 'utf-8'

                with open(filepath, 'r', encoding=encoding) as f:
                    return f.read()

            elif suffix == '.docx':
                doc = Document(filepath)
                return '\n'.join([para.text for para in doc.paragraphs])

            elif suffix == '.pdf':
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = []
                    for page in reader.pages:
                        text.append(page.extract_text())
                    return '\n'.join(text)

            else:
                logger.warning(f"不支持的文件格式: {suffix}")
                return None

        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            return None

    def process_url(self, url: str, title: str = "", tags: List[str] = None) -> Dict:
        """处理 URL"""
        logger.info(f"处理 URL: {url}")

        try:
            # 抓取页面
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # 提取标题
            if not title:
                title_tag = soup.find('title')
                title = title_tag.get_text() if title_tag else url

            # 提取正文
            # 移除脚本和样式
            for script in soup(['script', 'style']):
                script.decompose()

            # 尝试找到主要内容
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)

            # 清理空行
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            content = '\n'.join(lines)

            # 处理文本
            return self.process_text(
                text=content,
                title=title,
                source_type='url',
                tags=tags or ['web']
            )

        except Exception as e:
            logger.error(f"处理 URL 失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def process_text(self, text: str, title: str, source_type: str,
                     chapter: str = None, tags: List[str] = None) -> Dict:
        """处理文本内容"""
        logger.info(f"处理文本: {title}")

        if not self.claude_available:
            return {'success': False, 'error': 'Claude 不可用'}

        try:
            # 分块（每块约2000字）
            chunks = self._split_text(text, max_length=2000)
            logger.info(f"文本分为 {len(chunks)} 块")

            # 使用 Claude 分类章节
            if not chapter and self.book_structure:
                chapter = self._classify_chapter(text[:1000])

            # 使用 Claude 提取关键信息和质量评分
            summary = self._extract_summary(text[:2000])

            # 写入 OpenClaw
            openclaw_success = False
            if self.openclaw.available:
                openclaw_success = self._write_to_openclaw(title, text, tags or [])

            # 写入 Notion
            notion_page_id = None
            if self.notion_available:
                notion_page_id = self._write_to_notion(
                    title=title,
                    content=text,
                    chapter=chapter,
                    source_type=source_type,
                    summary=summary,
                    tags=tags or []
                )

            return {
                'success': True,
                'title': title,
                'chapter': chapter,
                'chunks': len(chunks),
                'summary': summary,
                'openclaw_success': openclaw_success,
                'notion_page_id': notion_page_id
            }

        except Exception as e:
            logger.error(f"处理文本失败: {str(e)}")
            return {'success': False, 'error': str(e)}

    def extract_prompts(self, text: str) -> List[Dict]:
        """提取提示词片段"""
        if not self.claude_available:
            return []

        try:
            prompt = f"""从以下文本中提取所有的提示词（Prompt）片段。

文本内容：
{text[:3000]}

请识别并提取：
1. 明确标注为"提示词"、"Prompt"、"模板"的内容
2. 看起来像是给 AI 的指令的段落
3. 包含角色设定、任务描述、输出格式要求的文本

以 JSON 格式返回：
[
  {{
    "title": "提示词标题",
    "content": "完整的提示词内容",
    "type": "角色设定/任务指令/输出模板"
  }}
]

只返回 JSON，不要其他内容。"""

            response = self.claude.generate(prompt, max_tokens=2000)

            # 解析 JSON
            import json
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]

            prompts = json.loads(response)
            logger.info(f"提取到 {len(prompts)} 个提示词")
            return prompts

        except Exception as e:
            logger.error(f"提取提示词失败: {str(e)}")
            return []

    def _split_text(self, text: str, max_length: int = 2000) -> List[str]:
        """分割文本"""
        chunks = []
        current_chunk = ""

        for line in text.split('\n'):
            if len(current_chunk) + len(line) + 1 > max_length:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk += '\n' + line if current_chunk else line

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _classify_chapter(self, text: str) -> str:
        """分类到书稿章节"""
        if not self.book_structure:
            return 'ch01'

        try:
            chapters_info = "\n".join([
                f"- {ch['id']}: {ch['title']}"
                for ch in self.book_structure['chapters']
            ])

            prompt = f"""将以下内容归类到最合适的章节。

章节列表：
{chapters_info}

内容摘要：
{text[:500]}

只返回章节ID（如 ch01），不要其他内容。"""

            chapter_id = self.claude.generate(prompt, max_tokens=50).strip()

            # 验证
            valid_chapters = [ch['id'] for ch in self.book_structure['chapters']]
            if chapter_id in valid_chapters:
                return chapter_id
            else:
                return 'ch01'

        except:
            return 'ch01'

    def _extract_summary(self, text: str) -> Dict:
        """提取摘要和质量评分"""
        try:
            prompt = f"""分析以下内容，提取关键信息。

内容：
{text}

以 JSON 格式返回：
{{
  "summary": "100字内的摘要",
  "key_points": ["要点1", "要点2", "要点3"],
  "quality_score": 8,
  "reason": "质量评分理由"
}}

只返回 JSON。"""

            response = self.claude.generate(prompt, max_tokens=500)

            import json
            response = response.strip()
            if response.startswith('```'):
                response = response.split('```')[1]
                if response.startswith('json'):
                    response = response[4:]

            return json.loads(response)

        except:
            return {
                'summary': text[:100],
                'key_points': [],
                'quality_score': 5,
                'reason': '自动评分'
            }

    def _write_to_openclaw(self, title: str, content: str, tags: List[str]) -> bool:
        """写入 OpenClaw（通过 CLI）"""
        try:
            # OpenClaw 没有直接的写入命令，这里记录日志
            # 实际使用时可以通过 agent 命令或直接写文件
            logger.info(f"OpenClaw 写入: {title} (标签: {', '.join(tags)})")
            return True
        except Exception as e:
            logger.error(f"OpenClaw 写入失败: {str(e)}")
            return False

    def _write_to_notion(self, title: str, content: str, chapter: str,
                         source_type: str, summary: Dict, tags: List[str]) -> Optional[str]:
        """写入 Notion"""
        try:
            metadata = {
                '来源类型': source_type,
                '章节': chapter,
                '质量评分': f"{summary.get('quality_score', 5)}/10",
                '标签': ', '.join(tags),
                '导入时间': datetime.now().isoformat()
            }

            page_id = self.notion.create_page(
                title=f"[知识库] {title}",
                format_type='书稿',
                content=content,
                metadata=metadata
            )

            logger.info(f"Notion 写入成功: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"Notion 写入失败: {str(e)}")
            return None


class InboxEventHandler(FileSystemEventHandler):
    """收件箱文件监听处理器"""

    def __init__(self, knowledge_feed: KnowledgeFeed):
        self.knowledge_feed = knowledge_feed
        self.processing = set()

    def on_created(self, event):
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # 忽略隐藏文件和临时文件
        if filepath.name.startswith('.') or filepath.name.startswith('~'):
            return

        # 避免重复处理
        if str(filepath) in self.processing:
            return

        self.processing.add(str(filepath))

        # 等待文件写入完成
        time.sleep(2)

        # 处理文件
        try:
            self.knowledge_feed.process_single_file(filepath)
        finally:
            self.processing.discard(str(filepath))


if __name__ == '__main__':
    # 测试
    kf = KnowledgeFeed()
    print(f"知识库注入服务可用: {kf.is_available()}")

    # 测试文本注入
    test_result = kf.process_text(
        text="这是一段测试文本，关于AI教育的内容...",
        title="测试文档",
        source_type="test",
        tags=["测试"]
    )
    print(f"测试结果: {test_result}")
