# BARRED Track 1 — Seed 68 Evidence Audit

## Question audited

**Claim:** “The code is vulnerable to out-of-bounds kernel memory read in `isofs_export_get_parent` due to an unchecked `parent_offset` derived from a directory record length.”

**Result:** **Proved safe for this exact out-of-bounds-read claim.**

This result concerns the stated trigger — an ISO image whose “.” directory record carries an artificially large `length` field, making `parent_offset` exceed the block buffer. It does not claim anything about unrelated isofs parsing behavior, other Linux versions, or bugs elsewhere in the filesystem.

## What was examined

1. I selected seed 68 from the replicated Gemma/Gemini persistent-disagreement queue because the allegation is precise and mechanically checkable: an unchecked `parent_offset = isonum_711(de->length)` feeding `bh->b_data + parent_offset`.
2. I traced the source to the supplied `fs/isofs/export.c` excerpt (Linux isofs export operations). The relevant function is `isofs_export_get_parent`:
   ```c
   de = (struct iso_directory_record*)bh->b_data;
   parent_offset = (unsigned long)isonum_711(de->length);
   de = (struct iso_directory_record*)(bh->b_data + parent_offset);
   ```
3. I checked the type of `isonum_711`. It reads a single byte from the ISO 9660 directory record (`length` is a `__u8` at record offset 0). Therefore `isonum_711(de->length)` returns a value in `[0, 255]`.
4. I checked the buffer size in the matched Linux source. `bh` is the result of `sb_bread(child_inode->i_sb, parent_block)`, which reads `sb->s_blocksize`; Linux 3.18 isofs accepts logical-zone sizes of only `512`, `1024`, or `2048` and sets that block size before this path runs. Thus this buffer is at least 512 bytes.
5. Therefore `parent_offset ≤ 255 < 512 ≤ block_size`, so `bh->b_data + parent_offset` always points inside the allocated block buffer. The immediately used directory-record fields are also within the remaining 257 bytes: `name_len` is at offset 32, `name[0]` at offset 33, and `isofs_normalize_block_and_offset` accesses fields no later than the eight-byte `extent` field ending at offset 9. No separate `length`-versus-block-size check is required for this exact claimed read.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `de = (struct iso_directory_record*)(bh->b_data + parent_offset)` with `parent_offset` from `de->length`. | Identified precisely. |
| What is the maximum value of `parent_offset`? | `isonum_711` reads one byte (`__u8`), so at most 255. | Bounded by format, not by code. |
| What is the minimum buffer size? | Linux 3.18 isofs accepts logical-zone sizes of `512`, `1024`, or `2048`, and `sb_bread` reads `sb->s_blocksize`. | Block buffer ≥ 512 bytes. |
| Can `parent_offset` exceed the buffer? | No: 255 < 512 ≤ block_size. | The alleged OOB read cannot occur. |
| Is a trigger demonstrated? | No; the proof-requirements trigger family is disproved by the format/contract bound. | Predicate refuted. |

## Why the model results were misleading

The GEPA predicate noticed the absence of an explicit `length`-versus-block-size check and inferred an out-of-bounds read, but it omitted two decisive facts: the ISO 9660 directory-record `length` field is a single byte (so `parent_offset` is capped at 255), and the Linux isofs block size in this path is at least 512 bytes. The replicated model outcomes are therefore not used as adjudication evidence.

This is **RFC Axis E: predicate invalidity**. The code has no explicit bounds check because the format itself caps `parent_offset` below the smallest possible block size, and the proposed bad read is blocked by that existing contract.

## Provenance check

The source was resolved against the Linux 3.18 release tree (downloaded as `linux-3.18.tar.xz`, extracted to `/private/tmp/kernel-audit/linux-3.18`):

- `fs/isofs/isofs.h:72`: `static inline int isonum_711(char *p) { return *(u8 *)p; }` — confirms the single-byte (0–255) bound.
- `fs/isofs/inode.c:463`: logical block size validated as one of `512`, `1024`, or `2048` — confirms the minimum 512-byte block buffer.
- `fs/isofs/export.c`: the supplied benchmark source matches Linux 3.18 for the audited `isofs_export_get_parent` function after whitespace normalization. Two unrelated later checks in the supplied file differ from 3.18, so this is function-level, not whole-file, provenance.

The CVEFixes corpus row behind this seed carries only `code`, `language`, and `safety` fields; it has no version/commit metadata, consistent with the seed-42 provenance finding. The CSV label is `safe`, but the version-matched source and ISO 9660 contract — not the label — settle the result.

This result is limited to the exact seed-68 claim of an out-of-bounds kernel memory read from a large `length` field in `isofs_export_get_parent`. It checks only the fixed fields that `isofs_normalize_block_and_offset` reads on this path; it does not prove all isofs parsing safe and does not depend on the CVEFixes `safe` label.
