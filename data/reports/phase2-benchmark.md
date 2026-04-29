# Phase 2 Index Benchmark

## Artifact sizes

| File | Size |
|---|---:|
| `public/indices/tier0.msgpack.zst` | 28.53 MB |
| `public/indices/reverse_en.msgpack.zst` | 14.82 MB |
| `public/indices/reverse_ko.msgpack.zst` | 143.5 KB |
| `public/indices/headwords.txt.zst` | 7.76 MB |

## Tier 0 (top-10K in-memory)

- Headwords: **10,000**
- Total entries: **352,851** (avg 35.3/hw)
- **Cold load (decompress + msgpack): 830.1 ms**

- Hit lookup median: **0.3 µs**  (p95 0.6 µs)
- Miss lookup median: **0.2 µs**

## Reverse index (English → Sanskrit/Tibetan)

- Tokens: **317,878**
- Cold load: **458.9 ms**
- Hit lookup median: **0.4 µs**  (p95 0.9 µs)
- Example: `fire` → 100 entries, first: `apte-sanskrit-english-031577`
- Example: `duty` → 100 entries

## Reverse index (Korean → original)

- Tokens: **3,102** (limited — expands after Phase 2 En→Ko batch)
- Cold load: **7.3 ms**
- Example: `법` → 100 entries

## Grand total

- **All Phase 2 indices: 51.25 MB**

### Comparison with ROADMAP targets

| Metric | Target | Actual |
|---|---|---|
| Tier 0 size | ~30 MB | 28.53 MB |
| Tier 0 cold load | <2s on 4G | 830 ms local |
| Search response (cache hit) | <50 ms | 0.3 µs |