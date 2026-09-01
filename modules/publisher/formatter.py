"""
Markdown 转微信 HTML 格式化工具
"""
import markdown

from modules.utils import setup_logger

logger = setup_logger('formatter', 'publisher.log')


class WechatFormatter:
    """微信公众号格式化工具"""

    def __init__(self):
        self.md = markdown.Markdown(extensions=['extra', 'codehilite'])

    def markdown_to_wechat_html(self, md_content: str) -> str:
        """将 Markdown 转换为微信公众号可用的 HTML"""
        try:
            # 转换为 HTML
            html = self.md.convert(md_content)

            # 添加微信公众号样式
            styled_html = self._apply_wechat_styles(html)

            logger.info("Markdown 转换为微信 HTML 成功")
            return styled_html

        except Exception as e:
            logger.error(f"Markdown 转换失败: {str(e)}")
            return md_content

    def _apply_wechat_styles(self, html: str) -> str:
        """应用微信公众号样式"""
        # 简单的样式替换
        # 实际使用时可以用更复杂的 CSS 样式

        styles = """
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.8;
    color: #333;
    padding: 20px;
}

h1 {
    font-size: 24px;
    font-weight: bold;
    color: #000;
    margin: 20px 0 10px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid #3f51b5;
}

h2 {
    font-size: 20px;
    font-weight: bold;
    color: #000;
    margin: 18px 0 8px 0;
}

h3 {
    font-size: 18px;
    font-weight: bold;
    color: #333;
    margin: 16px 0 6px 0;
}

p {
    margin: 10px 0;
    text-align: justify;
}

strong {
    color: #3f51b5;
    font-weight: bold;
}

em {
    font-style: italic;
    color: #666;
}

blockquote {
    border-left: 4px solid #3f51b5;
    padding-left: 15px;
    margin: 15px 0;
    color: #666;
    background: #f5f5f5;
}

ul, ol {
    margin: 10px 0;
    padding-left: 25px;
}

li {
    margin: 5px 0;
}

code {
    background: #f5f5f5;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: "Courier New", monospace;
    color: #e91e63;
}

pre {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 5px;
    overflow-x: auto;
}
</style>
"""

        return f"{styles}\n{html}"


if __name__ == '__main__':
    # 测试
    formatter = WechatFormatter()

    test_md = """
# 测试标题

这是一段**加粗**的文字，还有*斜体*。

## 子标题

- 列表项1
- 列表项2
- 列表项3

> 这是一段引用

这是`代码`示例。
"""

    html = formatter.markdown_to_wechat_html(test_md)
    print(html[:500])
