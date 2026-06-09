#!/usr/bin/env python3
"""切換 slides.md 的 Marp 主題。"""
import sys
import re
from pathlib import Path

THEMES = {
    "tech-dark":      "深藍科技風（預設）  — 適合技術簡報、深色場地",
    "clean-light":    "白底清爽風        — 適合明亮場地、一般簡報",
    "corporate-navy": "藍灰商務風        — 適合正式會議、企業場合",
    "warm-amber":     "暖琥珀深色風      — 視覺鮮明、適合創意分享",
}


def set_theme(theme: str, folder: str) -> None:
    slides = Path(folder) / "slides.md"
    if not slides.exists():
        print(f"[錯誤] 找不到 {slides}")
        sys.exit(1)

    content = slides.read_text(encoding="utf-8")
    if "theme:" not in content:
        print(f"[錯誤] {slides} 的 frontmatter 中找不到 theme: 欄位")
        sys.exit(1)

    new_content = re.sub(r"^theme: .*$", f"theme: {theme}", content, flags=re.MULTILINE)
    slides.write_text(new_content, encoding="utf-8")
    print(f"[完成] {slides}  →  theme: {theme}")
    print("      重新執行 step1_generate 即可看到新主題效果。")


def show_menu() -> None:
    print("╔══════════════════════════════════════════════════════╗")
    print("║             ai-video-maker 主題切換工具              ║")
    print("╠══════════════════════════════════════════════════════╣")
    for name, desc in THEMES.items():
        print(f"  {name:<18}  {desc}")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print("用法：")
    print("  python set_theme.py <主題名稱> [資料夾]")
    print()
    print("範例：")
    print("  python set_theme.py clean-light")
    print("  python set_theme.py corporate-navy ./my_lesson/")
    print()


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        show_menu()
        return

    theme = args[0]
    folder = args[1] if len(args) > 1 else "example"

    if theme not in THEMES:
        print(f"[錯誤] 不支援的主題：{theme}")
        print(f"可用主題：{' | '.join(THEMES.keys())}")
        sys.exit(1)

    set_theme(theme, folder)


if __name__ == "__main__":
    main()
