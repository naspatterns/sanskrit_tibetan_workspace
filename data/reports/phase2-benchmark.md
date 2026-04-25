# Phase 2 Index Benchmark

## Artifact sizes

| File | Size |
|---|---:|
| `public/indices/tier0.msgpack.zst` | 28.62 MB |
| `public/indices/reverse_en.msgpack.zst` | 14.85 MB |
| `public/indices/reverse_ko.msgpack.zst` | 92.6 KB |
| `public/indices/headwords.txt.zst` | 6.58 MB |

## Tier 0 (top-10K in-memory)

- Headwords: **10,000**
- Total entries: **355,648** (avg 35.6/hw)
- **Cold load (decompress + msgpack): 593.6 ms**

- Hit lookup median: **0.1 µs**  (p95 0.2 µs)
- Miss lookup median: **0.1 µs**

## Reverse index (English → Sanskrit/Tibetan)

- Tokens: **318,221**
- Cold load: **398.5 ms**
- Hit lookup median: **0.4 µs**  (p95 0.9 µs)
- Example: `fire` → 100 entries, first: `apte-sanskrit-english-031577`
- Example: `duty` → 100 entries

## Reverse index (Korean → original)

- Tokens: **532** (limited — expands after Phase 2 En→Ko batch)
- Cold load: **1.7 ms**
- Example: `법` → 100 entries

## Grand total

- **All Phase 2 indices: 50.14 MB**

### Comparison with ROADMAP targets

| Metric | Target | Actual |
|---|---|---|
| Tier 0 size | ~30 MB | 28.62 MB |
| Tier 0 cold load | <2s on 4G | 594 ms local |
| Search response (cache hit) | <50 ms | 0.1 µs |