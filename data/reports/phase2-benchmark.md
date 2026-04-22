# Phase 2 Index Benchmark

## Artifact sizes

| File | Size |
|---|---:|
| `public/indices/tier0.msgpack.zst` | 27.42 MB |
| `public/indices/reverse_en.msgpack.zst` | 14.85 MB |
| `public/indices/reverse_ko.msgpack.zst` | 92.6 KB |
| `public/indices/headwords.txt.zst` | 6.58 MB |

## Tier 0 (top-10K in-memory)

- Headwords: **10,000**
- Total entries: **355,648** (avg 35.6/hw)
- **Cold load (decompress + msgpack): 606.4 ms**

- Hit lookup median: **0.2 µs**  (p95 0.3 µs)
- Miss lookup median: **0.1 µs**

## Reverse index (English → Sanskrit/Tibetan)

- Tokens: **318,221**
- Cold load: **406.6 ms**
- Hit lookup median: **0.3 µs**  (p95 0.7 µs)
- Example: `fire` → 100 entries, first: `apte-sanskrit-english-031577`
- Example: `duty` → 100 entries

## Reverse index (Korean → original)

- Tokens: **532** (limited — expands after Phase 2 En→Ko batch)
- Cold load: **1.6 ms**
- Example: `법` → 100 entries

## Grand total

- **All Phase 2 indices: 48.94 MB**

### Comparison with ROADMAP targets

| Metric | Target | Actual |
|---|---|---|
| Tier 0 size | ~30 MB | 27.42 MB |
| Tier 0 cold load | <2s on 4G | 606 ms local |
| Search response (cache hit) | <50 ms | 0.2 µs |