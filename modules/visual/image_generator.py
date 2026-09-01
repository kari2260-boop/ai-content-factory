"""
图片生成器 - 支持多种 AI 图片生成服务
"""
import os
import re
import requests
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict
import base64
from datetime import datetime

from modules.utils import setup_logger

logger = setup_logger('image_generator', 'visual.log')


class ImageGenerator:
    """AI 图片生成器"""

    PLATFORM_CONFIG = {
        'wechat': {
            'label': '公众号封面',
            'size': '1536x1024',
            'style': 'educational',
            'prompt_hint': '公众号首图封面，横版编辑部封面构图，专业可信，像优质中文深度文章首图，左侧或下方留出标题空间',
            'overlay': {
                'box': (0.06, 0.13, 0.62, 0.75),
                'title_ratio': 0.052,
                'subtitle_ratio': 0.020,
                'align': 'left',
                'panel': False,
                'scrim': True,
                'title_max_lines': 4,
                'title_fill': (248, 250, 252, 255),
                'subtitle_fill': (210, 219, 232, 235),
            },
        },
        'xiaohongshu': {
            'label': '小红书封面',
            'size': '1024x1536',
            'style': 'colorful',
            'prompt_hint': '小红书首图封面，竖版构图，强钩子视觉，适合知识图文和收藏型内容，画面信息更密、标题更短更狠',
            'overlay': {
                'box': (0.08, 0.11, 0.90, 0.66),
                'title_ratio': 0.066,
                'subtitle_ratio': 0.026,
                'align': 'left',
                'panel': False,
                'scrim': True,
                'title_max_lines': 3,
                'title_fill': (20, 24, 35, 255),
                'subtitle_fill': (78, 90, 112, 238),
            },
        },
        'video': {
            'label': '视频号封面',
            'size': '1536x1024',
            'style': 'modern',
            'prompt_hint': '视频号封面，横版强焦点，远距离也能识别主题，适合叠加大标题',
            'overlay': {
                'box': (0.08, 0.18, 0.84, 0.70),
                'title_ratio': 0.062,
                'subtitle_ratio': 0.024,
                'align': 'center',
                'panel': False,
                'scrim': True,
                'title_max_lines': 3,
                'title_fill': (248, 250, 252, 255),
                'subtitle_fill': (210, 219, 232, 235),
            },
        },
        'moments': {
            'label': '朋友圈配图',
            'size': '1024x1024',
            'style': 'minimalist',
            'prompt_hint': '朋友圈配图，方图，温暖、真实、轻松，不像广告海报',
            'overlay': {
                'box': (0.08, 0.14, 0.84, 0.58),
                'title_ratio': 0.052,
                'subtitle_ratio': 0.022,
                'align': 'left',
                'panel': False,
                'scrim': True,
                'title_max_lines': 4,
                'title_fill': (248, 250, 252, 255),
                'subtitle_fill': (210, 219, 232, 235),
            },
        },
    }

    def __init__(self):
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.replicate_key = os.getenv('REPLICATE_API_TOKEN')
        self.youmind_key = os.getenv('YOUMIND_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.output_dir = Path('data/images')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.gpt_image_skill_script = Path.home() / '.agents' / 'skills' / 'gpt-image' / 'scripts' / 'generate.py'

        # 初始化 YouMind 客户端
        self.youmind = None
        if self.youmind_key:
            try:
                from modules.visual.youmind_client import YouMindClient
                self.youmind = YouMindClient()
            except Exception as e:
                logger.warning(f"YouMind 初始化失败: {e}")

        # 初始化 Gemini 客户端
        self.gemini = None
        if self.gemini_key:
            try:
                from modules.generator.gemini_client import GeminiClient
                self.gemini = GeminiClient()
                if self.gemini.available and self.gemini.use_proxy:
                    logger.info("Gemini 图片生成已就绪")
            except Exception as e:
                logger.warning(f"Gemini 初始化失败: {e}")

    def generate_cover_image(
        self,
        title: str,
        style: str = "educational",
        platform: str = "wechat",
        content: str = "",
        custom_prompt: str = "",
        preferred_provider: str = "auto"
    ) -> Optional[str]:
        """
        生成封面图

        Args:
            title: 内容标题
            style: 风格 (educational, modern, minimalist, colorful)
            platform: 平台 (wechat, xiaohongshu, video)
            content: 正文内容，用于提炼画面主题
            custom_prompt: 用户补充的视觉要求
            preferred_provider: auto/skill/openai/youmind/gemini/flux

        Returns:
            图片文件路径
        """
        logger.info(f"生成封面图: {title[:30]}... | 平台: {platform}")

        config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])
        if not style:
            style = config['style']

        # 根据平台选择尺寸
        size = self._get_platform_size(platform)

        # 构建提示词
        prompt = self._build_prompt(title, style, platform, content, custom_prompt)

        providers = self._get_provider_order(preferred_provider)
        for provider in providers:
            image_path = self._try_generate_with_provider(provider, prompt, size, style)
            if image_path:
                return image_path

        logger.warning("未配置可用的图片生成 API，或所有图片服务均生成失败")
        return None

    def generate_platform_cover(
        self,
        title: str,
        content: str,
        platform: str,
        subtitle: str = "",
        style: Optional[str] = None,
        custom_prompt: str = "",
        preferred_provider: str = "auto",
        overlay_text: bool = True,
        feedback: str = "",
        source_image: Optional[str] = None
    ) -> Optional[str]:
        """生成平台封面：先生成无字底图，再可选叠加准确文字；有反馈时可基于上一张图修改。"""
        base_prompt = custom_prompt.strip()
        textless_direction = (
            "Generate a clean textless background image. Leave enough negative space for later title overlay. "
            "Do not render any words, letters, Chinese characters, numbers, labels, watermarks, captions, or UI text."
        )
        feedback_direction = ""
        if feedback:
            feedback_direction = (
                "Revision request from user: "
                f"{feedback.strip()}. Keep the image connected to the article content and platform usage."
            )
        prompt = "\n".join(part for part in [base_prompt, feedback_direction, textless_direction] if part).strip()

        image_path = None
        if source_image and feedback:
            image_path = self.edit_platform_cover(
                source_image=source_image,
                title=title,
                content=content,
                platform=platform,
                feedback=feedback,
                custom_prompt=base_prompt,
                preferred_provider=preferred_provider
            )

        if not image_path:
            image_path = self.generate_platform_image(
                title=title,
                content=content,
                platform=platform,
                style=style,
                custom_prompt=prompt,
                preferred_provider=preferred_provider
            )
        if not image_path:
            return None

        if not overlay_text:
            return image_path

        return self.add_text_overlay(
            image_path=image_path,
            title=title,
            subtitle=subtitle,
            platform=platform
        )

    def edit_platform_cover(
        self,
        source_image: str,
        title: str,
        content: str,
        platform: str,
        feedback: str,
        custom_prompt: str = "",
        preferred_provider: str = "auto"
    ) -> Optional[str]:
        """基于上一张配图和用户反馈做图生图修改。当前本地 gpt-image skill 最稳定。"""
        if not source_image or not Path(source_image).exists():
            return None

        providers = self._get_provider_order(preferred_provider)
        if 'skill' not in providers:
            return None

        config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])
        content_brief = self._build_visual_brief(title, content, platform)
        prompt = f"""Edit this existing cover image for {config['label']}.
Article title: {title}
Article visual brief:
{content_brief}
User revision feedback: {feedback.strip()}
Extra direction: {custom_prompt.strip() if custom_prompt else 'none'}

Keep the useful composition of the previous image when possible, but fix the user's feedback.
Make the result more specifically related to the article argument, not a generic AI/education picture.
Leave clean negative space for later title overlay.
Do not render readable text, letters, Chinese characters, numbers, labels, watermarks, captions, or logos."""

        return self._generate_with_gpt_image_skill(prompt, image_path=source_image)

    def _get_provider_order(self, preferred_provider: str) -> list:
        """根据用户选择决定服务顺序。"""
        provider_map = {
            'openai': ['openai'],
            'dalle': ['openai'],
            'skill': ['skill'],
            'gpt-image': ['skill'],
            'gpt_image': ['skill'],
            'youmind': ['youmind'],
            'gemini': ['gemini'],
            'flux': ['flux'],
            'replicate': ['flux'],
        }
        if preferred_provider in provider_map:
            return provider_map[preferred_provider]
        return ['skill', 'openai', 'youmind', 'gemini', 'flux']

    def _try_generate_with_provider(self, provider: str, prompt: str, size: str, style: str) -> Optional[str]:
        """单个服务尝试失败时返回 None，让上层继续兜底。"""
        try:
            if provider == 'skill' and self.gpt_image_skill_script.exists():
                return self._generate_with_gpt_image_skill(prompt)

            if provider == 'openai' and self.openai_key:
                return self._generate_openai_image(prompt, size)

            if provider == 'youmind' and self.youmind and self.youmind.available:
                youmind_style = self.youmind._map_style(style)
                return self.youmind.generate_image(prompt, style=youmind_style, size=size)

            if provider == 'gemini' and self.gemini and self.gemini.available and getattr(self.gemini, 'use_proxy', False):
                return self.gemini.generate_image(prompt, size=size)

            if provider == 'flux' and self.replicate_key:
                return self._generate_flux(prompt, size)

        except Exception as e:
            logger.warning(f"{provider} 图片生成失败: {e}")

        return None

    def _generate_with_gpt_image_skill(self, prompt: str, image_path: Optional[str] = None) -> Optional[str]:
        """调用用户本地 gpt-image skill 脚本生成图片。"""
        try:
            logger.info("使用本地 gpt-image skill 生成图片")
            output_dir = self.output_dir / 'gpt_skill'
            output_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                sys.executable,
                str(self.gpt_image_skill_script),
                prompt,
                '--n',
                '1',
                '--output',
                str(output_dir)
            ]
            if image_path:
                cmd.extend(['--image', image_path])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=240,
                check=False
            )

            if result.returncode != 0:
                logger.warning(f"gpt-image skill 失败: {result.stderr or result.stdout}")
                return None

            image_path = self._extract_generated_path(result.stdout, output_dir)
            if image_path:
                logger.info(f"✅ gpt-image skill 图片生成成功: {image_path}")
                return str(image_path)

            logger.warning(f"gpt-image skill 未返回图片路径: {result.stdout}")
            return None

        except Exception as e:
            logger.warning(f"gpt-image skill 调用失败: {e}")
            return None

    def _extract_generated_path(self, output: str, output_dir: Path) -> Optional[Path]:
        """从 skill 输出中提取图片路径，失败时取目录内最新 PNG。"""
        for line in output.splitlines():
            if '已保存:' in line:
                candidate = line.split('已保存:', 1)[1].strip()
                path = Path(candidate)
                if path.exists():
                    return path

        images = sorted(output_dir.glob('*.png'), key=lambda p: p.stat().st_mtime, reverse=True)
        return images[0] if images else None

    def _get_platform_size(self, platform: str) -> str:
        """获取平台推荐尺寸"""
        config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])
        return config['size']

    def add_text_overlay(self, image_path: str, title: str, subtitle: str = "", platform: str = "wechat") -> Optional[str]:
        """给图片叠加中英文标题，避免 AI 直接画字导致错字。"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logger.warning("Pillow 未安装，跳过文字叠加")
            return image_path

        try:
            src_path = Path(image_path)
            image = Image.open(src_path).convert("RGBA")
            width, height = image.size
            config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])
            overlay_config = config.get('overlay', self.PLATFORM_CONFIG['wechat']['overlay'])
            x1r, y1r, x2r, y2r = overlay_config['box']
            box = (
                int(width * x1r),
                int(height * y1r),
                int(width * x2r),
                int(height * y2r)
            )

            layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer)

            if overlay_config.get('scrim'):
                self._draw_scrim(layer, platform)
                draw = ImageDraw.Draw(layer)

            if overlay_config.get('panel', True):
                panel_pad = int(width * 0.025)
                panel_box = (
                    max(0, box[0] - panel_pad),
                    max(0, box[1] - panel_pad),
                    min(width, box[2] + panel_pad),
                    min(height, box[3] + panel_pad)
                )
                try:
                    draw.rounded_rectangle(panel_box, radius=int(width * 0.025), fill=(255, 255, 255, 218))
                except AttributeError:
                    draw.rectangle(panel_box, fill=(255, 255, 255, 218))

            title_max_lines = overlay_config.get('title_max_lines', 4)
            title_font = self._fit_font(
                text=title,
                initial_size=int(width * overlay_config['title_ratio']),
                min_size=int(width * 0.034),
                max_width=box[2] - box[0],
                max_height=box[3] - box[1],
                max_lines=title_max_lines,
                draw=draw,
                bold=True
            )
            subtitle_font = self._load_font(int(width * overlay_config['subtitle_ratio']), bold=False)
            title_lines = self._wrap_text(title, title_font, box[2] - box[0], draw, max_lines=title_max_lines)
            subtitle_lines = self._wrap_text(subtitle, subtitle_font, box[2] - box[0], draw, max_lines=2) if subtitle else []

            line_gap = int(height * 0.018)
            subtitle_gap = int(height * 0.028) if subtitle_lines else 0
            title_height = sum(self._text_size(draw, line, title_font)[1] for line in title_lines)
            title_height += max(0, len(title_lines) - 1) * line_gap
            subtitle_height = sum(self._text_size(draw, line, subtitle_font)[1] for line in subtitle_lines)
            subtitle_height += max(0, len(subtitle_lines) - 1) * int(line_gap * 0.7)
            total_height = title_height + subtitle_gap + subtitle_height

            y = box[1] + max(0, ((box[3] - box[1]) - total_height) // 2)
            align = overlay_config.get('align', 'left')
            title_fill = tuple(overlay_config.get('title_fill', (23, 28, 40, 255)))
            subtitle_fill = tuple(overlay_config.get('subtitle_fill', (71, 83, 103, 238)))

            for line in title_lines:
                text_width, text_height = self._text_size(draw, line, title_font)
                x = self._aligned_x(box, text_width, align)
                self._draw_text_with_shadow(draw, (x, y), line, title_font, fill=title_fill)
                y += text_height + line_gap

            if subtitle_lines:
                y += subtitle_gap
                for line in subtitle_lines:
                    text_width, text_height = self._text_size(draw, line, subtitle_font)
                    x = self._aligned_x(box, text_width, align)
                    draw.text((x, y), line, font=subtitle_font, fill=subtitle_fill)
                    y += text_height + int(line_gap * 0.7)

            if platform == 'xiaohongshu':
                self._draw_xhs_badge(layer, box, width)

            final = Image.alpha_composite(image, layer).convert("RGB")
            output_path = src_path.with_name(f"{src_path.stem}_text.png")
            final.save(output_path, quality=95)
            logger.info(f"✅ 图片文字叠加完成: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.warning(f"图片文字叠加失败: {e}")
            return image_path

    def _load_font(self, size: int, bold: bool = False):
        """加载支持中文的系统字体。"""
        from PIL import ImageFont

        if bold:
            candidates = [
                str(Path.home() / "Library/Fonts/NotoSansSC-Bold.otf"),
                "/System/Library/Fonts/STHeiti Medium.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/System/Library/Fonts/HelveticaNeue.ttc",
            ]
        else:
            candidates = [
                str(Path.home() / "Library/Fonts/NotoSansSC-Regular.otf"),
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]

        for font_path in candidates:
            if Path(font_path).exists():
                try:
                    return ImageFont.truetype(font_path, size=size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _draw_scrim(self, layer, platform: str):
        """绘制克制的渐变遮罩，保证标题可读但不遮死底图。"""
        from PIL import Image, ImageDraw

        width, height = layer.size
        gradient = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(gradient)

        if platform in ("wechat", "moments"):
            for x in range(width):
                ratio = 1 - min(1, x / (width * 0.72))
                alpha = int(150 * (ratio ** 1.8))
                gdraw.line([(x, 0), (x, height)], fill=(8, 12, 18, alpha))
            for y in range(height):
                ratio = 1 - min(1, y / (height * 0.92))
                alpha = int(45 * (ratio ** 2))
                gdraw.line([(0, y), (width, y)], fill=(8, 12, 18, alpha))
        else:
            for y in range(height):
                ratio = 1 - min(1, abs(y - height * 0.46) / (height * 0.46))
                alpha = int(128 * max(0, ratio) ** 1.7)
                gdraw.line([(0, y), (width, y)], fill=(8, 12, 18, alpha))

        layer.alpha_composite(gradient)

    def _fit_font(
        self,
        text: str,
        initial_size: int,
        min_size: int,
        max_width: int,
        max_height: int,
        max_lines: int,
        draw,
        bold: bool = True
    ):
        """根据标题长度自动缩字号，避免封面字压满画面。"""
        size = initial_size
        while size >= min_size:
            font = self._load_font(size, bold=bold)
            lines = self._wrap_text(text, font, max_width, draw, max_lines=max_lines)
            line_heights = [self._text_size(draw, line, font)[1] for line in lines]
            total_height = sum(line_heights) + max(0, len(lines) - 1) * int(size * 0.24)
            if len(lines) <= max_lines and total_height <= max_height * 0.82:
                return font
            size -= 4
        return self._load_font(min_size, bold=bold)

    def _wrap_text(self, text: str, font, max_width: int, draw, max_lines: int = 3) -> list:
        """按像素宽度换行，兼容中文无空格文本。"""
        if not text:
            return []

        units = []
        buffer = ""
        for char in text.strip():
            if char.isspace():
                if buffer:
                    units.append(buffer)
                    buffer = ""
                units.append(" ")
            elif ord(char) < 128:
                buffer += char
            else:
                if buffer:
                    units.append(buffer)
                    buffer = ""
                units.append(char)
        if buffer:
            units.append(buffer)

        lines = []
        current = ""
        for unit in units:
            candidate = (current + unit).strip() if unit != " " else current + unit
            if not candidate:
                continue
            if self._text_size(draw, candidate, font)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current.strip())
                current = unit.strip()
                if len(lines) >= max_lines:
                    break
        if current and len(lines) < max_lines:
            lines.append(current.strip())

        if len(lines) == max_lines and len("".join(lines)) < len(text.strip()):
            last = lines[-1]
            while last and self._text_size(draw, last + "...", font)[0] > max_width:
                last = last[:-1]
            lines[-1] = last + "..."
        return lines

    def _text_size(self, draw, text: str, font) -> tuple:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _aligned_x(self, box: tuple, text_width: int, align: str) -> int:
        if align == 'center':
            return box[0] + max(0, ((box[2] - box[0]) - text_width) // 2)
        if align == 'right':
            return box[2] - text_width
        return box[0]

    def _draw_text_with_shadow(self, draw, position: tuple, text: str, font, fill: tuple):
        x, y = position
        shadow_alpha = 130 if fill[0] > 200 else 190
        shadow_fill = (0, 0, 0, shadow_alpha) if fill[0] > 200 else (255, 255, 255, shadow_alpha)
        draw.text((x + 2, y + 2), text, font=font, fill=shadow_fill)
        draw.text((x, y), text, font=font, fill=fill)

    def _draw_xhs_badge(self, layer, box: tuple, width: int):
        """给小红书封面增加更像平台的轻量标签。"""
        from PIL import ImageDraw

        draw = ImageDraw.Draw(layer)
        badge_pad_x = int(width * 0.028)
        badge_pad_y = int(width * 0.010)
        badge_text = "小红书图文"
        font = self._load_font(int(width * 0.022), bold=True)
        temp_draw = ImageDraw.Draw(layer)
        text_w, text_h = self._text_size(temp_draw, badge_text, font)
        badge_box = (
            box[0],
            max(0, box[1] - int(width * 0.052)),
            box[0] + text_w + badge_pad_x * 2,
            max(0, box[1] - int(width * 0.052)) + text_h + badge_pad_y * 2
        )
        try:
            draw.rounded_rectangle(badge_box, radius=int(width * 0.018), fill=(255, 72, 120, 235))
        except AttributeError:
            draw.rectangle(badge_box, fill=(255, 72, 120, 235))
        draw.text((badge_box[0] + badge_pad_x, badge_box[1] + badge_pad_y), badge_text, font=font, fill=(255, 255, 255, 255))

    def _build_prompt(
        self,
        title: str,
        style: str,
        platform: str,
        content: str = "",
        custom_prompt: str = ""
    ) -> str:
        """构建图片生成提示词"""

        style_prompts = {
            'educational': 'premium editorial cover, documentary realism, refined education and research visual language, subtle warm light, restrained palette',
            'modern': 'premium editorial poster, cinematic realism, modern magazine cover composition, strong silhouette, controlled contrast',
            'minimalist': 'quiet editorial photography, clean composition, warm real-life detail, restrained colors, generous negative space',
            'colorful': 'premium social-media editorial card, strong visual hook, refined color accents, clean hierarchy, not childish'
        }

        base_style = style_prompts.get(style, style_prompts['educational'])
        config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])
        platform_hint = config['prompt_hint']
        content_brief = self._build_visual_brief(title, content, platform)

        prompt = f"""Create a {base_style} cover image for an article titled "{title}".
Platform and usage: {platform_hint}.
Article visual brief:
{content_brief if content_brief else 'Core topic: AI, education, family growth, knowledge work, and practical insight.'}
Recommended aesthetic:
{self._get_aesthetic_direction(platform)}
Visual direction: high quality, professional, suitable for Chinese education and creator content. The image must clearly reflect the article's specific argument, not a generic AI illustration.
Layout: one strong visual metaphor connected to the topic, 2-3 supporting scene details from the article, clear foreground/background depth, clean negative space for a title overlay.
Composition rule: no large blank rounded rectangle, no fake text panel, no poster template blocks generated by the model. The title will be added later by software.
Constraints: no readable text, no logos, no watermark, no QR code, no fake Chinese characters.
Avoid: cluttered UI, stock-photo feeling, dark blue/purple gradient dominance, childish cartoon style, cheap PPT look, overexposed beige background, random tiny people in empty architecture."""

        if custom_prompt:
            prompt += f"\nExtra user direction: {custom_prompt}"

        return prompt

    def _get_aesthetic_direction(self, platform: str) -> str:
        """平台审美默认值，减少廉价模板感。"""
        directions = {
            'wechat': (
                "Think of The New Yorker / Wired / Bloomberg-style editorial cover adapted for Chinese WeChat articles: "
                "a concrete documentary scene or symbolic still life, cinematic but calm, academic credibility, "
                "paper texture or real environment detail, sophisticated cropping, left-side shadow space for software title overlay."
            ),
            'xiaohongshu': (
                "A high-end Xiaohongshu knowledge-card cover: bold hook headline area, one memorable central object, "
                "bright controlled accents, realistic material detail, clear visual hierarchy, high save/share energy, "
                "designed like a vertical knowledge note with compressed information and stronger contrast."
            ),
            'video': (
                "A video thumbnail with one instantly readable scene, cinematic lighting, strong subject contrast, "
                "less than three visual ideas, enough dark negative space for large software title overlay."
            ),
            'moments': (
                "A warm editorial lifestyle image, real and conversational, like a thoughtful personal essay cover, "
                "not advertising, not poster-heavy, with quiet emotional detail."
            ),
        }
        return directions.get(platform, directions['wechat'])

    def _build_visual_brief(self, title: str, content: str, platform: str) -> str:
        """把正文压成图片模型能理解的视觉 brief。"""
        lines = self._extract_content_lines(content)
        keywords = self._extract_keywords(f"{title}\n{content}")
        core_lines = lines[:5]
        config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])

        if not core_lines and not keywords:
            return ""

        parts = [
            f"Core topic: {title}",
            f"Platform tone: {config['prompt_hint']}",
        ]
        if keywords:
            parts.append(f"Important entities and motifs: {', '.join(keywords[:10])}")
        if core_lines:
            parts.append("Key article points to visualize:")
            for idx, line in enumerate(core_lines, 1):
                parts.append(f"{idx}. {line}")
        parts.append(
            "Suggested metaphor: turn the article argument into a concrete scene with people, objects, environment, or editorial symbols that match the content."
        )
        return "\n".join(parts)

    def _extract_content_lines(self, content: str, max_lines: int = 6) -> list:
        """提取正文中最适合转成画面的短句。"""
        if not content:
            return []

        cleaned = content.replace("\r", "\n")
        raw_parts = re.split(r"[\n。！？!?；;]+", cleaned)
        lines = []
        skip_prefixes = ("#", "-", "*", "字数", "标题", "开头", "正文", "结尾")
        for part in raw_parts:
            line = re.sub(r"\s+", " ", part).strip(" #*-_`0123456789.、")
            if len(line) < 8:
                continue
            if any(line.startswith(prefix) for prefix in skip_prefixes):
                continue
            if len(line) > 90:
                line = line[:90]
            lines.append(line)
            if len(lines) >= max_lines:
                break
        return lines

    def _extract_keywords(self, text: str, max_keywords: int = 12) -> list:
        """从标题和正文中抓取高频关键词，避免 prompt 跑偏。"""
        if not text:
            return []

        candidates = re.findall(r"[A-Za-z][A-Za-z0-9.+#-]{1,}|[\u4e00-\u9fff]{2,8}", text)
        stopwords = {
            "这个", "一个", "我们", "你们", "他们", "但是", "所以", "因为", "如果", "不是", "没有",
            "什么", "怎么", "可以", "需要", "孩子", "家长", "教育", "内容", "生成", "平台", "文章"
        }
        counts = {}
        for word in candidates:
            word = word.strip()
            if len(word) < 2 or word in stopwords:
                continue
            counts[word] = counts.get(word, 0) + 1
        return [word for word, _ in sorted(counts.items(), key=lambda item: (-item[1], -len(item[0])))[:max_keywords]]

    def _summarize_content_for_prompt(self, content: str, max_chars: int = 500) -> str:
        """压缩正文，避免把整篇文章塞进图片模型。"""
        if not content:
            return ""

        cleaned = " ".join(content.replace("#", " ").replace("*", " ").split())
        return cleaned[:max_chars]

    def generate_platform_image(
        self,
        title: str,
        content: str,
        platform: str,
        style: Optional[str] = None,
        custom_prompt: str = "",
        preferred_provider: str = "auto"
    ) -> Optional[str]:
        """结合平台和正文生成单张配图。"""
        config = self.PLATFORM_CONFIG.get(platform, self.PLATFORM_CONFIG['wechat'])
        return self.generate_cover_image(
            title=title,
            style=style or config['style'],
            platform=platform,
            content=content,
            custom_prompt=custom_prompt,
            preferred_provider=preferred_provider
        )

    def _generate_openai_image(self, prompt: str, size: str) -> Optional[str]:
        """使用 OpenAI 图片 API 生成图片，兼容 URL 和 base64 返回。"""
        try:
            model = os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-1')
            logger.info(f"使用 OpenAI 图片模型生成图片: {model}")

            url = "https://api.openai.com/v1/images/generations"
            headers = {
                "Authorization": f"Bearer {self.openai_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": model,
                "prompt": prompt,
                "n": 1,
                "size": size,
            }

            if model == 'dall-e-3':
                data["quality"] = "standard"

            response = requests.post(url, headers=headers, json=data, timeout=120)
            response.raise_for_status()

            result = response.json()
            image_data = result['data'][0]

            if image_data.get('b64_json'):
                image_path = self._save_base64_image(image_data['b64_json'], prefix='openai')
            else:
                image_url = image_data['url']
                image_path = self._download_image(image_url, prefix='openai')
            logger.info(f"✅ 图片生成成功: {image_path}")
            return str(image_path)

        except Exception as e:
            logger.error(f"OpenAI 图片生成失败: {str(e)}")
            return None

    def _generate_flux(self, prompt: str, size: str) -> Optional[str]:
        """使用 Flux (via Replicate) 生成图片"""
        try:
            logger.info("使用 Flux 生成图片")

            # Replicate API 调用
            # 这里需要安装 replicate 包: pip install replicate
            import replicate

            width, height = map(int, size.split('x'))

            output = replicate.run(
                "black-forest-labs/flux-schnell",
                input={
                    "prompt": prompt,
                    "width": width,
                    "height": height,
                    "num_outputs": 1
                }
            )

            # 下载图片
            image_url = output[0]
            image_path = self._download_image(image_url, prefix='flux')
            logger.info(f"✅ 图片生成成功: {image_path}")
            return str(image_path)

        except Exception as e:
            logger.error(f"Flux 生成失败: {str(e)}")
            return None

    def _download_image(self, url: str, prefix: str = "cover") -> Path:
        """下载图片到本地"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = self.output_dir / filename

        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return filepath

    def _save_base64_image(self, b64_json: str, prefix: str = "image") -> Path:
        """保存 base64 图片到本地。"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.png"
        filepath = self.output_dir / filename

        image_bytes = base64.b64decode(b64_json)
        with open(filepath, 'wb') as f:
            f.write(image_bytes)

        return filepath

    def generate_batch(self, contents: list) -> Dict[str, str]:
        """批量生成图片"""
        results = {}

        for content in contents:
            title = content.get('title', '')
            platform = content.get('platform', 'wechat')
            body = content.get('content', '')
            style = content.get('style')

            image_path = self.generate_platform_image(title, body, platform, style=style)
            if image_path:
                results[platform] = image_path

        return results


# 测试代码
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    generator = ImageGenerator()

    # 测试生成
    image_path = generator.generate_cover_image(
        title="AI时代，如何培养孩子的核心竞争力",
        style="educational",
        platform="xiaohongshu"
    )

    print(f"生成的图片: {image_path}")
