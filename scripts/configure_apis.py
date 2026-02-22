#!/usr/bin/env python3
"""
API 配置助手
帮助用户逐步配置所有 API 凭证
"""
import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_step(number, text):
    print(f"\n📍 步骤 {number}: {text}")

def print_info(text):
    print(f"ℹ️  {text}")

def print_success(text):
    print(f"✅ {text}")

def print_warning(text):
    print(f"⚠️  {text}")

def get_input(prompt, optional=False):
    suffix = " (可选，直接回车跳过)" if optional else ""
    value = input(f"👉 {prompt}{suffix}: ").strip()
    return value if value else None

def configure_wechat():
    print_header("微信公众号配置")

    print_info("需要认证的服务号或订阅号")
    print_info("登录地址: https://mp.weixin.qq.com")

    print_step(1, "登录微信公众平台")
    print("   - 访问 https://mp.weixin.qq.com")
    print("   - 使用管理员账号登录")

    print_step(2, "获取开发者凭证")
    print("   - 点击左侧菜单：开发 -> 基本配置")
    print("   - 找到「开发者ID(AppID)」和「开发者密码(AppSecret)」")
    print("   - 如果没有 AppSecret，点击「重置」生成新的")

    print_step(3, "配置 IP 白名单")
    print("   - 在同一页面找到「IP白名单」")
    print("   - 点击「修改」，添加你的服务器 IP")
    print("   - 如果是本地测试，添加你的公网 IP")

    print("\n" + "-"*60)
    appid = get_input("请输入 AppID (格式: wx...)")
    secret = get_input("请输入 AppSecret")

    if appid and secret:
        return {"WECHAT_APPID": appid, "WECHAT_SECRET": secret}
    else:
        print_warning("跳过微信公众号配置")
        return {}

def configure_xiaohongshu():
    print_header("小红书配置")

    print_info("需要企业认证账号")
    print_info("开放平台: https://open.xiaohongshu.com/")

    print_step(1, "注册开发者账号")
    print("   - 访问 https://open.xiaohongshu.com/")
    print("   - 使用企业账号注册")
    print("   - 完成企业认证")

    print_step(2, "创建应用")
    print("   - 登录后点击「应用管理」")
    print("   - 点击「创建应用」")
    print("   - 填写应用信息并提交审核")

    print_step(3, "获取凭证")
    print("   - 审核通过后，进入应用详情")
    print("   - 获取「App Key」和「App Secret」")

    print_step(4, "账号授权")
    print("   - 点击「账号授权」")
    print("   - 扫码授权你的小红书账号")
    print("   - 获取「Access Token」")

    print("\n" + "-"*60)
    app_key = get_input("请输入 App Key", optional=True)
    app_secret = get_input("请输入 App Secret", optional=True)
    access_token = get_input("请输入 Access Token", optional=True)

    if app_key and app_secret and access_token:
        return {
            "XHS_APP_KEY": app_key,
            "XHS_APP_SECRET": app_secret,
            "XHS_ACCESS_TOKEN": access_token
        }
    else:
        print_warning("跳过小红书配置")
        return {}

def configure_baidu_tongji():
    print_header("百度统计配置")

    print_info("需要百度统计账号")
    print_info("登录地址: https://tongji.baidu.com/")

    print_step(1, "登录百度统计")
    print("   - 访问 https://tongji.baidu.com/")
    print("   - 使用百度账号登录")

    print_step(2, "获取 Site ID")
    print("   - 在网站列表中找到你的网站")
    print("   - 点击「获取代码」")
    print("   - 在代码中找到类似 hm.js?后面的一串字符")
    print("   - 这就是你的 site_id")

    print_step(3, "获取 API Token")
    print("   - 点击顶部菜单：管理 -> API 管理")
    print("   - 如果没有 token，点击「申请 token」")
    print("   - 复制显示的 token")

    print("\n" + "-"*60)
    token = get_input("请输入 Token", optional=True)
    site_id = get_input("请输入 Site ID", optional=True)

    if token and site_id:
        return {
            "BAIDU_TONGJI_TOKEN": token,
            "BAIDU_TONGJI_SITE_ID": site_id
        }
    else:
        print_warning("跳过百度统计配置")
        return {}

def configure_seo_tools():
    print_header("SEO 工具配置（可选）")

    print_info("这些是可选的第三方 SEO 工具")
    print_info("不配置也可以使用基础 SEO 分析功能")

    print("\n【选项 1】5118 API")
    print("   - 网站: https://www.5118.com/")
    print("   - 功能: 关键词挖掘、排名监控")
    print("   - 费用: 付费服务")

    print("\n【选项 2】站长工具 API")
    print("   - 网站: http://api.tool.chinaz.com/")
    print("   - 功能: SEO 综合查询")
    print("   - 费用: 付费服务")

    print("\n" + "-"*60)
    token_5118 = get_input("5118 Token", optional=True)
    key_chinaz = get_input("站长工具 Key", optional=True)

    config = {}
    if token_5118:
        config["SEO_5118_TOKEN"] = token_5118
    if key_chinaz:
        config["SEO_CHINAZ_KEY"] = key_chinaz

    if not config:
        print_warning("跳过 SEO 工具配置（将使用基础功能）")

    return config

def update_env_file(config):
    """更新 .env 文件"""
    env_path = Path("/Users/k/ai-content-factory/.env")

    if not env_path.exists():
        print_warning(f".env 文件不存在: {env_path}")
        return False

    # 读取现有内容
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 更新配置
    updated_lines = []
    for line in lines:
        updated = False
        for key, value in config.items():
            if line.startswith(f"{key}="):
                updated_lines.append(f"{key}={value}\n")
                updated = True
                break
        if not updated:
            updated_lines.append(line)

    # 写回文件
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(updated_lines)

    return True

def main():
    print("\n" + "🎯 "*20)
    print("     AI 内容工厂 - API 配置助手")
    print("🎯 "*20)

    print("\n本助手将帮助你配置以下 API:")
    print("  1. 微信公众号 - 发布文章")
    print("  2. 小红书 - 发布笔记")
    print("  3. 百度统计 - 数据分析")
    print("  4. SEO 工具 - 内容优化（可选）")

    print("\n💡 提示:")
    print("  - 可以选择性配置，不需要的可以跳过")
    print("  - 配置信息会保存到 .env 文件")
    print("  - 随时可以重新运行此脚本修改配置")

    input("\n按回车键开始配置...")

    all_config = {}

    # 1. 微信公众号
    if input("\n是否配置微信公众号? (y/n): ").lower() == 'y':
        all_config.update(configure_wechat())

    # 2. 小红书
    if input("\n是否配置小红书? (y/n): ").lower() == 'y':
        all_config.update(configure_xiaohongshu())

    # 3. 百度统计
    if input("\n是否配置百度统计? (y/n): ").lower() == 'y':
        all_config.update(configure_baidu_tongji())

    # 4. SEO 工具
    if input("\n是否配置 SEO 工具? (y/n): ").lower() == 'y':
        all_config.update(configure_seo_tools())

    # 保存配置
    if all_config:
        print_header("保存配置")
        print(f"将保存 {len(all_config)} 个配置项:")
        for key in all_config.keys():
            print(f"  ✓ {key}")

        if update_env_file(all_config):
            print_success("配置已保存到 .env 文件")
            print_info("位置: /Users/k/ai-content-factory/.env")
        else:
            print_warning("保存失败，请手动编辑 .env 文件")
    else:
        print_warning("未配置任何 API")

    print_header("配置完成")
    print("📚 查看使用指南: docs/API_SKILLS_GUIDE.md")
    print("🧪 测试 Skills:")
    print("   /seo-optimize 关键词 留学申请")
    print("   /baidu-analytics 概况")
    print("   /wechat-publish 状态")
    print("\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  配置已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        sys.exit(1)
