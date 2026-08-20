# 심플키 상세페이지 자동 생성 시스템 v1 (2026-08-21)

카피만 넣으면 심플키 디자인이 자동으로 입혀진 상세페이지가 조립되는 시스템.
원칙: **AI는 HTML을 직접 쓰지 않는다. 카피를 스키마(YAML)에 채울 뿐, 렌더링은 결정적 템플릿이 한다.**
(근거: Sanity 페이지빌더·shadcn 레지스트리 패턴 — 디자인 붕괴 원천 차단)

## 3층 구조

| 층 | 파일 | 누가 만지나 |
|---|---|---|
| 콘텐츠 (카피·섹션 선택) | `content/*.yml` | 대표님(Pages CMS)·AI |
| 패턴 (섹션 골격 13종×variant) | `system/patterns/*.html` + `patterns.css` | AI(세스)만 |
| 토큰·스켈레톤 (디자인 규칙·픽셀) | `system/tokens.css`·`base.css`·`base.html` | AI(세스)만 · 픽셀 보호 영역 |

## 새 상세페이지 만드는 법 (AI용)

1. `content/기존.yml` 복제 → 카피를 새 상품에 맞게 교체.
2. 섹션 패턴은 옵시디언 「심플키 상세페이지 마스터 섹션 패턴 (피그마 골격·정본)」의 13섹션 A/B/C 기준으로 선택. 고가 컨설팅 디폴트 = hero-a → problem-a → agitate-b → solution-a → trust-a → how-a → proof-a → offer-c → objection-a → urgency-a → cta-a → faq-b → final-a.
3. `python3 system/build.py` → `p/<slug>/index.html` 생성.
4. 검토 전 `noindex: true` 유지. 지영님 컨펌 후 false.
5. `git push` = 발행. 발행 후 Pixel Helper로 픽셀 확인.

## 디자인 규칙 (위반 금지)

- 색·크기·여백은 **토큰만** 사용. 임의 hex·px 금지. (`tokens.css`가 유일한 출처)
- 타입 스케일 8단계·스페이싱 8px 그리드·섹션 세로 패딩은 xl/lg/md 3단만.
- 오렌지는 화면 5~10%: CTA·핵심 숫자·포인트에만. 브라운 배경은 히어로·긴급성·클로징·헤더·푸터만.
- 새 variant 추가 = `patterns/<섹션>-<x>.html` + `patterns.css`에 토큰 기반 스타일 + 이 README 카탈로그에 한 줄.

## 픽셀 안전 (3겹)

1. Pixel(647144813979261)·GTM(GTM-WX8R8ZB)은 `base.html` 한 곳에만 존재 → 유실 자체가 구조적으로 불가.
2. `build.py`가 출력마다 존재 검증 — 없으면 파일을 쓰지 않고 실패.
3. GitHub Actions가 발행 전 전 페이지(라이브 루트 포함) 전수 grep — 실패 시 발행 중단.
- 예약 전환(BookingCompleted)은 cal.com 네이티브 발화. 랜딩에서 중복 발화 금지. CTA 클릭은 ConsultClick 맞춤 이벤트만.

## 대표님 직접 수정 경로

app.pagescms.org → GitHub 로그인 → 이 저장소 선택 → 「상세페이지」에서 카피·섹션 순서·여백 폼 편집 → 저장 = 커밋 → GitHub Actions가 자동 재조립·발행 (~1분).
설정 파일 = `.pages.yml` (필드 라벨 한국어).

## 로컬 미리보기

```
cd ~/Documents/simplekey-landing && python3 -m http.server 8732
→ http://localhost:8732/p/consulting/
```
