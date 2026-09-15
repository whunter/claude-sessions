# IAWA Media Copy — Hand-off

## To resume

14 collections remain uncopied. Identifiers (S3 subdirectory name == CSV `identifier`, no mismatches among these):

```
Ms1998_022_Young
Ms2001_026_Jansone
Ms2002_004_Duncombe
Ms2003_015_Skala
Ms2004_004_Hastings
Ms2005_002_Treder
Ms2007_007_Feuerstein
Ms2007_009_Roth
Ms2008_089_Alexander
Ms2013_023_King
Ms2013_059_Manevich
Ms2013_088_Cochrane
Ms2013_090_Laleyan
Ms2016_012_Womens_Development_Corp
```

Note: `Ms2013_090_Laleyan` alone is ~2.84M objects / 319 GB — expect it to dominate remaining runtime.

## Copy command pattern

For each identifier `$id`:

```bash
aws s3 sync "s3://img.cloud.lib.vt.edu/iawa/${id}/" "s3://vtdlp-s3-tunnel-dev/iawa/${id}/"
```

Prefer `sync` over `cp --recursive` from the start this time — it's idempotent and safely re-runnable, which matters because both individual read-timeouts and full-job fatal errors were observed during this session (see session-summary.md). Re-run `sync` a second time after the first pass to mop up any stragglers, then verify with:

```bash
aws s3 ls "s3://img.cloud.lib.vt.edu/iawa/${id}/" --recursive --summarize | tail -2
aws s3 ls "s3://vtdlp-s3-tunnel-dev/iawa/${id}/" --recursive --summarize | tail -2
```

Object count and total size must match exactly between source and destination before considering a collection done.

## Concurrency guidance

Running many `aws s3 cp`/`sync` jobs in parallel (6 was tried) against `vtdlp-s3-tunnel-dev` produced transient read-timeout/connection errors under load — the destination endpoint seems to have a concurrency/throughput ceiling. A lower parallelism (e.g. 3-4) or running fully sequential (safer, slower) may reduce the retry overhead. Either way, always do a final `sync` + count-verification pass per collection — do not trust `cp --recursive`'s own exit code alone, since it can report success on individual files while a whole job aborts early on a listing-level fatal error.

## Environment gotcha

Do NOT run retry logic as a `while read line; do ...; done < file` loop inside a backgrounded shell task in this harness — it silently hung twice with zero output for 40+ minutes. Instead, generate a flat script of literal `aws s3 cp src dst` lines (e.g. via a small Python/awk pass over the failure list) and execute it directly, foreground or background — that pattern worked reliably.

## Untouched, no action needed

- Original files in `img.cloud.lib.vt.edu` were never modified — only read/listed.
- The user's own separate `aws s3 sync` (staging/bastion → `vtdlp-pprd.img.cloud.lib.vt.edu`) is unrelated to this task; leave it alone.
