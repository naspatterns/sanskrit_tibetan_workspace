# audit-C-demo-guide — Sentinel demo 사용자 시연 가이드

Date: 2026-04-30
Production preview: `http://localhost:4173/`
Sentinel queries: `data/reports/audit-2026-04-30/sentinel-50-queries-draft.md`

## 사전 준비

```bash
# 1. Production preview server 실행 (이미 시작되었거나 재시동)
cd /path/to/sanskrit-tibetan-workspace
npm run preview                 # localhost:4173

# 2. 별도 터미널에서 결과 기록 파일 준비
cd data/reports/audit-2026-04-30
touch audit-C-sentinel-results.csv
```

CSV 헤더:
```csv
#,query,category,top_3_retrieved,verdict,latency_ms,notes
```

## 시연 절차 (1.5-2시간)

### 0. 첫 방문 시 (cold load 측정)

1. Chrome devtools 열기 (F12) → Network 탭 → Disable cache 체크 (cold)
2. Application 탭 → Service Workers → "Unregister" 버튼 (이전 SW 제거)
3. Application 탭 → Cache Storage → 모든 stw-indices-* 삭제
4. 페이지 새로고침 → Splash 화면 표시 → 모든 indices 다운로드 완료까지 대기
5. **Network 탭에서 측정**: 첫 7 indices 다운로드 총 시간 (예상 3-5초)

### 1-15: 카테고리 1+2 (산스크리트 핵심 + prefix)

각 query마다:
1. 검색창에 query 입력
2. 결과 관찰:
   - top-3 entries (Apte/MW/Macdonell이 우선?)
   - Zone A (정의) / Zone B (대응어) / 자동완성 박스
3. CSV에 기록:
   ```
   1,dharma,1,"apte/mw/macdonell:dharma",✅,<5,Apte 우선 정렬 정상
   2,ātman,1,"apte:ātman/mw:ātman/...",✅,<5,diacritic input ok
   ...
   ```

**P0/P1 fix 전 baseline**이므로 결과 그대로 기록.

### 16-20: 카테고리 3 (티벳어 Wylie)

`klong chen` 같은 단어 입력 → Zone A에 9 entries 표시 예상 (audit B3).

특히 #19 `rdo rje` (vajra 대응어) — equivalents Wylie channel 작동 확인.

### 21-30: 카테고리 4 (영어 역검색)

⚠️ **현재 baseline은 Track A audit에서 측정된 대로 부정확** (P0-1, P1-1):
- top-5에 `agni`, `dharma` 등 핵심어가 안 나옴 (homiḥ, hradaḥ 등 후위 단어)
- Raw `entry_id`만 표시 (UI P0-1)

기록 시 verdict는 ❌, notes에 "current state"만.

### 31-35: 카테고리 5 (한국어 역검색)

특히 `자비/공/도` = 0 hits → "결과 없음" 메시지 확인.

### 36-40: 카테고리 6 (한자)

법/空/菩薩/涅槃/如來 — equivalents zh channel.

### 41-45: 카테고리 7 (혼용/sandhi)

`mahābhārata`, `tat tvam asi` 같은 다단어 + 고유명. 자동완성 + 검색 모두 작동 확인.

### 46-48: 카테고리 8 (Edge)

- `dharmaaa` (3 a) — "결과 없음" 메시지 우아한지
- `aaa` — 마찬가지
- 공백만 — 초기 화면 유지

### 49-50: 카테고리 9 (Dead zone)

- `decl-a01` 검색 → 결과 0건 (audit B7에서 0 leak 확인 ✅)
- `aṃśanīya@aṃś` (Heritage decl 형식) → 결과 0건

## 추가 사용자 검증 (Day 3 deferred items)

### D4 — Heap profile (수동 측정)

1. Chrome devtools → Memory 탭
2. "Take heap snapshot" → 명칭 "1. cold load done"
3. 검색 30회 (다양한 카테고리) 후 "Take heap snapshot" → "2. after 30 searches"
4. 비교: heap 증가량이 < 10 MB이면 leak 없음. > 50 MB면 leak 의심.

### D9 — Declension HMR race verify in production

1. URL 직접 입력: `http://localhost:4173/declension?q=deva`
2. 입력창에 `deva` 자동 채워지는지 확인
3. dev mode와 비교 (`npm run dev` localhost:5173/declension?q=deva)

**예상**: prod에서 자동 채워짐 (HMR 없으니 race 없음).

### 모바일 시뮬

1. Chrome devtools → Device toolbar (Ctrl+Shift+M)
2. iPhone SE (375×667) 선택
3. 검색 + 결과 + 곡용 페이지 layout 확인:
   - 검색바가 폭 안에 맞나?
   - top bar 4 요소 (Search/Decl/검색input/Theme)이 wrap?
   - Equivalents chip wrap?

이 결과는 별도 `audit-C-mobile.md`로 기록.

## 종합 평가

50 queries 끝나면:

```bash
# CSV summary
awk -F',' 'NR>1 {if($5=="✅") good++; else bad++} END {print "Good:",good,"Bad:",bad}' \
  audit-C-sentinel-results.csv
```

목표:
- Baseline (P0/P1 fix 전): 50 queries 중 25-35개 ✅ (P0-1/P1-1/P1-2 영향으로)
- After Phase 3.6 fix: 50 queries 중 ≥45 ✅

차이가 Phase 3.6의 가시적 가치.

## 산출물

```
data/reports/audit-2026-04-30/
├── audit-C-sentinel-results.csv       # 50 queries baseline
├── audit-C-mobile.md                  # 모바일 시뮬 결과 (수동)
└── (this file)
```

## 다음 세션 시 진행

1. 위 가이드대로 50 queries baseline 측정
2. Phase 3.6 P0-1 (reverse UI fix) 시작 — 가장 큰 영향
3. Phase 3.6 P0-2 ($225 batch submit) — 병행
4. Phase 3.6 P1 6건 fix
5. After-fix 50 queries 재측정 → diff 비교
6. Phase 4 deploy entry checklist (audit-E-deploy.md §6)
