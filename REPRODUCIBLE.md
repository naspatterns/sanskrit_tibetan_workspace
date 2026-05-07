# REPRODUCIBLE.md — Step-by-step rebuild guide

This document captures the **exact** sequence of commands to take the
repository from a fresh clone to a fully functional `npm run preview`,
identical to the production build at the date below. Includes Phase 5
(Edge API + D1) setup as of 2026-05-05.

**Last verified**: 2026-05-05 · main `c615b0a`

---

## 0. Environment prerequisites

```bash
# macOS / Linux. Windows works in WSL.
python --version            # 3.12.x
node --version              # 20.x or higher
which uv && uv --version    # uv 0.4.x or higher (https://docs.astral.sh/uv/)
which npm
```

Required workspace **outside this repo** (read-only):

```bash
ls "/Users/jibak/Library/CloudStorage/GoogleDrive-naspatterns@gmail.com/내 드라이브/haMsa CODE/sanskrit_tibetan_reading_workspace/build/dict.sqlite"
# → must exist; this is the v1 source of truth (3.36M entries × 130 dicts).
```

---

## 1. Fresh clone & install

```bash
git clone <repo>
cd sanskrit-tibetan-workspace

# Python venv (managed by uv)
uv sync

# Node deps
npm install
```

This installs **Python 3.12** + dependencies (`zstandard`, `msgpack`,
`tqdm`, `fastjsonschema`, `pytest`, etc.) and **Node 20** + dependencies
(`svelte`, `vite`, `vitest`, `fzstd`, `@msgpack/msgpack`, etc.).

---

## 2. Phase 1 — JSONL extraction from v1 SQLite

```bash
# Build per-dict meta.json (130 + 18 equiv = 148 dicts)
uv run python -m scripts.build_meta

# Extract entries from v1 SQLite (5 workers, ~6 minutes)
uv run python -m scripts.extract_from_v1
# → data/jsonl/<slug>.jsonl   (3.36M entries, ~5.6 GB, gitignored)
# → data/jsonl/<slug>.meta.json  (per-dict counts)
```

Phase 2.5 spawn dicts (Zone B 대응어, AmaraKośa NLP, Tib-Chn Wylie etc.)
are extracted by their respective `extract_equiv_*.py` scripts. These
were already invoked once and committed via the equivalents pipeline
in earlier phases; for a fresh rebuild, run the spawn extraction scripts
listed in `data/sources/<slug>/meta.json:extract_script` for each
`role: equivalents` dict.

```bash
# Verify (16s with 5 workers + fastjsonschema)
uv run python -m scripts.verify
# Expected: Dicts 148 · Entries 3,815,934 · Errors 0 · Warnings ~141K (non-critical)
```

---

## 3. Phase 2b + 3.7 — apply translations to JSONL

The translations are committed as JSONL diffs and **not yet baked into
JSONL** because Phase 2b's design preserved JSONL as the canonical v1
extraction.

```bash
# Apply 9,995 (Phase 2b top-10K) + 39,873 (Phase 3.7 P1-2 top-10K..50K)
# Korean translations to body.ko fields, also recomputes reverse.ko[].
uv run python -m scripts.apply_translations_to_jsonl
# Expected: "Applied 49,868 new ko translations across 31 dicts"
```

This step is **idempotent** — re-running has no effect since the script
preserves existing v1 body.ko (skips when present).

After this step, JSONL Korean coverage rises **11.31% → 12.79%**.

---

## 4. Phase 2 + 3.7 — build all 9 indices

Run in this order (each command stands alone; no shared state besides
files on disk):

```bash
# 1. Top-10K (Sanskrit) — frequency + canonical importance boost
uv run python -m scripts.frequency
# Output: data/reports/top10k.txt  (10,000 norm headwords)

# 2. Top-20K — same scoring, larger cut for tier0-extended
uv run python -m scripts.frequency --top-n 20000 --out-top data/reports/top20k.txt

# 3. Split top-20K into top-10K..20K for the extended index
python3 -c "
with open('data/reports/top20k.txt') as f:
    lines = [l.strip() for l in f if l.strip()]
with open('data/reports/top10k_to_20k.txt', 'w') as f:
    f.write('\n'.join(lines[10000:20000]) + '\n')
"

# 4. Tibetan top-10K (separate language scoring)
uv run python -m scripts.frequency --lang-filter bo --out-top data/reports/top10k_bo.txt

# 5. Tier-0 indices (3 files: Sanskrit / Tibetan / Sanskrit-extended)
uv run python -m scripts.build_tier0
uv run python -m scripts.build_tier0 \
    --top10k data/reports/top10k_bo.txt \
    --out public/indices/tier0-bo.msgpack.zst
uv run python -m scripts.build_tier0 \
    --top10k data/reports/top10k_to_20k.txt \
    --out public/indices/tier0-extended.msgpack.zst

# 6. Reverse indices (en + ko, with EN/KO synonym injection)
uv run python -m scripts.build_reverse_index

# 7. Reverse meta (id → [iast, dict_idx])
uv run python -m scripts.build_reverse_meta

# 8. Headwords (autocomplete) with rank + upasarga columns
uv run python -m scripts.build_fst

# 9. Equivalents (Zone B)
uv run python -m scripts.build_equivalents_index

# 10. Heritage Declension paradigms
uv run python -m scripts.build_declension
```

### Expected output sizes (Cloudflare 25 MiB cap per file)

| Index | Compressed | Notes |
|---|---:|---|
| `tier0.msgpack.zst` | **23 MB** | top-10K Sanskrit · zstd-22 + long-range mode |
| `tier0-bo.msgpack.zst` | 7.7 MB | top-10K Tibetan |
| `tier0-extended.msgpack.zst` | 9.1 MB | top-10K..20K Sanskrit (Phase 3.7 A) |
| `reverse_en.msgpack.zst` | 17 MB | 317,884 tokens · EN synonym 193 inj |
| `reverse_ko.msgpack.zst` | 918 KB | 20,962 tokens · KO synonym 89 inj |
| `reverse_meta.msgpack.zst` | 8.9 MB | id → [iast, dict_idx] |
| `equivalents.msgpack.zst` | 12 MB | 424,820 keys · CJK gate |
| `declension.msgpack.zst` | 2.0 MB | 38,815 paradigm rows |
| `headwords.txt.zst` | 7.7 MB | 1,071,112 entries · 4-col TSV |
| **Total** | **~89 MB** | All under 25 MiB single-file cap |

---

## 5. Phase 3 — Svelte/SvelteKit frontend

```bash
# Run unit tests (Python + TypeScript)
uv run pytest -q                       # 79 tests
npm test                               # 104 tests

# Type-check (Svelte + TypeScript)
npx svelte-check --threshold error    # Expected: 0 errors / 0 warnings

# Dev server
npm run dev                           # http://localhost:5173

# Production build (adapter-static — outputs to ./build/)
npm run build

# Local preview of production bundle
npm run preview                       # http://localhost:4173
```

---

## 6. Audit + Sentinel verification (verify quality)

```bash
# Translation coverage
uv run python -m scripts.audit_translations
# Expected: "Overall Korean coverage: 12.79% (430,939 / 3,369,435)"

# Reverse search precision (audit-A)
uv run python -m scripts.audit_reverse_precision
# Expected: "EN strict=15/15 loose=15/15 · KO strict=15/15 loose=15/15"

# Sentinel 50 — curated UX-walkthrough simulation
uv run python -m scripts.audit_sentinel_50
# Expected: "총합: ✅ 50 · ⚠️ 0 · ❌ 0"

# Sentinel 215 — extended (50 + 165 mid/long-tail/cross-channel/upasarga)
uv run python -m scripts.audit_sentinel_200
# Expected: "총합: ✅ 202/215 (94.0%) · ⚠️ 6 · ❌ 7"

# Random lookup integrity (statistical sample)
uv run python -m scripts.audit_random_lookup
# Expected: All 7 indices @ 100%
```

---

## 7. Phase 3.7 data assets (curated, committed)

These power the Phase 3.7 quality lifts and are loaded by the build
scripts above:

```
data/sources/_canonical/important.txt    # 332 philosophical 핵심어
data/sources/_kosynonym/synonyms.json    # 52 iast → 89 KO/Hanja
data/sources/_ensynonym/synonyms.json    # 113 iast → 193 EN tokens
data/sources/_upasarga/upasarga.json     # 23 SA + 30 BO canonical prefixes
data/translations.jsonl                  # 9,995 top-10K Phase 2b ko
data/translations-en-extended.jsonl      # 39,873 top-10K..50K Phase 3.7 ko
```

To re-derive `data/translations.jsonl` itself from scratch see
`scripts/translate_via_subagent.py` (Phase 3.7 P1-2 sub-agent path).
That requires a long-running Claude Code session and is **not** part
of the standard rebuild — the file is committed because it represents
~$130 of API budget.

---

## 8. Reproducibility checks

After rebuild, the following invariants should hold:

```bash
# Test invariants
uv run python -c "
import zstandard as zstd, msgpack
from pathlib import Path

t0 = msgpack.unpackb(zstd.ZstdDecompressor().decompress(
    Path('public/indices/tier0.msgpack.zst').read_bytes()),
    raw=False, strict_map_key=False)
assert len(t0) == 10_000, f'tier0 should have 10K keys, got {len(t0)}'
assert 'agni' in t0
assert 'dharma' in t0

ext = msgpack.unpackb(zstd.ZstdDecompressor().decompress(
    Path('public/indices/tier0-extended.msgpack.zst').read_bytes()),
    raw=False, strict_map_key=False)
assert len(ext) == 10_000, f'tier0-ext should have 10K keys, got {len(ext)}'

# Headwords integrity
import zstandard
hw = zstandard.ZstdDecompressor().decompress(
    Path('public/indices/headwords.txt.zst').read_bytes()).decode('utf-8')
lines = [l for l in hw.splitlines() if l]
assert len(lines) == 1_071_112, f'headwords should be 1.07M, got {len(lines)}'
# Sample 4-col TSV check
parts = lines[0].split('\\t')
assert len(parts) == 4, f'headwords.txt.zst expects 4 cols, got {len(parts)}'

print('✓ All reproducibility invariants hold')
"
```

---

## 9. Phase 5 — Cloudflare Workers + D1 (already deployed)

Phase 5 was completed in commit `c615b0a` (2026-05-05). The Worker is
deployed at `https://stw-api.naspatterns.workers.dev` backed by D1
database `stw-entries` (id `b53085a2-bece-419b-85c7-491df9dadd35`).

### To rebuild Phase 5 from scratch (or fork)

```bash
# 0. Wrangler auth (once per machine)
npm install -g wrangler
wrangler login                           # OAuth via browser (or CLOUDFLARE_API_TOKEN env var)
wrangler whoami                          # verify

# 1. Create D1 database
cd workers
wrangler d1 create stw-entries
# → copy the printed `database_id` to wrangler.toml

# 2. Apply schema
wrangler d1 execute stw-entries --remote --file=sql/schema.sql

# 3. Generate SQL chunks (60 files, ~2.98M rows, ~565 MB)
cd ..
uv run python -m scripts.frequency --out-full data/reports/frequency.json
uv run python -m scripts.build_d1_dump --rank-cutoff 9999999999

# 4. Bulk import (resumable; ~5 min total at 10s per chunk)
cd workers
bash import_all.sh

# 5. Deploy Worker
wrangler deploy

# 6. Verify (8/8 ✅ expected)
cd ..
uv run python -m scripts.audit_d1_integrity
```

### To re-import after schema change

```bash
# Drop + re-create
cd workers
wrangler d1 execute stw-entries --remote --command="DROP TABLE entries"
wrangler d1 execute stw-entries --remote --file=sql/schema.sql

# Clear .done markers and re-run
rm -f sql/*.done
bash import_all.sh
```

### Cloudflare D1 free tier limits (as of 2026)

| Quota | Free | Used (current) | Headroom |
|---|---:|---:|---:|
| Storage | 5 GB | 780 MB | 84% free |
| Reads/day | 5M rows | <1K | 99.99% free |
| Writes/day | 100K rows | 0 (read-only after import) | 100% free |
| Workers requests/day | 100K | <100 | 99.9% free |

→ No paid plan needed for current scale.

---

## 10. Phase 4 — production deploy (Cloudflare Pages, ✅ first deploy)

**Live**: https://sanskrit-tibetan-workspace.pages.dev (commit `ba8e5f6`)

### 10.1 Pre-flight

```bash
# All must pass
uv run pytest -q                        # 79
npm test                                # 104
npx svelte-check --threshold error      # 0/0
npm run build                           # build/ 89 MB
```

### 10.2 Build artifact size guard

```bash
du -sh build/                           # ~89 MB total
ls -lh build/indices/*.zst | awk '$5+0 > 25 { exit 1 }' \
  && echo "✓ All indices under 25 MiB Cloudflare per-file limit"
```

### 10.3 First-time Pages project setup (one-off)

In Cloudflare dashboard → Workers & Pages → Create application → Pages →
Connect to Git, then:
- Framework preset: **None** (the auto-detect will fail because of the
  symlink — see §10.5)
- Build command: leave empty (we deploy via wrangler)
- Build output directory: `build/`

Confirm project exists:
```bash
npx wrangler pages project list
# sanskrit-tibetan-workspace · sanskrit-tibetan-workspace.pages.dev
```

### 10.4 Production deploy (every release)

```bash
npm run build
npx wrangler pages deploy ./build \
  --project-name=sanskrit-tibetan-workspace \
  --branch=main \
  --commit-message="Phase 4: <ASCII description>" \
  --commit-hash=$(git rev-parse --short HEAD)
```

**중요**: `--commit-message` 명시 필수.
미지정시 wrangler가 `git log -1`을 읽어서 commit message를 attach 시도하는데,
한글/em-dash가 포함된 메시지에서 UTF-8 인코딩 오류 (`code: 8000111`)로 deploy
실패 (파일 업로드는 성공한 뒤 commit attach 단계에서). ASCII-only 명시 시
정상 동작.

### 10.5 GitHub auto-build이 실패하는 이유 (의도적)

GitHub push trigger로 발생하는 자동 빌드는 항상 실패함. 원인:
- `static/indices` is a symlink → `../public/indices`
- `public/indices/*.zst` is gitignored (89 MB, regenerable)
- GitHub clone에서 심볼릭 링크는 보존되지만 target dir이 없음
- `adapter-static`이 broken symlink 따라가다 빌드 실패

해결: 자동 빌드는 무시하고 manual `wrangler pages deploy`만 사용. CI가
`pytest` + `vitest` + `svelte-check` + `dry-build` (broken symlink을
empty dir로 대체) 통해서 빌드 가능성만 검증.

### 10.6 CSP allow Worker API origin

`static/_headers`의 `Content-Security-Policy: ... connect-src 'self'`만
있으면 Phase 5 Edge API (`stw-api.naspatterns.workers.dev`)로의
cross-origin fetch가 차단되어 long-tail entries (vajracchedikā, śūraṅgama)
가 production에서 silent-fail. Fix: `connect-src 'self'
https://stw-api.naspatterns.workers.dev` (commit `8664e9a`).

### 10.7 Verify live deploy

```bash
# HTTP 200 + CSP 확인
curl -sI -A "Mozilla/5.0 verify" \
  https://sanskrit-tibetan-workspace.pages.dev/ \
  | grep -E "(HTTP/|content-security-policy:|server:)"

# Indices served correctly (cache-control: immutable, 1 year)
curl -sI -A "Mozilla/5.0 verify" \
  https://sanskrit-tibetan-workspace.pages.dev/indices/headwords.txt.zst

# Worker API end-to-end (8/8 ✅)
uv run python -m scripts.audit_d1_integrity
```

---

## 11. Known reproducibility caveats

1. **`extract_from_v1.py`** depends on `dict.sqlite` from v1 workspace
   (immutable reference). If absent, JSONL cannot be regenerated.
2. **`translations*.jsonl`** files (Korean) are committed because
   regenerating requires LLM API or sub-agent budget.
3. **JSONL gitignored** by design (licensing concern: aggregated content
   from third-party dicts). To share, ship `data/sources/<slug>/meta.json`
   + `extract_*.py` + `dict.sqlite` separately under each dict's license.
4. **Multiprocessing**: `extract_from_v1.py` and `verify.py` are parallel
   (5 workers). `frequency.py`, `build_tier0.py`, `build_reverse_index.py`
   are single-process — Phase 5+ optimization deferred.
5. **CLAUDE.md** is gitignored (per-machine workflow). Sync manually
   between worktrees.
