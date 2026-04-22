# Sanskrit-Tibetan Workspace

산스크리트·티벳·한문 다중 사전 검색 + 곡용(Declension) + 독해 + 어휘 웹 워크스페이스 (v2).

v1 (`sanskrit_tibetan_reading_workspace`)의 후속으로, 검색 성능 문제와
사용자 피드백을 근본적으로 해결하기 위해 전면 재설계.

---

## v1 대비 개선점

v1은 정적 호스팅에서 2.3GB SQLite를 브라우저가 HTTP Range로 직접 쿼리하는
구조였습니다. 기발하지만 아키텍처적으로 틀림 — 첫 검색 5-10초, 매 검색 1-3초.

v2는 7대 원칙으로 재설계:

1. **Edge Compute First** — Cloudflare Workers + D1 (무료 티어로 충분)
2. **Frequency-Tiered Storage** — 상위 1만 단어 메모리, 나머지 lazy
3. **Offline-First** — Service Worker + OPFS
4. **Data as Artifact** — JSONL 포맷, SQLite는 검색 엔진일 뿐
5. **Streaming UI** — Svelte 5 + nanostores
6. **URL-as-State** — 완전한 상태 복원
7. **Plugin Architecture** — 사전 하나 추가 = 디렉터리 하나 추가

또한 v1 사용자 피드백을 데이터 레이어와 UI에서 해결:

- **Smart snippets** — 문장 경계 기반 (50자 잘림 문제) · FB-1
- **Translation coverage** — DE/FR/LA/RU 재번역 batch · FB-2
- **Priority ordering** — Apte #1, MW #2 명시적 순서 · FB-3
- **IAST 표시 강제** — 모든 산스크리트 UI에 IAST (HK/Devanagari 노출 금지) · FB-4
- **Declension 탭 분리** — Heritage 곡용 사전을 별도 탭으로 · FB-5
- **다크모드** — 시스템 기본 + 사용자 토글 · FB-6
- **이름 변경** — Nighaṇṭu → Sanskrit-Tibetan Workspace · FB-7

상세 설계: `ARCHITECTURE.md` · 로드맵: `ROADMAP.md` · 피드백 대응: `docs/v1-feedback.md`

---

## 탭 구조

v2는 3개 메인 탭:

| 탭 | 기능 | 위치 |
|----|------|------|
| **검색** (Search) | 135개 사전 통합 검색 (곡용 사전 제외) | `/` |
| **곡용** (Declension) | Heritage 기반 산스크리트 곡용표 조회·생성 | `/declension` |
| **독해** (Reader) | 텍스트 읽기 + 토큰 클릭 검색 (Phase 6+) | `/reader` |

독해 + 어휘는 Phase 6 이후 (v1에서 포팅).

---

## 디렉터리 구조

```
sanskrit-tibetan-workspace/
├── README.md                     ← 이 문서
├── ARCHITECTURE.md               ← 설계 원칙 + 기술 스택
├── ROADMAP.md                    ← Phase별 계획
├── package.json                  ← Svelte + Vite
├── scripts/                      ← Python 데이터 파이프라인
│   ├── extract_from_v1.py        ← v1 dict.sqlite → JSONL
│   ├── build_tier0.py            ← top-10K memory index
│   ├── build_fst.py              ← autocomplete FST
│   ├── build_declension.py       ← Heritage → paradigm tables
│   ├── audit_translations.py     ← 번역 coverage 리포트
│   ├── translate_batch.py        ← Claude batch 재번역
│   └── verify.py                 ← 정합성 검증
├── src/                          ← Svelte 프론트엔드
│   ├── lib/                      ← 검색 엔진, 상태 관리, 테마
│   ├── routes/
│   │   ├── +page.svelte          ← / (검색)
│   │   ├── declension/           ← /declension
│   │   └── reader/               ← /reader (Phase 6+)
│   └── styles/
│       ├── theme.css             ← 라이트/다크 CSS 변수 (OKLCH)
│       └── global.css
├── public/
│   └── indices/                  ← 빌드된 정적 인덱스 (gitignored)
├── data/                         ← 원본 + 중간 산출물 (gitignored)
│   ├── jsonl/                    ← 사전별 JSONL
│   ├── declension/               ← paradigm 데이터
│   └── indices/                  ← 빌드된 바이너리 인덱스
├── tests/                        ← Vitest + Playwright
└── docs/
    ├── schema.json               ← JSONL 엔트리 스키마
    ├── dict-source.md            ← 사전 plugin 명세
    ├── declension-tab.md         ← 곡용 탭 상세 설계
    ├── v1-feedback.md            ← 사용자 피드백 대응
    └── decisions-pending.md      ← ADR 초안
```

---

## 상태

**계획 단계.** 아직 코드 없음.

- [x] Phase 0: 프로젝트 뼈대 + 설계 문서
- [x] Phase 1: 데이터 추출 파이프라인 (v1 → JSONL, 130 dicts, 3.36M entries)
- [x] Phase 2: Tier 0 인덱스 + FST + 역인덱스 (49 MB, cold load <700ms)
- [ ] Phase 3: Svelte UI (검색 + 다크모드)
- [ ] Phase 3.5: Declension 탭
- [ ] Phase 4: 배포
- [ ] Phase 5: Edge API
- [ ] Phase 6+: Reader + Vocab 포팅

---

## 라이선스

- **코드**: MIT (TBD)
- **데이터**: 각 원본 사전의 라이선스 승계. `LICENSES.md` 참조 (v1에서 가져옴)

## 연락

naspatterns@gmail.com
