"""
Notion API 客户端
负责将内容写入 Notion 数据库，支持分块写入避免截断
"""
from notion_client import Client
from typing import Dict, List
import time

from modules.utils import setup_logger
from modules.config import NOTION_TOKEN, NOTION_DATABASE_ID

logger = setup_logger('notion_client', 'publisher.log')


class NotionClient:
    """Notion API 客户端"""

    def __init__(self):
        if not NOTION_TOKEN or not NOTION_DATABASE_ID:
            raise ValueError("未配置 NOTION_TOKEN 或 NOTION_DATABASE_ID")

        self.client = Client(auth=NOTION_TOKEN)
        self.database_id = NOTION_DATABASE_ID
        self._db_properties = None

    def _get_database_properties(self) -> Dict:
        """获取数据库属性（缓存）"""
        if self._db_properties is None:
            db = self.client.databases.retrieve(database_id=self.database_id)
            self._db_properties = db.get('properties', {})
        return self._db_properties

    def create_page(self, title: str, format_type: str, content: str, metadata: Dict = None) -> str:
        """创建 Notion 页面（使用分块方案避免截断）"""
        try:
            logger.info(f"创建 Notion 页面: {title[:30]}... (格式: {format_type})")

            # 创建页面（只包含属性，不包含内容）
            # 适配 K博士书稿库的字段结构
            properties = {
                "名称": {  # 使用"名称"而不是"标题"
                    "title": [
                        {
                            "text": {
                                "content": title[:100]  # Notion 标题限制
                            }
                        }
                    ]
                }
            }

            # 添加"类型"字段（对应"格式"）
            if "类型" in self._get_database_properties():
                properties["类型"] = {
                    "select": {
                        "name": format_type
                    }
                }

            # 添加"状态"字段
            if "状态" in self._get_database_properties():
                properties["状态"] = {
                    "select": {
                        "name": "草稿"
                    }
                }

            # 添加"内容"字段（预览，最多2000字符）
            if "内容" in self._get_database_properties():
                # 提取纯文本内容作为预览
                preview = content.replace('#', '').replace('*', '').replace('\n\n', ' ')[:2000]
                properties["内容"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": preview
                            }
                        }
                    ]
                }

            page = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )

            page_id = page['id']
            logger.info(f"页面创建成功: {page_id}")

            # 分块写入内容
            self._append_content_blocks(page_id, content)

            # 添加元数据
            if metadata:
                self._append_metadata_blocks(page_id, metadata)

            logger.info(f"内容写入完成: {page_id}")
            return page_id

        except Exception as e:
            logger.error(f"创建 Notion 页面失败: {str(e)}")
            raise

    def _append_content_blocks(self, page_id: str, content: str):
        """分块追加内容到页面"""
        # Notion API 限制：每次最多100个 blocks，每个 block 最多2000字符
        MAX_BLOCK_SIZE = 1800  # 留一些余量
        MAX_BLOCKS_PER_REQUEST = 90  # 留一些余量

        # 按段落分割内容
        paragraphs = content.split('\n\n')
        blocks = []

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 处理 Markdown 标题
            if para.startswith('# '):
                blocks.append({
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "rich_text": [{"type": "text", "text": {"content": para[2:].strip()[:2000]}}]
                    }
                })
            elif para.startswith('## '):
                blocks.append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"type": "text", "text": {"content": para[3:].strip()[:2000]}}]
                    }
                })
            elif para.startswith('### '):
                blocks.append({
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [{"type": "text", "text": {"content": para[4:].strip()[:2000]}}]
                    }
                })
            else:
                # 普通段落，如果太长则分割
                if len(para) <= MAX_BLOCK_SIZE:
                    blocks.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": para}}]
                        }
                    })
                else:
                    # 分割长段落
                    chunks = [para[i:i+MAX_BLOCK_SIZE] for i in range(0, len(para), MAX_BLOCK_SIZE)]
                    for chunk in chunks:
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            }
                        })

        # 分批追加 blocks
        for i in range(0, len(blocks), MAX_BLOCKS_PER_REQUEST):
            batch = blocks[i:i+MAX_BLOCKS_PER_REQUEST]
            try:
                self.client.blocks.children.append(
                    block_id=page_id,
                    children=batch
                )
                logger.info(f"追加了 {len(batch)} 个 blocks")
                time.sleep(0.5)  # 避免速率限制

            except Exception as e:
                logger.error(f"追加 blocks 失败: {str(e)}")
                raise

    def _append_metadata_blocks(self, page_id: str, metadata: Dict):
        """追加元数据块"""
        try:
            # 添加分隔线
            self.client.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {}
                    },
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"type": "text", "text": {"content": "📊 元数据"}}]
                        }
                    }
                ]
            )

            # 添加元数据
            metadata_text = "\n".join([f"**{k}:** {v}" for k, v in metadata.items()])
            self.client.blocks.children.append(
                block_id=page_id,
                children=[
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": metadata_text[:2000]}}]
                        }
                    }
                ]
            )

        except Exception as e:
            logger.warning(f"追加元数据失败: {str(e)}")

    def update_page_status(self, page_id: str, status: str):
        """更新页面状态"""
        try:
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "状态": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            logger.info(f"页面状态更新为: {status}")

        except Exception as e:
            logger.error(f"更新页面状态失败: {str(e)}")
            raise


if __name__ == '__main__':
    # 测试
    try:
        client = NotionClient()
        page_id = client.create_page(
            title="测试页面",
            format_type="测试",
            content="# 测试标题\n\n这是测试内容。\n\n## 子标题\n\n更多内容...",
            metadata={"来源": "测试", "字数": "100"}
        )
        print(f"创建成功: {page_id}")

    except Exception as e:
        print(f"测试失败: {str(e)}")
