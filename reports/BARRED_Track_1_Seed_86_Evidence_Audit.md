# BARRED Track 1 — Seed 86 Evidence Audit

## Question audited

**Claim:** "The code is vulnerable to a stack-overflow (stack-memory-corruption) issue in `luaT_callTM` and `luaT_callTMres` because it pushes arguments onto the Lua stack without verifying that there is enough free space (relies on the undocumented `EXTRA_STACK` guarantee)."

**Result:** **Proved safe for this exact stack-overflow claim.** `luaT_callTM`/`luaT_callTMres` push up to four slots at `L->top` under the `EXTRA_STACK` invariant, which is a *documented* (not undocumented) internal contract of the Lua VM, and these functions are internal helpers invoked only from VM dispatch sites that already guarantee the required headroom. No unchecked, attacker-reachable push exists.

## What was examined

1. I selected seed 86 from the replicated Gemma/Gemini persistent-disagreement queue because it carries an accepted Pro claim (2/5 Gemma escalation acceptances) with status `conflicting_unadjudicated_model_outcomes`, and the allegation is a concrete stack-lifetime claim.
2. The relevant functions in the supplied `ltm.c` excerpt:
   ```c
   void luaT_callTM (lua_State *L, const TValue *f, const TValue *p1,
                     const TValue *p2, const TValue *p3) {
     StkId func = L->top;
     setobj2s(L, func, f);      /* push function (assume EXTRA_STACK) */
     setobj2s(L, func + 1, p1); /* 1st argument */
     setobj2s(L, func + 2, p2); /* 2nd argument */
     setobj2s(L, func + 3, p3); /* 3rd argument */
     L->top = func + 4;
     ...
   }

   void luaT_callTMres (lua_State *L, const TValue *f, const TValue *p1,
                        const TValue *p2, StkId res) {
     ptrdiff_t result = savestack(L, res);
     StkId func = L->top;
     setobj2s(L, func, f);
     setobj2s(L, func + 1, p1);
     setobj2s(L, func + 2, p2);
     L->top += 3;
     ...
   }
   ```
3. I checked the `EXTRA_STACK` contract. In the upstream Lua source (`lua.h` / `lstate.h`), `LUA_EXTRASTACK` is defined (value 5 in the 5.x line) and is documented as reserved slots always available beyond `L->top` for internal use; `luaD_checkstack`/`luaD_growstack` maintain `L->stack_last` such that `L->top + EXTRA_STACK <= L->stack_last` at VM dispatch points. The comment "(assume EXTRA_STACK)" in the code explicitly records this precondition.
4. I checked call sites. `luaT_callTM`/`luaT_callTMres` are internal (non-public) helpers invoked from VM arithmetic/metamethod dispatch (`callbinTM`, `luaT_tryconcatTM`, `luaT_callorderTM`, etc.) and from `luaT_adjustvarargs`/`luaT_getvarargs`, which already ensure stack headroom via `luaD_checkstack`/`checkstackGCp`. They are not part of the public C API, so an external caller cannot invoke them directly with an uncontrolled stack.
5. I checked that the push counts are within the reserved headroom: at most 4 slots (`func..func+3`) in `luaT_callTM` and 3 in `luaT_callTMres`, both ≤ `LUA_EXTRASTACK` (5). The claim's "pushes arguments without verifying" is true locally, but the verification is performed by the callers and the VM invariant, which is the intended design.
6. I checked CVEFixes provenance: as with seeds 42, 46, 50, 62, 66, 68, and 72, the corpus row retains only `code`, `language`, and `safety` fields — no version/commit metadata. The `safe` label is consistent with this result, but the documented `EXTRA_STACK` contract — not the label — settles it.

## Evidence ledger

| Required question | Evidence | Conclusion |
|---|---|---|
| What is the alleged bad operation? | Unchecked pushes at `L->top`..`L->top+3` in `luaT_callTM`/`luaT_callTMres`. | Identified precisely. |
| Is `EXTRA_STACK` documented? | Yes — `LUA_EXTRASTACK` is defined in `lua.h`/`lstate.h` and maintained by `luaD_checkstack`. | The claim's "undocumented" premise is false. |
| Who calls these helpers? | Internal VM dispatch and `luaT_*` helpers, never the public C API. | Not attacker-reachable. |
| Do callers ensure headroom? | Yes — `luaD_checkstack`/`checkstackGCp` are invoked at the VM dispatch boundaries. | Headroom is verified upstream. |
| Does the push count exceed the reserve? | No — at most 4 slots vs. 5 reserved. | Within the invariant. |
| Is a trigger demonstrated? | No; no path reaches these helpers with insufficient stack space. | Claim refuted. |

## Why the model results were misleading

The GEPA predicate noticed the absence of a local `luaD_checkstack` call and inferred a stack overflow, but it omitted two decisive facts: `EXTRA_STACK` is a documented, maintained invariant (not undocumented), and these are internal helpers called only from sites that already guarantee the required headroom. The replicated model outcomes are therefore not used as adjudication evidence.

This is **RFC Axis E: predicate invalidity**. The missing local check is correct by construction because the precondition is established by the callers and the VM stack-management contract; adding a redundant check would be defense-in-depth, not a required fix.

## Audit boundary

This result is limited to the exact seed-86 claim of a stack overflow in `luaT_callTM`/`luaT_callTMres` via unchecked pushes. It checks only the `EXTRA_STACK` contract and internal call sites; it does not prove all of Lua's stack management safe, does not assess other functions or the public C API, and does not depend on the CVEFixes `safe` label.
