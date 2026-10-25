# BARRED Track 1 — Rapid Triage Summary (22 remaining seeds)

Lightweight classification of the 22 seeds not in the persistent-split or pro-claim queues. 
Each is classified as `triage_likely_valid`, `triage_likely_invalid`, `triage_context_deficient`, or `triage_ambiguous` based on a quick source/contract check. 
These are **not** full independent adjudications — they are triage labels to complete the ledger. A seed can be promoted to a full `BARRED_Track_1_Seed_XX_Evidence_Audit.md` on demand.

| Seed | Triage status | Rationale |
|---:|---|---|
| 43 | triage_context_deficient | gf128mul_4k_lle callee not in seed (ghash.c); guard on ctx->gf128 unverified |
| 45 | triage_context_deficient | inc_ucount/dec_ucount in user_namespace.c, not in this sysctl seed |
| 48 | triage_likely_invalid | llc2_timeout_table mode 0644 = root-writable only; not privilege escalation |
| 53 | triage_context_deficient | no division by mss in this file; division is in skb_segment callee |
| 54 | triage_context_deficient | BUG() present in default case but state reachability via netlink unproven |
| 58 | triage_ambiguous | negated claim ('NOT vulnerable'); deep audit needed to verify frag6_print |
| 59 | triage_likely_invalid | loop bound 'MLX4_MAX_MAC_NUM - 1' skips a slot (not OOB); total==max guard present |
| 63 | triage_likely_valid | unbounded loop on attacker-controlled ip6r_len in tcpdump (DoS) |
| 64 | triage_likely_invalid | bounds checks present (size<=0, cch>maxsize-offset, bloc>=maxoffset) |
| 65 | triage_likely_valid | rcu_read_unlock before use of skb->dev (UAF) |
| 67 | triage_context_deficient | tcpdump OOB on address-mode; bounds unclear without deep read |
| 74 | triage_context_deficient | mr dereferenced without NULL check but reachability (can mr be NULL?) unproven |
| 76 | triage_likely_valid | strlen on ASN1_STRING_data can OOB if not NUL-terminated (known pattern) |
| 77 | triage_context_deficient | uninitialized pointer claim; needs deep code read |
| 81 | triage_likely_valid | write_urbs_free checked on port but set on wport (different struct) |
| 82 | triage_context_deficient | UAF race in ipv6_defrag; locking/timing unclear |
| 83 | triage_likely_invalid | bounds check present: (seg>>3) >= context.size |
| 84 | triage_ambiguous | negated claim ('NOT vulnerable'); deep audit needed |
| 87 | triage_likely_valid | NEED_IP(2) missing in t>=32, t!=2 path before get_unaligned_le16 |
| 88 | triage_likely_valid | negated claim correct: crypto_mod_put before return |
| 89 | triage_context_deficient | failover_timer management; reset path unclear |
| 91 | triage_context_deficient | service-principal spoofing; caller/auth flow unclear |

## Counts
- triage_ambiguous: 2
- triage_context_deficient: 10
- triage_likely_invalid: 4
- triage_likely_valid: 6
- Total triaged: 22
