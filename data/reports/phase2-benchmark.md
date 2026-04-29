# Phase 2 Index Benchmark

## Artifact sizes

| File | Size |
|---|---:|
| `public/indices/tier0.msgpack.zst` | 28.78 MB |
| `public/indices/reverse_en.msgpack.zst` | 14.79 MB |
| `public/indices/reverse_ko.msgpack.zst` | 92.6 KB |
| `public/indices/headwords.txt.zst` | 6.26 MB |

## Tier 0 (top-10K in-memory)

- Headwords: **10,000**
- Total entries: **370,186** (avg 37.0/hw)
- **Cold load (decompress + msgpack): 661.2 ms**

- Hit lookup median: **0.1 µs**  (p95 0.2 µs)
- Miss lookup median: **0.1 µs**

## Reverse index (English → Sanskrit/Tibetan)

- Tokens: **317,725**
- Cold load: **376.8 ms**
- Hit lookup median: **0.3 µs**  (p95 0.7 µs)
- Example: `fire` → 100 entries, first: `apte-sanskrit-english-031577`
- Example: `duty` → 100 entries

## Reverse index (Korean → original)

- Tokens: **532** (limited — expands after Phase 2 En→Ko batch)
- Cold load: **1.7 ms**
- Example: `법` → 100 entries

## Grand total

- **All Phase 2 indices: 49.91 MB**

### Comparison with ROADMAP targets

| Metric | Target | Actual |
|---|---|---|
| Tier 0 size | ~30 MB | 28.78 MB |
| Tier 0 cold load | <2s on 4G | 661 ms local |
| Search response (cache hit) | <50 ms | 0.1 µs |