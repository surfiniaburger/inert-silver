import pytest
from scenarios.debate.judge_slicer import slice_code_for_judge, extract_function_name

C_SAMPLE = """
/* License Header */
#include <stdio.h>

int helper_func(int a) {
    return a * 2;
}

void vulnerable_target(char *buf, int len) {
    if (len > 10) {
        printf("Safe\\n");
    }
    buf[len] = '\\0';
}

int unrelated_func(int x) {
    int y = x + 1;
    return y;
}
"""

def test_slice_matches_predicate_function():
    pred = "The code is vulnerable to out-of-bounds write in vulnerable_target"
    sliced = slice_code_for_judge(C_SAMPLE, pred)
    assert "void vulnerable_target" in sliced
    assert "buf[len] = '\\0';" in sliced
    assert "helper_func" not in sliced
    assert "unrelated_func" not in sliced
    assert "/* License Header */" not in sliced

def test_slice_matches_transcript_function():
    pred = "The code has an issue"
    transcript = "Pro: Look at vulnerable_target where buf[len] is written.\nCon: But len is checked."
    sliced = slice_code_for_judge(C_SAMPLE, pred, transcript=transcript)
    assert "void vulnerable_target" in sliced
    assert "helper_func" not in sliced
    assert "unrelated_func" not in sliced

def test_slice_preserves_anchors():
    pred = "The code has an issue"
    sample_data = {"anchors": ["buf[len] = '\\0';", "len > 10"]}
    sliced = slice_code_for_judge(C_SAMPLE, pred, sample_data=sample_data)
    assert "void vulnerable_target" in sliced
    assert "buf[len] = '\\0';" in sliced

def test_slice_fallback_on_empty_match():
    pred = "Completely unrelated text without any matching identifiers"
    sliced = slice_code_for_judge(C_SAMPLE, pred)
    # Should fall back to full code
    assert sliced == C_SAMPLE

def test_slice_fallback_on_single_function():
    single_func = "int foo(int x) { return x + 1; }"
    sliced = slice_code_for_judge(single_func, "foo is bad")
    assert sliced == single_func
