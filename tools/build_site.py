# -*- coding: utf-8 -*-
"""Build a static, dependency-free site from the CET-4 markdown sources."""
import html
import json
import os
import re
import shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "content")
OUT = BASE
TITLE = "英语四级全题型做题技巧与高频考点总结"

PAGES = [
    ("00_intro.md", "intro", "使用说明"),
    ("01_part1.md", "part1", None),
    ("02_part2a.md", "part2a", None),
    ("02_part2b.md", "part2b", None),
    ("02_part2c.md", "part2c", None),
    ("03_part3.md", "part3", None),
    ("04_part4a.md", "part4a", None),
    ("04_part4b.md", "part4b", None),
    ("05_part5a.md", "part5a", None),
    ("05_part5b.md", "part5b", None),
    ("06_part6.md", "part6", None),
    ("07_part7.md", "part7", None),
    ("08_appendix.md", "appendix", None),
]
# chapters are grouped into one page per part
GROUP = {
    "intro": ["intro"],
    "part1": ["part1"],
    "part2": ["part2a", "part2b", "part2c"],
    "part3": ["part3"],
    "part4": ["part4a", "part4b"],
    "part5": ["part5a", "part5b"],
    "part6": ["part6"],
    "part7": ["part7"],
    "appendix": ["appendix"],
}
ORDER = ["intro", "part1", "part2", "part3", "part4", "part5",
         "part6", "part7", "appendix"]


def esc(s):
    return html.escape(s, quote=False)


CJK = re.compile(r"[\u3400-\u9fff]")


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    def q(m):
        inner = m.group(1)
        if CJK.search(inner):
            return "\u201c" + inner + "\u201d"
        return m.group(0)

    s = re.sub(r'"([^"<>]{1,80})"', q, s)
    return s


def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def slugify(t):
    return "sec-" + re.sub(r"[^0-9a-zA-Z]+", "-", t).strip("-")[:40]


def is_table_start(lines, i):
    return (i + 1 < len(lines) and lines[i].lstrip().startswith("|")
            and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]))


def render_md(text, page_key):
    lines = text.splitlines()
    out = []
    sections = []
    i = 0
    n = len(lines)
    k = 0
    while i < n:
        line = lines[i].rstrip()
        if not line.strip() or line.strip() == "<!-- pagebreak -->":
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            if level == 1:
                out.append(f"<h1>{inline(title.strip())}</h1>")
            elif level == 2:
                k += 1
                sid = slugify(title)
                if sid == "sec-":
                    sid = f"sec-{page_key}-{k}"
                sections.append((sid, title.strip()))
                out.append(f'<h2 id="{sid}">{inline(title.strip())}'
                           f'<a class="anchor" href="#{sid}" '
                           f'aria-label="链接">#</a></h2>')
            elif level == 3:
                out.append(f"<h3>{inline(title)}</h3>")
            else:
                out.append(f"<h4>{inline(title)}</h4>")
            i += 1
            continue
        if is_table_start(lines, i):
            head = cells(line)
            i += 2
            rows = []
            while i < n and lines[i].lstrip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            t = ['<div class="table-wrap"><table><thead><tr>']
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                r = r + [""] * (len(head) - len(r))
                t.append("<tr>" + "".join(
                    f"<td>{inline(c)}</td>" for c in r[:len(head)]) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            out.append('<div class="tip">' + "<br>".join(
                inline(x) for x in buf) + "</div>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < n and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append(re.sub(r"^\s*[-*]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(
                f"<li>{inline(x)}</li>" for x in items) + "</ul>")
            continue
        if re.match(r"^\s*\d+[.)]\s+", line):
            items = []
            while i < n and re.match(r"^\s*\d+[.)]\s+", lines[i]):
                items.append(re.sub(r"^\s*\d+[.)]\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(
                f"<li>{inline(x)}</li>" for x in items) + "</ol>")
            continue
        buf = [line.strip()]
        i += 1
        while i < n:
            nxt = lines[i].rstrip()
            if (not nxt.strip() or nxt.startswith("#")
                    or nxt.startswith(">") or nxt.startswith("|")
                    or re.match(r"^\s*[-*]\s+", nxt)
                    or re.match(r"^\s*\d+[.)]\s+", nxt)
                    or nxt.strip() == "<!-- pagebreak -->"):
                break
            buf.append(nxt.strip())
            i += 1
        out.append("<p>" + inline("".join(buf)) + "</p>")
    return "\n".join(out), sections


def read_page(key):
    chunks = []
    for fname, k, _ in PAGES:
        if k in GROUP[key]:
            with open(os.path.join(SRC, fname), encoding="utf-8") as f:
                chunks.append(f.read())
    return "\n\n".join(chunks)


def main():
    os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
    nav, content, search, labels = [], {}, [], {}
    for key in ORDER:
        body, secs = render_md(read_page(key), key)
        content[key] = body
        labels[key] = secs
        for sid, title in secs:
            nav.append({"key": key, "id": sid, "title": title})
        # search entries: split body by h2
        parts = re.split(r'<h2 id="([^"]+)">', body)
        for idx in range(1, len(parts), 2):
            sid = parts[idx]
            seg = parts[idx + 1]
            text = re.sub(r"<[^>]+>", " ", seg)
            text = re.sub(r"\s+", " ", html.unescape(text)).strip()
            search.append({"t": html.unescape(
                re.sub(r"<[^>]+>", "", sid and "")), "p": key, "a": sid,
                "x": text[:500]})

    # rebuild search titles from section list
    title_map = {(key, sid): title for key in ORDER for sid, title in labels[key]}
    for s in search:
        s["t"] = title_map.get((s["p"], s["a"]), "")

    parts_meta = [
        ("intro", "使用说明", "怎么用这本书、30 天与 14 天计划"),
        ("part1", "第一部分", "全题型做题技巧"),
        ("part2", "第二部分", "写作素材库"),
        ("part3", "第三部分", "听力高频考点"),
        ("part4", "第四部分", "阅读高频考点"),
        ("part5", "第五部分", "翻译高频考点"),
        ("part6", "第六部分", "同义替换总表"),
        ("part7", "第七部分", "语法与搭配速查"),
        ("appendix", "附录", "考前清单与速查表"),
    ]

    with open(os.path.join(OUT, "assets", "style.css"), encoding="utf-8") as f:
        css = f.read()
    with open(os.path.join(OUT, "assets", "app.js"), encoding="utf-8") as f:
        js = f.read()

    def page(title, body, key="", home=False):
        links = []
        for idx, (k, label, desc) in enumerate(parts_meta):
            sub = []
            for sid, t in labels[k]:
                sub.append(f'<li><a href="{k}.html#{sid}">{esc(t)}</a></li>')
            active = " active" if k == key else ""
            links.append(
                f'<div class="nav-part{active}"><a class="nav-head" '
                f'href="{k}.html"><span class="nav-label">{label}</span>'
                f'<span class="nav-desc">{esc(desc)}</span></a>'
                f'<ul class="nav-sections">{"".join(sub)}</ul></div>')
        cur = ORDER.index(key) if key in ORDER else -1
        pager = ""
        if cur >= 0:
            prev_k = ORDER[cur - 1] if cur > 0 else None
            next_k = ORDER[cur + 1] if cur < len(ORDER) - 1 else None
            if prev_k:
                pager += (f'<a class="pager prev" href="{prev_k}.html">'
                          f'<span>上一篇</span>{parts_meta[cur-1][1]}'
                          f'</a>')
            if next_k:
                pager += (f'<a class="pager next" href="{next_k}.html">'
                          f'<span>下一篇</span>{parts_meta[cur+1][1]}'
                          f'</a>')
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(TITLE)}：写作、听力、阅读、翻译全题型技巧与高频考点。">
<link rel="stylesheet" href="assets/style.css">
</head>
<body data-page="{key}">
<div class="progress" id="progress"></div>
<header class="topbar">
  <button class="menu-btn" id="menuBtn" aria-label="目录">☰</button>
  <a class="brand" href="index.html">{esc(TITLE)}</a>
  <div class="search-box">
    <input id="searchInput" type="search" placeholder="搜索：同义替换 / 选词填空 / 翻译…" autocomplete="off">
  </div>
  <a class="dl" href="assets/cet4-guide.pdf" download>下载 PDF</a>
</header>
<div class="layout">
  <aside class="sidebar" id="sidebar">
    <div class="side-title">目录</div>
    <nav>{''.join(links)}</nav>
    <div class="side-foot">
      <a href="assets/cet4-guide.docx" download>Word 版</a>
      <a href="https://github.com/" target="_blank" rel="noopener">GitHub</a>
    </div>
  </aside>
  <main class="main">
    <article class="article{' home' if home else ''}">
      {body}
      {pager}
    </article>
    <footer class="foot">
      <p>非官方备考资料 · 按现行四级笔试题型整理 · 内容由 AI 辅助生成，请以官方考试大纲为准</p>
      <p>本作品采用 CC BY-NC-SA 4.0 许可协议 · 可自由分享，禁止商用</p>
    </footer>
  </main>
</div>
<div class="search-panel" id="searchPanel" hidden>
  <div class="search-head">搜索结果 <button id="searchClose">关闭</button></div>
  <div id="searchResults"></div>
</div>
<div class="mask" id="mask"></div>
<script>window.__SEARCH__ = "search.json";</script>
<script src="assets/app.js"></script>
</body>
</html>"""

    # home
    cards = "".join(
        f'<a class="card" href="{k}.html"><span class="card-k">{label}</span>'
        f'<span class="card-t">{esc(desc)}</span></a>'
        for k, label, desc in parts_meta[1:])
    home_body = f"""
<div class="hero">
  <div class="eyebrow">CET-4 · 710 分 · 57 题</div>
  <h1>{esc(TITLE)}</h1>
  <p class="lede">技巧在前，素材在后。7 个部分、92 页、84 张表，
  把写作、听力、阅读、翻译的做题流程和高频考点放在同一本里。</p>
  <div class="cta">
    <a class="btn primary" href="part1.html">开始阅读</a>
    <a class="btn" href="assets/cet4-guide.pdf" download>下载 PDF</a>
    <a class="btn" href="assets/cet4-guide.docx" download>下载 Word</a>
  </div>
  <div class="stats">
    <div><b>57</b><span>道题</span></div>
    <div><b>7</b><span>大部分</span></div>
    <div><b>84</b><span>张表格</span></div>
    <div><b>430+</b><span>组同义替换</span></div>
  </div>
</div>
<h2>全书结构</h2>
<div class="cards">{cards}</div>
<h2>怎么用</h2>
<p>先用两三天把第一部分读一遍，形成固定的做题流程；之后每天背 5 句写作句型、10 组同义替换，再做一篇阅读；考前一周只看错题本和附录清单。</p>
<div class="tip">所有同义替换表都带中文注释：先遮住最后一列自测，反应不过来的画记号，第二遍只背画记号的。</div>
"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(TITLE, home_body, "", home=True))

    for key in ORDER:
        label = dict((k, l) for k, l, _ in parts_meta)[key]
        desc = dict((k, d) for k, l, d in parts_meta)[key]
        with open(os.path.join(OUT, f"{key}.html"), "w", encoding="utf-8") as f:
            f.write(page(f"{label} {desc} · {TITLE}", content[key], key))

    with open(os.path.join(OUT, "search.json"), "w", encoding="utf-8") as f:
        json.dump(search, f, ensure_ascii=False)
    with open(os.path.join(OUT, "assets", "search-data.js"), "w",
              encoding="utf-8") as f:
        f.write("window.__SEARCH_DATA__ = " +
                json.dumps(search, ensure_ascii=False) + ";")
    with open(os.path.join(OUT, "assets", "style.css"), "w", encoding="utf-8") as f:
        f.write(css)
    with open(os.path.join(OUT, "assets", "app.js"), "w", encoding="utf-8") as f:
        f.write(js)
    with open(os.path.join(OUT, ".nojekyll"), "w", encoding="utf-8") as f:
        f.write("")
    print("built pages:", len(ORDER) + 1, "sections:", len(nav),
          "search:", len(search))


if __name__ == "__main__":
    main()
