import os
from pathlib import Path
from dotenv import load_dotenv

def main():
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    app_secret = os.getenv("FEISHU_APP_SECRET")
    
    print("=" * 60)
    print("App Secret 隐藏字符检测")
    print("=" * 60)
    print(f"原始字符串: '{app_secret}'")
    print(f"字符串长度: {len(app_secret)}")
    print()
    print("字符详情 (索引: ASCII值 - 字符):")
    print("-" * 60)
    
    for i, char in enumerate(app_secret):
        ascii_val = ord(char)
        if ascii_val == 32:
            char_repr = "(空格)"
        elif ascii_val == 9:
            char_repr = "(制表符)"
        elif ascii_val < 32 or ascii_val > 126:
            char_repr = f"(不可见字符: {ascii_val})"
        else:
            char_repr = char
        print(f"{i:2d}: {ascii_val:3d} - {char_repr}")

if __name__ == "__main__":
    main()