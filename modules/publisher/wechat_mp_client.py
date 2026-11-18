"""
微信公众号草稿箱客户端
推送文章到草稿箱，支持带封面图
"""
import os
import requests
import json
import time
from pathlib import Path
from typing import Optional, Dict

from modules.utils import setup_logger

logger = setup_logger('wechat_mp', 'publisher.log')

_token_cache: Dict[str, float] = {}  # {token: expires_at}


class WechatMPClient:
    """微信公众号 API 客户端"""

    def __init__(self):
        self.appid = os.getenv('WECHAT_APPID', '').strip()
        self.secret = os.getenv('WECHAT_SECRET', '').strip()
        if not self.appid or not self.secret:
            raise ValueError("WECHAT_APPID 或 WECHAT_SECRET 未配置")
        self._access_token: Optional[str] = None
        self._token_expires: float = 0

    @property
    def available(self) -> bool:
        return bool(self.appid and self.secret)

    def _get_access_token(self) -> str:
        """获取 access_token（有效期 2 小时，自动续期）"""
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token

        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": self.appid,
            "secret": self.secret,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "errcode" in data:
            raise RuntimeError(f"获取 access_token 失败: {data}")

        self._access_token = data["access_token"]
        self._token_expires = time.time() + data["expires_in"]
        logger.info("access_token 已更新")
        return self._access_token

    def upload_image(self, image_path: str) -> str:
        """上传永久素材（封面图），返回 media_id"""
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image"
        with open(image_path, 'rb') as f:
            resp = requests.post(url, files={"media": f}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "errcode" in data and data["errcode"] != 0:
            raise RuntimeError(f"上传封面图失败: {data}")
        media_id = data.get("media_id", "")
        logger.info(f"封面图上传成功: media_id={media_id}")
        return media_id

    def add_draft(self, title: str, content_html: str, digest: str = "",
                  author: str = "", thumb_media_id: str = "") -> str:
        """
        新建草稿，返回 media_id

        Args:
            title: 文章标题
            content_html: 正文 HTML（微信公众号格式）
            digest: 摘要（可选）
            author: 作者（可选）
            thumb_media_id: 封面图素材 ID（可选）
        Returns:
            草稿 media_id
        """
        token = self._get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}"

        article = {
            "title": title[:64],
            "content": content_html,
            "author": author,
            "digest": digest[:120] if digest else title[:120],
            "content_source_url": "",
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }
        if thumb_media_id:
            article["thumb_media_id"] = thumb_media_id

        payload = {"articles": [article]}
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"创建草稿失败: {data}")

        media_id = data.get("media_id", "")
        logger.info(f"草稿创建成功: media_id={media_id}")
        return media_id

    def push_article_draft(self, title: str, markdown_content: str,
                           image_path: Optional[str] = None) -> Dict:
        """
        一键推送到草稿箱
        1. 若有封面图，先上传拿 media_id
        2. 把 markdown 转为微信 HTML
        3. 调 draft/add

        Returns:
            {'success': bool, 'media_id': str, 'error': str}
        """
        try:
            thumb_media_id = ""
            if image_path and Path(image_path).exists():
                thumb_media_id = self.upload_image(image_path)

            content_html = _markdown_to_wechat_html(markdown_content)

            # 从内容提取摘要（取第一段非标题行）
            lines = [l.strip() for l in markdown_content.splitlines() if l.strip() and not l.startswith('#')]
            digest = lines[0][:120] if lines else title

            media_id = self.add_draft(
                title=title,
                content_html=content_html,
                digest=digest,
                thumb_media_id=thumb_media_id,
            )
            return {"success": True, "media_id": media_id}
        except Exception as e:
            logger.error(f"推送草稿失败: {e}")
            return {"success": False, "media_id": "", "error": str(e)}


def _markdown_to_wechat_html(md: str) -> str:
    """简单 Markdown → 微信公众号 HTML（不引入额外依赖）"""
    import re
    lines = md.splitlines()
    html_parts = []
    for line in lines:
        line = line.rstrip()
        if not line:
            html_parts.append('<p><br/></p>')
            continue
        # 标题
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m:
            level = len(m.group(1))
            tag = f'h{min(level+1, 4)}'
            text = _inline(m.group(2))
            style = 'font-size:18px;font-weight:bold;color:#1a1510;margin:16px 0 8px' if level == 1 else 'font-size:16px;font-weight:bold;color:#2a241c;margin:12px 0 6px'
            html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            continue
        # 无序列表
        if re.match(r'^[-*]\s+', line):
            text = _inline(re.sub(r'^[-*]\s+', '', line))
            html_parts.append(f'<p style="padding-left:1em;margin:4px 0">· {text}</p>')
            continue
        # 普通段落
        html_parts.append(f'<p style="margin:8px 0;line-height:1.8;font-size:15px;color:#333">{_inline(line)}</p>')

    return '\n'.join(html_parts)


def _inline(text: str) -> str:
    import re
    # 粗体
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # 斜体
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # 行内代码
    text = re.sub(r'`(.+?)`', r'<code style="background:#f5f0e8;padding:1px 4px">\1</code>', text)
    return text
