# Wylie Fix Handoff — `equiv-tib-chn-great`

Spawn: `serene-herschel-91f856`
Branch: `claude/serene-herschel-91f856`
Base: `276f424` (Phase 2.5)

## Summary

Replaced the in-house char-by-char Tibetan→Wylie converter with **pyewts**
(standard EWTS, root-letter-aware, stack-aware). Re-processed the 30,889-row
JSONL in place. `verify.py` warnings on this dict dropped **30,851 → 38
(−99.88%)**, errors stay at **0**.

## Numbers

| Metric                           | Before     | After  | Δ            |
|----------------------------------|-----------:|-------:|-------------:|
| `equiv-tib-chn-great` warnings   | 30,851     | 38     | −30,813      |
| `equiv-tib-chn-great` errors     | 0          | 0      | 0            |
| Rows with Wylie populated        | 30,851     | 30,851 | 0            |
| Total rows                       | 30,889     | 30,889 | 0            |

The 38 residual warnings are rows whose `headword` is a lone shad `།`
(OCR-extracted punctuation, no convertible letters). pyewts produces an
empty Wylie for these; the postprocess falls back to the Tibetan-unicode
passthrough so the schema's `headword_iast` length≥1 invariant holds.
These are pre-existing data-quality issues, not Wylie quality.

## Quality samples

| `headword`                                  | Before (custom)                  | After (pyewts)              |
|---------------------------------------------|----------------------------------|-----------------------------|
| `རྟགས་ཀྱི་སོན་ལ་བཀོད་ཡོད།`                  | `rtgsa kyi son la bkod yod`      | `rtags kyi son la bkod yod` |
| `བསྟན`                                      | `bstna`                          | `bstan`                     |
| `བྱང་ཆུབ་སེམས་དཔའ`                          | (mis-stacked)                    | `byang chub sems dpa'`      |
| `མཐུན་ཀྐྱེན་…`                              | (no stack handling)              | `mthun k+k+yen …`           |

Root letter is now correctly identified, super/sub stacks render with `+`
notation per EWTS, prefixes/suffixes follow standard rules.

## Code changes

- [`pyproject.toml`](pyproject.toml) — adds `pyewts>=0.2.0` runtime dep and a
  `[tool.uv]` `extra-build-dependencies` entry pinning `setuptools<81` for
  pyewts's build env (pyewts imports `pkg_resources`, removed in setuptools 81+).
- [`scripts/lib/transliterate.py`](scripts/lib/transliterate.py) — adds
  `_has_tibetan` + `tibetan_to_wylie` helpers; `detect_and_convert_to_iast`
  now routes Tibetan unicode through pyewts so
  `normalize_headword(headword)` matches the stored `headword_norm`.
  Lazy-imported pyewts (only loaded on first Tibetan input).
- [`scripts/postprocess_tib_chn_wylie.py`](scripts/postprocess_tib_chn_wylie.py)
  — uses `tibetan_to_wylie` from the shared lib instead of the in-house
  `to_wylie`. Adds an `else` branch to restore `headword_iast` to the
  Tibetan unicode passthrough when Wylie is empty (lone-shad rows), so
  schema's length≥1 invariant survives idempotent re-runs.
- `scripts/lib/tibetan_wylie.py` — **untouched**, kept for reference; no
  longer imported by any active script.
- [`data/sources/equiv-tib-chn-great/meta.json`](data/sources/equiv-tib-chn-great/meta.json)
  — `postprocess.wylie_converter` flipped to `"pyewts"`,
  `wylie_kind` to `"standard-ewts (root-letter aware, stack-aware)"`.

## Data artifact

`data/jsonl/equiv-tib-chn-great.jsonl` (43 MB, 30,889 rows) is regenerated.
JSONL is gitignored, so the main session must `cp` it from the spawn worktree:

```sh
SPAWN=.claude/worktrees/serene-herschel-91f856
cp "$SPAWN/data/jsonl/equiv-tib-chn-great.jsonl" data/jsonl/equiv-tib-chn-great.jsonl
```

MD5 of the new file: `2647358969714a7dfd4934c5d8f5da46`

## Merge procedure

1. **Code changes** (auto-merge via PR or fast-forward):
   - `pyproject.toml`, `uv.lock`
   - `scripts/lib/transliterate.py`
   - `scripts/postprocess_tib_chn_wylie.py`
   - `data/sources/equiv-tib-chn-great/meta.json`
2. **Data artifact** — copy as above (gitignored).
3. **Verify locally** (optional, since spawn already did this):
   ```sh
   uv sync
   uv run python -m scripts.verify --dicts equiv-tib-chn-great
   ```
   The full repo's verify currently fails on the meta-registry pre-check
   for hopkins-family slugs (`equiv-hopkins`, `tib-hopkins-*`,
   `equiv-lin-4lang`, `equiv-yogacara-index`) — those errors are
   **pre-existing**, unrelated to this change. To verify just this dict
   without that pre-check noise, isolate sources:
   ```sh
   mkdir -p /tmp/verify-tib && cp -R data/sources/equiv-tib-chn-great /tmp/verify-tib/
   uv run python -m scripts.verify --sources /tmp/verify-tib --jsonl data/jsonl
   # Expected: 0 errors, 38 warnings
   ```

## Side effects to be aware of

`detect_and_convert_to_iast` now handles Tibetan, which means **any other
script that invokes `normalize_headword()` on a Tibetan unicode string will
now get Wylie back instead of NFD-stripped Tibetan**. If any other build
script relies on the old passthrough behavior for Tibetan, it would now see
Wylie. A quick `grep -r normalize_headword scripts/` should catch callers,
but no Tibetan-headword dict besides `equiv-tib-chn-great` is currently
post-processed for Wylie, so this is unlikely to bite.

`pyewts` is now a hard runtime dep. Builders that don't need Tibetan still
import the module on first Tibetan call only (lazy-init in `_EWTS`),
so the import cost is zero for non-Tibetan paths.

## Done / Not done

Done:
- [x] `uv add pyewts` (with `setuptools<81` build-env pin)
- [x] `to_wylie` replaced with standard EWTS
- [x] `equiv-tib-chn-great.jsonl` re-processed (idempotent)
- [x] verify warnings reduced from 30,851 → 38 (−99.88%)
- [x] errors stay at 0

Not done (out of scope):
- Hopkins-family meta-registry errors (pre-existing, separate task).
- Dropping the 38 lone-shad garbage rows (would need source-extract change).
- `scripts/lib/tibetan_wylie.py` left as dead code; safe to delete in a
  follow-up if no one imports it.
