# BARRED Track 1 — Seed 78 Evidence Audit

## Question audited

**Claim:** “The code is vulnerable to a stack-based buffer overflow in the function `open_input_file` due to unchecked use of `strcat` on the fixed-size `cwd` buffer.”

**Result:** **Confirmed vulnerable for this exact claim.** Unlike seeds 42, 50, and 68, the supplied source does contain the unchecked operation the predicate describes; the benchmark `safe` label is wrong for this predicate.

## What was examined

1. I selected seed 78 because the allegation is precise and mechanically checkable: `strcat` into a fixed 1024-byte stack buffer.
2. The relevant function:
   ```c
   int open_input_file(const char *fname) {
       char cwd[1024];
       if (getcwd(cwd, sizeof(cwd)) != NULL) {
           strcat(cwd, "/../../tests/inputs/");   // no bounds check
       } else { ... }
       if ((fname==NULL) || ((strlen(cwd)+strlen(fname)) > sizeof(cwd))) {
           ... return -1;   // guard runs AFTER the suffix strcat
       }
       strcat(cwd, fname);
       ...
   }
   ```
3. `getcwd(cwd, 1024)` writes at most 1023 chars + NUL, so `cwd` can hold a path up to 1023 characters. The subsequent `strcat(cwd, "/../../tests/inputs/")` appends 21 bytes with no capacity check. If the working directory path is longer than 1002 characters, the suffix write overflows `cwd` on the stack before the guard ever runs.
4. The guard `strlen(cwd) + strlen(fname) > sizeof(cwd)` is evaluated only after the first `strcat` has already executed, so it cannot prevent the overflow; it also does not account for the 21-byte suffix that was already appended.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | `strcat(cwd, "/../../tests/inputs/")` into `char cwd[1024]`. | Identified precisely. |
| Is the operation unchecked? | Yes; no capacity test precedes it. | Unchecked. |
| Can the buffer be exceeded? | Yes, when `getcwd` returns a path longer than 1002 chars. | Reachable. |
| Does the existing guard prevent it? | No; it runs after the overflow and checks `cwd+fname`, not `cwd+suffix`. | Guard ineffective. |
| Is a trigger demonstrated? | Reachability shown by path-length argument; no runtime trace required. | Claim substantiated. |

## Audit boundary

This result is limited to the exact seed-78 claim of a stack buffer overflow via unchecked `strcat` in `open_input_file`. It does not assess other functions in the file, does not depend on the CVEFixes `safe` label (which is wrong here), and does not constitute a full vulnerability report for the project.