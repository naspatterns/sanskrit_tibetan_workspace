# Nighaṇṭu (निघण्टु)

Sanskrit–Tibetan–Chinese multi-dictionary lexicon, v2.

> *Nighaṇṭu* — the classical Sanskrit term for a glossary/lexicon.
> Yāska's *Nighaṇṭu* (~5th c. BCE) is the oldest known Indian lexicon.

**v2 의 목표**: 사용자가 검색어 치는 순간 결과가 보여야 한다 (<100ms).

---

## v1 대비 개선점

v1 (`sanskrit_tibetan_reading_workspace`)은 정적 호스팅에서 2.3GB SQLite를
브라우저가 HTTP Range로 직접 쿼리하는 기발하지만 아키텍처적으로 틀린 접근.
첫 검색 5-10초, 매 검색 1-3초. 사용자 불만 다수.

v2는 다음 원칙으로 재설계:

1. **Edge Compute First** — Cloudflare Workers + D1 (무료 티어로 충분)
2. **Frequency-Tiered Storage** — 상위 1만 단어 메모리, 나머지 lazy
3. **Offline-First** — Service Worker + OPFS
4. **Data as Artifact** — JSONL 포맷, SQLite는 검색 엔진일 뿐
5. **Streaming UI** — Svelte 5 + nanostores
6. **URL-as-State** — 완전한 상태 복원
7. **Plugin Architecture** — 사전 하나 추가 = 디렉터리 하나 추가

상세 설계: `ARCHITECTURE.md`
단계별 로드맵: `ROADMAP.md`

---

## 디렉터리 구조

```
nighantu/
├── README.md                     ← 이 문서
├── ARCHITECTURE.md               ← 설계 원칙 + 기술 선택
├── ROADMAP.md                    ← Phase별 실행 계획
├── package.json                  ← Svelte + Vite (TBD)
├── scripts/                      ← Python 데이터 파이프라인
│   ├── extract_from_v1.py        ← v1 dict.sqlite → JSONL (재사용)
│   ├── build_tier0.py            ← top-10K memory index
│   ├── build_fst.py              ← autocomplete FST
│   └── verify.py                 ← 정합성 검증
├── src/                          ← Svelte 프론트엔드
│   ├── lib/                      ← 검색 엔진, 상태 관리
│   ├── routes/                   ← 페이지
│   └── styles/                   ← CSS modules
├── public/
│   └── indices/                  ← 빌드된 정적 인덱스 (gitignored)
├── data/                         ← 원본 + 중간 산출물 (gitignored)
│   ├── jsonl/                    ← 사전별 JSONL
│   └── indices/                  ← 빌드된 바이너리 인덱스
├── tests/                        ← Vitest + Playwright
└── docs/                         ← 추가 문서
```

---

## 빠른 시작 (빌드 후)

```bash
# 개발 서버
pnpm install
pnpm dev

# 데이터 파이프라인 (v1 재사용)
python3 scripts/extract_from_v1.py   # v1 dict.sqlite → data/jsonl/
python3 scripts/build_tier0.py       # → public/indices/tier0.msgpack.zst
python3 scripts/build_fst.py         # → public/indices/autocomplete.fst
python3 scripts/verify.py            # 정합성 검증

# 프로덕션 빌드
pnpm build
```

---

## 상태

**계획 단계.** 아직 코드 없음. 다음 세션부터 구현 시작.

- [x] 프로젝트 뼈대
- [x] 설계 문서
- [x] 로드맵
- [ ] Phase 1: 데이터 추출 파이프라인 (v1 → JSONL)
- [ ] Phase 2: Tier 0 인덱스 + FST
- [ ] Phase 3: Svelte UI 최소 버전
- [ ] Phase 4: 배포
- [ ] Phase 5: Edge API (Cloudflare Workers)

---

## 라이선스

- **코드**: MIT (TBD)
- **데이터**: 각 원본 사전의 라이선스 승계. `LICENSES.md` 참조 (v1에서 가져옴)

## 연락

naspatterns@gmail.com
