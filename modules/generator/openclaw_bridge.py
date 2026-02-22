"""
OpenClaw 内容生成桥接 - 升级版
直接调用 OpenClaw 生成 K博士风格的5种格式内容
"""
import subprocess
import json
import os
from typing import Dict, Optional
from pathlib import Path

from modules.utils import setup_logger

logger = setup_logger('openclaw_bridge', 'generator.log')


class OpenClawBridge:
    """OpenClaw 知识库和内容生成桥接"""

    def __init__(self):
        self.available = self._check_openclaw()
        self.workspace_path = Path.home() / '.openclaw' / 'workspace'

    def _check_openclaw(self) -> bool:
        """检查 OpenClaw 是否可用"""
        try:
            result = subprocess.run(
                ['openclaw', 'gateway', 'health'],
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                logger.info("✅ OpenClaw 网关运行正常")
                return True
            else:
                logger.warning("⚠️ OpenClaw 网关未运行")
                return False

        except subprocess.TimeoutExpired:
            logger.warning("⚠️ OpenClaw 检查超时（可能正在启动）")
            return False
        except Exception as e:
            logger.warning(f"⚠️ OpenClaw 检查失败: {str(e)}")
            return False

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

    def get_kari_profile(self) -> Dict[str, str]:
        """获取 Kari 的完整画像"""
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
            # 构建 prompt
            prompt = self._build_prompt(topic, user_opinion, format_type)

            logger.info(f"🚀 使用 OpenClaw 生成 {format_type} 格式内容...")

            # 调用 OpenClaw agent
            # 使用 memory 命令来利用 workspace 中的信息
            result = subprocess.run(
                [
                    'openclaw', 'agent',
                    '--message', prompt,
                    '--agent', 'main',
                    '--json'
                ],
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )

            if result.returncode != 0:
                logger.error(f"❌ OpenClaw 生成失败: {result.stderr}")
                return {
                    'error': True,
                    'content': f'生成失败: {result.stderr}',
                    'word_count': 0
                }

            # 解析输出
            try:
                output = json.loads(result.stdout)
                content = output.get('response', output.get('message', ''))
            except json.JSONDecodeError:
                # 如果不是 JSON，直接使用文本输出
                content = result.stdout.strip()

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
                'model': 'main-agent'
            }

        except subprocess.TimeoutExpired:
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
- 总字数：800-1000字
- 结构：标题(带emoji) → 开头(痛点或场景) → 正文(3-5个要点，用序号) → 总结(金句或行动建议) → 话题标签
- 多用短句，易于阅读
- 每个要点用emoji标注
- 话题标签3-5个
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

        prompt = f"""你是 K博士（郭梦娇）的内容生成助手。请根据以下信息，生成一篇{format_names[format_type]}。

**重要提示：**
1. 你已经完整学习了 K博士的风格、方法论和案例库（在 USER.md、MEMORY.md、CONTENT_GUIDE.md 中）
2. 请严格按照 K博士的风格创作：温暖有温度、专业但易懂、实践导向、结构清晰
3. 使用 K博士的方法论：人生杠杆、从弱变强、关键决策
4. 引用 K博士的真实案例和金句库

---

**选题信息：**
标题：{topic['title']}
摘要：{topic.get('excerpt', '无')}
来源：{topic['source']}
AI评分理由：{topic.get('ai_reason', '无')}
建议角度：{', '.join(topic.get('suggested_angles', []))}

---

**K博士的核心观点：**
{user_opinion}

---

{format_requirements[format_type]}

---

**创作原则（必须遵守）：**
✅ 温暖鼓励、真诚分享（不说教）
✅ 专业易懂、有理有据（引用研究和数据）
✅ 实践导向、可操作（提供具体方法）
✅ 真实案例、数据支撑（用 K博士的经历）
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
    bridge = OpenClawBridge()

    if bridge.available:
        print("✅ OpenClaw 可用")

        # 测试读取配置
        profile = bridge.get_kari_profile()
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
