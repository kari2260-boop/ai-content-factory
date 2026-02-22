"""
项目初始化脚本
检查环境、创建必要的目录和配置文件
"""
import os
import sys
from pathlib import Path

def check_environment():
    """检查环境变量"""
    print("🔍 检查环境变量...")

    required_vars = {
        'ANTHROPIC_AUTH_TOKEN': 'Claude API Key',
        'GEMINI_API_KEY': 'Gemini API Key (可选)'
    }

    missing = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            if var == 'GEMINI_API_KEY':
                print(f"  ⚠️  {desc}: 未配置（可选）")
            else:
                print(f"  ❌ {desc}: 未配置")
                missing.append(var)
        else:
            print(f"  ✅ {desc}: 已配置")

    if missing:
        print(f"\n❌ 缺少必需的环境变量: {', '.join(missing)}")
        print("请在系统环境变量中配置这些 API Key")
        return False

    return True


def check_env_file():
    """检查 .env 文件"""
    print("\n🔍 检查 .env 文件...")

    env_file = Path('.env')
    env_example = Path('.env.example')

    if not env_file.exists():
        if env_example.exists():
            print("  ⚠️  .env 文件不存在，从 .env.example 创建...")
            env_file.write_text(env_example.read_text())
            print("  ✅ .env 文件已创建")
        else:
            print("  ❌ .env.example 文件不存在")
            return False

    # 检查 Notion 配置
    env_content = env_file.read_text()

    if 'your_notion_integration_token_here' in env_content:
        print("  ⚠️  请在 .env 文件中配置 NOTION_TOKEN 和 NOTION_DATABASE_ID")
        print("  📖 参考 README.md 获取 Notion 配置")
        return False

    print("  ✅ .env 文件已配置")
    return True


def check_directories():
    """检查目录结构"""
    print("\n🔍 检查目录结构...")

    required_dirs = [
        'data/topics',
        'data/drafts',
        'data/published',
        'logs',
        'config'
    ]

    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ 创建目录: {dir_path}")
        else:
            print(f"  ✅ 目录存在: {dir_path}")

    return True


def check_dependencies():
    """检查 Python 依赖"""
    print("\n🔍 检查 Python 依赖...")

    try:
        import streamlit
        import anthropic
        import notion_client
        import feedparser
        import schedule
        print("  ✅ 所有依赖已安装")
        return True

    except ImportError as e:
        print(f"  ❌ 缺少依赖: {str(e)}")
        print("\n请运行: pip3 install -r requirements.txt")
        return False


def check_openclaw():
    """检查 OpenClaw"""
    print("\n🔍 检查 OpenClaw...")

    import subprocess

    try:
        result = subprocess.run(
            ['openclaw', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"  ✅ OpenClaw 已安装: {result.stdout.strip()}")

            # 检查网关状态
            result = subprocess.run(
                ['openclaw', 'gateway', 'health'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print("  ✅ OpenClaw 网关运行正常")
            else:
                print("  ⚠️  OpenClaw 网关未运行（可选功能）")

            return True

    except Exception as e:
        print(f"  ⚠️  OpenClaw 未安装或不可用（可选功能）")
        return True  # OpenClaw 是可选的


def main():
    """主函数"""
    print("=" * 60)
    print("🏭 K博士 AI 内容工厂 - 初始化检查")
    print("=" * 60)

    checks = [
        ("环境变量", check_environment),
        (".env 文件", check_env_file),
        ("目录结构", check_directories),
        ("Python 依赖", check_dependencies),
        ("OpenClaw", check_openclaw)
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 检查失败: {str(e)}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("📊 检查结果汇总")
    print("=" * 60)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n🎉 所有检查通过！系统已就绪")
        print("\n下一步:")
        print("  1. 运行 Streamlit 管理后台: streamlit run app.py")
        print("  2. 或运行定时调度器: python3 scheduler.py")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请根据提示修复")
        return 1


if __name__ == '__main__':
    sys.exit(main())
