"""
效果反馈追踪模块
记录发布内容的效果数据，分析并建议回流到书稿库
"""
from typing import Dict, List, Optional
from datetime import datetime
from notion_client import Client

from modules.generator.claude_client import ClaudeClient
from modules.utils import setup_logger
from modules.config import NOTION_TOKEN, NOTION_DATABASE_ID

logger = setup_logger('feedback_tracker', 'feedback_tracker.log')


class FeedbackTracker:
    """效果反馈追踪器"""

    def __init__(self):
        if not NOTION_TOKEN:
            raise ValueError("未配置 NOTION_TOKEN")

        self.client = Client(auth=NOTION_TOKEN)
        self.content_db_id = NOTION_DATABASE_ID  # 内容库
        self.feedback_db_id = None  # 效果库（需要创建）
        self.book_db_id = None  # 书稿库（需要创建）

        try:
            self.claude = ClaudeClient()
            self.claude_available = True
        except:
            self.claude_available = False
            logger.warning("Claude 客户端不可用")

    def record_publish(self, title: str, platform: str, topic: str, content: str) -> str:
        """记录发布内容到效果库"""
        try:
            logger.info(f"记录发布: {title} - {platform}")

            # 如果效果库不存在，使用内容库
            db_id = self.feedback_db_id or self.content_db_id

            page = self.client.pages.create(
                parent={"database_id": db_id},
                properties={
                    "标题": {
                        "title": [{"text": {"content": title[:100]}}]
                    },
                    "平台": {
                        "select": {"name": platform}
                    },
                    "选题": {
                        "rich_text": [{"text": {"content": topic[:2000]}}]
                    },
                    "发布时间": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "阅读量": {
                        "number": 0
                    },
                    "互动数": {
                        "number": 0
                    },
                    "主观评分": {
                        "select": {"name": "未评分"}
                    }
                }
            )

            # 添加内容
            self.client.blocks.children.append(
                block_id=page['id'],
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": content[:2000]}}]
                        }
                    }
                ]
            )

            logger.info(f"发布记录已创建: {page['id']}")
            return page['id']

        except Exception as e:
            logger.error(f"记录发布失败: {str(e)}")
            raise

    def update_metrics(self, feedback_page_id: str, views: int, interactions: int,
                      completion_rate: Optional[float] = None) -> bool:
        """更新效果数据"""
        try:
            logger.info(f"更新效果数据: {feedback_page_id}")

            properties = {
                "阅读量": {"number": views},
                "互动数": {"number": interactions}
            }

            if completion_rate is not None:
                properties["完读率"] = {"number": completion_rate}

            self.client.pages.update(
                page_id=feedback_page_id,
                properties=properties
            )

            logger.info("效果数据更新成功")
            return True

        except Exception as e:
            logger.error(f"更新效果数据失败: {str(e)}")
            return False

    def update_score(self, feedback_page_id: str, subjective_score: int) -> bool:
        """更新主观评分（1-5星）"""
        try:
            logger.info(f"更新主观评分: {feedback_page_id} - {subjective_score}星")

            score_map = {
                5: "⭐⭐⭐⭐⭐",
                4: "⭐⭐⭐⭐",
                3: "⭐⭐⭐",
                2: "⭐⭐",
                1: "⭐"
            }

            score_text = score_map.get(subjective_score, "未评分")

            self.client.pages.update(
                page_id=feedback_page_id,
                properties={
                    "主观评分": {"select": {"name": score_text}}
                }
            )

            logger.info("主观评分更新成功")
            return True

        except Exception as e:
            logger.error(f"更新主观评分失败: {str(e)}")
            return False

    def analyze_and_suggest_backflow(self, feedback_page_id: str) -> Dict:
        """分析并建议是否回流"""
        try:
            logger.info(f"分析回流建议: {feedback_page_id}")

            # 获取页面数据
            page = self.client.pages.retrieve(page_id=feedback_page_id)
            properties = page['properties']

            # 提取数据
            views = properties.get('阅读量', {}).get('number', 0)
            interactions = properties.get('互动数', {}).get('number', 0)
            score_text = properties.get('主观评分', {}).get('select', {}).get('name', '未评分')

            # 转换评分
            score_map = {
                "⭐⭐⭐⭐⭐": 5,
                "⭐⭐⭐⭐": 4,
                "⭐⭐⭐": 3,
                "⭐⭐": 2,
                "⭐": 1,
                "未评分": 0
            }
            score = score_map.get(score_text, 0)

            # 判断是否应该回流
            should_backflow = False
            reasons = []

            if views >= 5000:
                should_backflow = True
                reasons.append(f"阅读量达到 {views}，超过 5000 阈值")

            if score >= 4:
                should_backflow = True
                reasons.append(f"主观评分 {score} 星，达到高质量标准")

            if interactions >= 100:
                reasons.append(f"互动数 {interactions}，用户反响良好")

            reason = "；".join(reasons) if reasons else "未达到回流标准"

            result = {
                "should_backflow": should_backflow,
                "reason": reason,
                "metrics": {
                    "views": views,
                    "interactions": interactions,
                    "score": score
                }
            }

            logger.info(f"回流分析完成: {result}")
            return result

        except Exception as e:
            logger.error(f"分析回流建议失败: {str(e)}")
            return {
                "should_backflow": False,
                "reason": f"分析失败: {str(e)}",
                "metrics": {}
            }

    def confirm_backflow(self, book_page_id: str) -> bool:
        """确认回流到书稿库"""
        try:
            logger.info(f"确认回流: {book_page_id}")

            self.client.pages.update(
                page_id=book_page_id,
                properties={
                    "是否参考样本": {"checkbox": True}
                }
            )

            logger.info("回流确认成功")
            return True

        except Exception as e:
            logger.error(f"确认回流失败: {str(e)}")
            return False

    def generate_prompt_optimization_advice(self, platform: str) -> str:
        """生成提示词优化建议"""
        if not self.claude_available:
            return "Claude 客户端不可用，无法生成优化建议"

        try:
            logger.info(f"生成 {platform} 平台的提示词优化建议")

            # 获取该平台的效果数据
            feedback_data = self._get_platform_feedback(platform)

            if not feedback_data:
                return f"{platform} 平台暂无效果数据"

            # 构建分析 prompt
            prompt = f"""你是内容优化专家。请分析以下 {platform} 平台的内容效果数据，给出提示词优化建议。

## 效果数据
{self._format_feedback_data(feedback_data)}

## 任务
1. 分析高效内容的共同特征
2. 分析低效内容的问题所在
3. 给出具体的提示词优化建议（3-5条）
4. 每条建议要具体可操作

请用中文回答，格式清晰。"""

            advice = self.claude.generate(prompt, max_tokens=1500)
            logger.info("提示词优化建议生成成功")
            return advice

        except Exception as e:
            logger.error(f"生成优化建议失败: {str(e)}")
            return f"生成失败: {str(e)}"

    def _get_platform_feedback(self, platform: str) -> List[Dict]:
        """获取平台的效果数据"""
        try:
            db_id = self.feedback_db_id or self.content_db_id

            results = self.client.databases.query(
                database_id=db_id,
                filter={
                    "property": "平台",
                    "select": {"equals": platform}
                },
                sorts=[
                    {"property": "阅读量", "direction": "descending"}
                ],
                page_size=20
            )

            feedback_list = []
            for page in results['results']:
                props = page['properties']
                feedback_list.append({
                    'title': props.get('标题', {}).get('title', [{}])[0].get('text', {}).get('content', ''),
                    'views': props.get('阅读量', {}).get('number', 0),
                    'interactions': props.get('互动数', {}).get('number', 0),
                    'score': props.get('主观评分', {}).get('select', {}).get('name', '未评分')
                })

            return feedback_list

        except Exception as e:
            logger.error(f"获取平台效果数据失败: {str(e)}")
            return []

    def _format_feedback_data(self, feedback_data: List[Dict]) -> str:
        """格式化效果数据"""
        if not feedback_data:
            return "暂无数据"

        lines = []
        for i, item in enumerate(feedback_data[:10], 1):
            lines.append(
                f"{i}. {item['title'][:30]}... | "
                f"阅读: {item['views']} | "
                f"互动: {item['interactions']} | "
                f"评分: {item['score']}"
            )

        return "\n".join(lines)


if __name__ == '__main__':
    # 测试
    try:
        tracker = FeedbackTracker()
        print("✅ FeedbackTracker 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
