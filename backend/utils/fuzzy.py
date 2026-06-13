# utils/fuzzy.py
from __future__ import annotations

def fuzzy_like_patterns(text: str, *, max_patterns: int = 8, include_single_chars: bool = True) -> list[str]:
    """
    產生 SQL LIKE patterns（Google-like fallback 用）
    - 先包含完整字串：%text%
    - 再逐字插入 %：%高%見%明%
    - 再姓+任一字：%高%見% / %高%明%
    - 再任兩字：%見%明%
    - 最後（可選）單字：%高%/%見%/%明%
    """
    s = (text or "").strip()
    if not s:
        return []

    pats: list[str] = []

    def add(p: str):
        if p and p not in seen:
            seen.add(p)
            pats.append(p)

    seen = set()

    # 1) 完整包含
    add(f"%{s}%")

    # 2) 逐字插 %
    if len(s) >= 2:
        add("%" + "%".join(list(s)) + "%")

    # 3) 首字 + 任一字（常用於姓名：姓 + 名其中一字）
    if len(s) >= 2:
        first = s[0]
        for ch in s[1:]:
            add(f"%{first}%{ch}%")

    # 4) 任兩字相鄰片段
    if len(s) >= 2:
        for i in range(len(s) - 1):
            add(f"%{s[i]}%{s[i+1]}%")

    # 5) 單字（最寬，最後手段）
    if include_single_chars:
        for ch in set(s):
            add(f"%{ch}%")

    return pats[: max(1, int(max_patterns))]
