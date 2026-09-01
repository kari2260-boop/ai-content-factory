"""
OpenClaw 内容生成桥接 - 升级版
直接调用 OpenClaw 生成 K博士风格的5种格式内容
支持远程 Gateway（如 Mac Mini 上的 OpenClaw）
"""
import subprocess
import json
import os
import shutil
import re
import requests
from typing import Dict, Optional
from pathlib import Path

from modules.utils import setup_logger
from modules.config import OPENCLAW_GATEWAY_URL

logger = setup_logger('openclaw_bridge', 'generator.log')


class OpenClawBridge:
    """OpenClaw 知识库和内容生成桥接"""

    def __init__(self, user_id: str = 'dr_k'):
        self.user_id = user_id
        # 远程 Gateway HTTP URL（ws:// → http://）
        self.gateway_http_url = OPENCLAW_GATEWAY_URL.replace('ws://', 'http://').replace('wss://', 'https://')
        self.status = self._check_openclaw()
        self.available = bool(self.status.get('gateway_reachable'))
        self.workspace_path = Path.home() / '.openclaw' / 'workspace' / 'profiles' / user_id

    def _check_openclaw(self) -> Dict[str, object]:
        """通过 HTTP 检测远程 Gateway 是否可达。"""
        url = self.gateway_http_url
        logger.info(f"🔍 检测 OpenClaw Gateway: {url}")

        # 尝试常见的健康检查端点
        for endpoint in ['/health', '/api/health', '/status', '/']:
            try:
                resp = requests.get(f"{url}{endpoint}", timeout=5)
                if resp.status_code < 500:
                    logger.info(f"✅ OpenClaw Gateway 可达: {url}{endpoint} ({resp.status_code})")
                    return {
                        "installed": True,
                        "service_running": True,
                        "gateway_reachable": True,
                        "agent_active": True,
                        "label": "运行中",
                        "detail": f"远程 Gateway 正常 ({url})",
                        "raw": "",
                    }
            except requests.exceptions.ConnectionError:
                continue
            except Exception:
                continue

        logger.warning(f"⚠️ OpenClaw Gateway 不可达: {url}")
        return {
            "installed": False,
            "service_running": False,
            "gateway_reachable": False,
            "agent_active": False,
            "label": "未运行",
            "detail": f"无法连接到 {url}，请确认 Mac Mini 上的 OpenClaw 已启动",
            "raw": "",
        }

    def get_status(self) -> Dict[str, object]:
        """获取可展示的状态摘要。"""
        return self.status

    def _read_workspace_file(self, filename: str) -> str:
        """读取 OpenClaw workspace 文件"""
        try:
            filepath = self.workspace_path / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            logger.error(f"读取 {filename} 失败: {str(e)}")
            return ""

    def get_user_profile(self) -> Dict[str, str]:
        """获取用户的完整画像"""
        return {
            'user': self._read_workspace_file('USER.md'),
            'memory': self._read_workspace_file('MEMORY.md'),
            'content_guide': self._read_workspace_file('CONTENT_GUIDE.md')
        }

    def generate_content(
        self,
        topic: Dict,
        user_opinion: str,
        format_type: str
    ) -> Dict:
        """
        使用 OpenClaw 生成指定格式的内容

        Args:
            topic: 选题信息
            user_opinion: 用户观点
            format_type: 格式类型 (video/article/moments/xiaohongshu/book)

        Returns:
            生成结果字典
        """
        if not self.available:
            return {
                'error': True,
                'content': 'OpenClaw 不可用',
                'word_count': 0
            }

        try:
            prompt = self._build_prompt(topic, user_opinion, format_type)
            logger.info(f"🚀 使用远程 OpenClaw 生成 {format_type} 格式内容...")

            # 调用远程 Gateway API
            resp = requests.post(
                f"{self.gateway_http_url}/api/chat",
                json={"message": prompt, "stream": False},
                timeout=120
            )

            if resp.status_code != 200:
                logger.error(f"❌ OpenClaw API 返回 {resp.status_code}")
                return {
                    'error': True,
                    'content': f'API 返回错误: {resp.status_code}',
                    'word_count': 0
                }

            result = resp.json()
            content = result.get('response', result.get('message', result.get('content', '')))

            if not content:
                logger.error("❌ OpenClaw 返回空内容")
                return {
                    'error': True,
                    'content': '生成内容为空',
                    'word_count': 0
                }

            logger.info(f"✅ {format_type} 格式内容生成成功 ({len(content)} 字)")
            return {
                'error': False,
                'content': content,
                'word_count': len(content),
                'provider': 'OpenClaw',
                'model': 'remote-gateway'
            }

        except requests.exceptions.Timeout:
            logger.error(f"❌ OpenClaw 生成超时 ({format_type})")
            return {
                'error': True,
                'content': '生成超时（超过2分钟）',
                'word_count': 0
            }
        except Exception as e:
            logger.error(f"❌ OpenClaw 生成异常: {str(e)}")
            return {
                'error': True,
                'content': f'生成异常: {str(e)}',
                'word_count': 0
            }

    def _build_prompt(self, topic: Dict, user_opinion: str, format_type: str) -> str:
        """构建生成内容的 prompt"""

        format_names = {
            'video': '视频号文案',
            'article': '公众号文章',
            'moments': '朋友圈文案',
            'xiaohongshu': '小红书文案',
            'book': '书稿素材'
        }

        format_requirements = {
            'video': """
**格式要求：**
- 总字数：900-1500字
- 结构：开场Hook(0-10秒) → 核心观点1(10-90秒) → 案例/故事(90-180秒) → 核心观点2(180-240秒) → 金句总结(240-270秒) → 行动号召(270-300秒)
- 口语化表达，每30秒一个小高潮
- 包含2-3个金句（可单独截图传播）
- 结尾有明确的CTA
""",
            'article': """
**格式要求：**
- 总字数：2000字左右
- 结构：备选标题(3个) → 开头场景/故事 → 一、问题的本质 → 二、深层原因分析 → 三、实践解决方案 → 四、写在最后 → 思考问题
- 每300-400字一个小标题
- 包含具体案例或数据支撑
- 结尾留思考问题，引导评论
""",
            'moments': """
**格式要求：**
- 总字数：150-200字
- 结构：第一句抓眼球 → 核心观点/故事 → 引发思考/讨论 → 话题标签
- 有态度、有观点
- 可以使用emoji但不过度
- 结尾留钩子，引导评论
""",
            'xiaohongshu': """
**格式要求：**
- 总字数：500-800字
- 结构：标题(尽量短，适合封面) → 开头(痛点/反差/结论) → 正文(3-5个要点，每个要点有小标题) → 总结(金句或行动建议) → 话题标签
- 多用短句，易于阅读，适合拆成图文卡片
- 每个要点都要能单独做一张图文卡
- 话题标签3-5个

**输出格式：**
### 封面标题
一句话标题，20字内。

### 01 误区
2-4句，讲大家最常见的理解偏差。

### 02 核心判断
2-4句，直接给出你的核心观点。

### 03 方法
3个小点，每个小点2-3句。

### 04 案例/清单
2-3个具体例子或检查清单。

### 05 结尾
1-2句总结 + 互动提问 + 话题标签。
""",
            'book': """
**格式要求：**
- 总字数：800-1200字
- 结构：建议归档章节 → 核心论点 → 理论支撑 → 案例/数据 → 实践建议 → 参考文献
- 学术化表达，有理论支撑
- 包含数据、研究、案例
- 逻辑严密，论证充分
"""
        }

        prompt = f"""你是 {self.user_id} 的内容生成助手。请根据以下信息，生成一篇{format_names[format_type]}。

**重要提示：**
1. 你已经完整学习了用户的风格、方法论和案例库（在 USER.md、MEMORY.md、CONTENT_GUIDE.md 中）
2. 请严格按照用户的风格创作：温暖有温度、专业但易懂、实践导向、结构清晰
3. 使用用户的方法论和理念
4. 引用用户的真实案例和金句库

---

**选题信息：**
标题：{topic['title']}
摘要：{topic.get('excerpt', '无')}
来源：{topic['source']}
AI评分理由：{topic.get('ai_reason', '无')}
建议角度：{', '.join(topic.get('suggested_angles', []))}

---

**用户的核心观点：**
{user_opinion}

---

{format_requirements[format_type]}

---

**创作原则（必须遵守）：**
✅ 温暖鼓励、真诚分享（不说教）
✅ 专业易懂、有理有据（引用研究和数据）
✅ 实践导向、可操作（提供具体方法）
✅ 真实案例、数据支撑（用真实经历）
✅ 尊重多元、包容差异
✅ 引导思考、启发行动
✅ 关注过程、发现优势

❌ 避免说教、大道理、空洞鸡汤
❌ 避免术语堆砌、炫耀专业
❌ 避免只讲理论不讲实践
❌ 避免标题党、夸大其词

---

请直接输出{format_names[format_type]}的完整内容，不要有任何前缀说明。
"""

        return prompt

    def generate_all_formats(
        self,
        topic: Dict,
        user_opinion: str
    ) -> Dict:
        """
        生成所有5种格式的内容

        Returns:
            包含所有格式内容的字典
        """
        logger.info("=" * 60)
        logger.info(f"🚀 开始生成所有格式内容: {topic['title']}")
        logger.info("=" * 60)

        results = {
            'topic': topic,
            'user_opinion': user_opinion,
            'contents': {},
            'generated_at': None,
            'provider': 'OpenClaw'
        }

        formats = ['video', 'article', 'moments', 'xiaohongshu', 'book']
        format_names = {
            'video': '视频号',
            'article': '公众号',
            'moments': '朋友圈',
            'xiaohongshu': '小红书',
            'book': '书稿'
        }

        for format_type in formats:
            logger.info(f"\n📝 正在生成 {format_names[format_type]} 格式...")

            result = self.generate_content(topic, user_opinion, format_type)
            results['contents'][format_type] = result

            if result['error']:
                logger.error(f"❌ {format_names[format_type]} 生成失败")
            else:
                logger.info(f"✅ {format_names[format_type]} 生成成功 ({result['word_count']} 字)")

        from datetime import datetime
        results['generated_at'] = datetime.now().isoformat()

        logger.info("\n" + "=" * 60)
        logger.info("✅ 所有格式内容生成完成")
        logger.info("=" * 60)

        return results


if __name__ == '__main__':
    # 测试
    bridge = OpenClawBridge(user_id='dr_k')

    if bridge.available:
        print("✅ OpenClaw 可用")

        # 测试读取配置
        profile = bridge.get_user_profile()
        print(f"\n📄 USER.md: {len(profile['user'])} 字符")
        print(f"📄 MEMORY.md: {len(profile['memory'])} 字符")
        print(f"📄 CONTENT_GUIDE.md: {len(profile['content_guide'])} 字符")

        # 测试生成内容
        test_topic = {
            'title': 'AI时代，孩子该学什么才不会被淘汰？',
            'excerpt': '随着AI技术的快速发展，家长们越来越焦虑...',
            'source': '测试',
            'ai_reason': '这个话题非常符合K博士的专业领域',
            'suggested_angles': ['从人生杠杆角度分析', '结合真实案例']
        }

        test_opinion = "我认为AI时代最重要的是培养孩子从弱变强的能力和做决策的能力"

        print("\n🧪 测试生成朋友圈格式...")
        result = bridge.generate_content(test_topic, test_opinion, 'moments')

        if not result['error']:
            print(f"\n✅ 生成成功 ({result['word_count']} 字):")
            print("-" * 60)
            print(result['content'])
            print("-" * 60)
        else:
            print(f"\n❌ 生成失败: {result['content']}")
    else:
        print("❌ OpenClaw 不可用")
        print("请先启动 OpenClaw: openclaw gateway")
