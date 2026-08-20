#!/usr/bin/env python3
"""
심플키 상세페이지 자동 조립 빌더 v1 (2026-08-21)

사용법:
  python3 system/build.py                    # content/*.yml 전부 빌드
  python3 system/build.py content/xxx.yml    # 한 페이지만 빌드

구조:
  content/<페이지>.yml  = 카피 + 섹션 선택 (대표·비개발자 편집 영역)
  system/patterns/*.html = 섹션 패턴 템플릿 (13섹션 × A/B/C variant)
  system/base.html       = 페이지 스켈레톤 (Pixel·GTM·SEO·cal — 보호 영역)
  출력 = p/<slug>/index.html

안전 장치: 빌드 후 Meta Pixel(647144813979261)·GTM(GTM-WX8R8ZB) 존재를 기계 검증.
하나라도 없으면 빌드 실패(exit 1) — 파일을 쓰지 않는다.
"""
import sys, re, html, pathlib
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
SYSTEM = ROOT / "system"
PATTERNS = SYSTEM / "patterns"
CONTENT = ROOT / "content"

PIXEL_ID = "647144813979261"
GTM_ID = "GTM-WX8R8ZB"

# ---------- 미니 템플릿 엔진 (mustache 부분집합) ----------
SECTION_RE = re.compile(r"\{\{#([\w.]+)\}\}(.*?)\{\{/\1\}\}", re.S)
RAW_RE = re.compile(r"\{\{\{([\w.]+)\}\}\}")
VAR_RE = re.compile(r"\{\{([\w.]+)\}\}")

def lookup(ctx, key):
    if key == ".":
        return ctx.get(".", "") if isinstance(ctx, dict) else ctx
    cur = ctx
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur

def render(tpl, ctx):
    def do_section(m):
        key, body = m.group(1), m.group(2)
        val = lookup(ctx, key)
        if not val:
            return ""
        if isinstance(val, list):
            out = []
            for item in val:
                sub = dict(ctx)
                if isinstance(item, dict):
                    sub.update(item)
                else:
                    sub["."] = item
                out.append(render(body, sub))
            return "".join(out)
        if isinstance(val, dict):
            sub = dict(ctx); sub.update(val)
            return render(body, sub)
        return render(body, ctx)  # truthy 스칼라 = 조건부 표시
    tpl = SECTION_RE.sub(do_section, tpl)
    tpl = RAW_RE.sub(lambda m: str(lookup(ctx, m.group(1)) or ""), tpl)
    tpl = VAR_RE.sub(lambda m: html.escape(str(lookup(ctx, m.group(1)) or ""), quote=False), tpl)
    return tpl

# ---------- 패턴 로드 ----------
META_RE = re.compile(r"<!--\s*meta:\s*(.*?)\s*-->")

def load_pattern(name):
    path = PATTERNS / f"{name}.html"
    if not path.exists():
        sys.exit(f"[빌드 실패] 패턴 없음: {name} ({path})")
    src = path.read_text(encoding="utf-8")
    meta = {}
    m = META_RE.search(src.split("\n", 1)[0])
    if m:
        for pair in m.group(1).split():
            k, _, v = pair.partition("=")
            meta[k] = v
        src = src.split("\n", 1)[1]
    return meta, src

# ---------- 페이지 빌드 ----------
def build_page(yml_path):
    data = yaml.safe_load(pathlib.Path(yml_path).read_text(encoding="utf-8"))
    page = data.get("page", {})
    slug = page.get("slug") or pathlib.Path(yml_path).stem
    out_dir = ROOT / page.get("out", f"p/{slug}")
    if not str(out_dir.resolve()).startswith(str(ROOT.resolve()) + "/"):
        sys.exit(f"[빌드 실패] 출력 경로가 저장소 바깥: {out_dir}")

    sections_html = []
    for sec in data.get("sections", []):
        name = sec["pattern"]
        meta, tpl = load_pattern(name)
        bg = sec.get("bg", meta.get("bg", "white"))
        pad = sec.get("pad", meta.get("pad", "xl"))
        sec_id = sec.get("id", meta.get("id", name.split("-")[0]))
        pad_cls = "" if pad == "xl" else f" pad-{pad}"
        body = render(tpl, sec.get("fields", {}))
        sections_html.append(
            f'<section id="{sec_id}" class="sec bg-{bg}{pad_cls}" data-pattern="{name}">\n{body}\n</section>'
        )

    base = (SYSTEM / "base.html").read_text(encoding="utf-8")
    canonical = page.get("canonical", f"https://simplekey.kr/p/{slug}/")
    ctx = {
        "title": page.get("title", "심플키"),
        "description": page.get("description", ""),
        "canonical": canonical,
        "og_image": page.get("og_image", "https://simplekey.kr/assets/og.png"),
        "robots": "noindex, nofollow" if page.get("noindex", True) else "index, follow",
        "sections": "\n\n".join(sections_html),
    }
    out = render(base, ctx)

    # ---------- 픽셀·GTM 기계 검증 (실패 시 파일 안 씀) ----------
    errors = []
    if f"fbq('init','{PIXEL_ID}')" not in out:
        errors.append(f"Meta Pixel init({PIXEL_ID}) 누락")
    if out.count(PIXEL_ID) < 2:
        errors.append("Meta Pixel noscript 폴백 누락")
    if out.count(GTM_ID) < 2:
        errors.append(f"GTM({GTM_ID}) head/body 스니펫 누락")
    has_booking = 'id="booking"' in out or "id='booking'" in out
    if has_booking and "cal-embed" not in out:
        errors.append("booking 섹션이 있는데 cal.com 임베드 슬롯(#cal-embed) 누락")
    leftover = VAR_RE.findall(out)
    if leftover:
        errors.append(f"치환 안 된 변수 잔존: {sorted(set(leftover))[:10]}")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(f"[빌드 실패] {yml_path}: 검증 {len(errors)}건 실패 — 출력 파일을 쓰지 않았다")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(out, encoding="utf-8")
    print(f"  ✓ {yml_path} → {out_dir / 'index.html'} ({len(out):,} bytes · 섹션 {len(sections_html)}개 · 픽셀/GTM 검증 통과)")

def main():
    targets = sys.argv[1:] or sorted(str(p) for p in CONTENT.glob("*.yml"))
    if not targets:
        sys.exit("content/*.yml 없음")
    print(f"심플키 빌더 — {len(targets)}개 페이지")
    for t in targets:
        build_page(t)

if __name__ == "__main__":
    main()
