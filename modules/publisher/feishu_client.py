"""
飞书文档发布器 - 将内容发布到飞书文档
"""
import os
from typing import Dict, Optional
from datetime import datetime
import lark_oapi as lark
from lark_oapi.api.docx.v1 import *

from modules.utils import setup_logger

logger = setup_logger('feishu_publisher', 'publisher.log')


class FeishuPublisher:
    """飞书文档发布器"""

    def __init__(self):
        self.app_id = os.getenv('FEISHU_APP_ID')
        self.app_secret = os.getenv('FEISHU_APP_SECRET')
        self.doc_token = os.getenv('FEISHU_DOC_TOKEN', 'FQKKdaTb6oxOBIxceIOciEK3nFe')

        if self.app_id and self.app_secret:
            self.client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()
            self.available = True
            logger.info("✅ 飞书 API 初始化成功")
        else:
            self.available = False
            logger.warning("⚠️ 飞书 API 未配置")

    def publish_draft(self, draft: Dict) -> Optional[str]:
        """
        发布草稿到飞书文档

        Args:
            draft: 草稿内容

        Returns:
            飞书文档链接
        """
        if not self.available:
            logger.warning("飞书 API 未配置，跳过发布")
            return None

        try:
            logger.info(f"发布到飞书: {draft.get('topic', {}).get('title', '')[:30]}...")

            # 构建文档内容
            content = self._build_document_content(draft)

            # 追加到飞书文档
            request = CreateDocumentBlockChildrenRequest.builder() \
                .document_id(self.doc_token) \
                .block_id(self._get_root_block_id()) \
                .request_body(CreateDocumentBlockChildrenRequestBody.builder()
                    .children(content)
                    .build()) \
                .build()

            response = self.client.docx.v1.document_block_children.create(request)

            if response.success():
                doc_url = f"https://g71kfep2ds.feishu.cn/docx/{self.doc_token}"
                logger.info(f"✅ 发布成功: {doc_url}")
                return doc_url
            else:
                logger.error(f"❌ 发布失败: {response.msg}")
                return None

        except Exception as e:
            logger.error(f"发布到飞书失败: {str(e)}")
            return None

    def _get_root_block_id(self) -> str:
        """获取文档根 block ID"""
        try:
            request = GetDocumentRequest.builder() \
                .document_id(self.doc_token) \
                .build()

            response = self.client.docx.v1.document.get(request)

            if response.success():
                return response.data.document.block_id
            else:
                logger.error(f"获取文档信息失败: {response.msg}")
                return ""

        except Exception as e:
            logger.error(f"获取根 block ID 失败: {str(e)}")
            return ""

    def _build_document_content(self, draft: Dict) -> list:
        """构建飞书文档内容结构"""

        topic = draft.get('topic', {})
        title = topic.get('title', '')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        blocks = []

        # 标题
        blocks.append({
            "block_type": 2,  # 标题1
            "heading1": {
                "elements": [{"text_run": {"content": f"📝 {title}"}}]
            }
        })

        # 时间戳
        blocks.append({
            "block_type": 3,  # 正文
            "text": {
                "elements": [{"text_run": {"content": f"生成时间: {timestamp}"}}]
            }
        })

        # 分隔线
        blocks.append({"block_type": 3, "text": {"elements": [{"text_run": {"content": "---"}}]}})

        # 各平台内容
        formats = [
            ('video_script', '🎬 视频号文案'),
            ('wechat_article', '📰 公众号文章'),
            ('moments', '💬 朋友圈文案'),
            ('xiaohongshu', '📱 小红书文案'),
            ('book_material', '📚 书稿素材')
        ]

        for key, label in formats:
            if key in draft and draft[key]:
                # 格式标题
                blocks.append({
                    "block_type": 4,  # 标题2
                    "heading2": {
                        "elements": [{"text_run": {"content": label}}]
                    }
                })

                # 内容
                content = draft[key]
                # 分段处理
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        blocks.append({
                            "block_type": 3,
                            "text": {
                                "elements": [{"text_run": {"content": para.strip()}}]
                            }
                        })

        # 底部分隔
        blocks.append({"block_type": 3, "text": {"elements": [{"text_run": {"content": "\n" + "="*50 + "\n"}}]}})

        return blocks


# 测试代码
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    publisher = FeishuPublisher()

    test_draft = {
        'topic': {'title': 'AI时代教育测试'},
        'video_script': '这是视频号文案...',
        'wechat_article': '这是公众号文章...',
        'xiaohongshu': '这是小红书文案...'
    }

    url = publisher.publish_draft(test_draft)
    print(f"发布结果: {url}")
