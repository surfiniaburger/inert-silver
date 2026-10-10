import logging
import re
from typing import Optional, List, Set

logger = logging.getLogger(__name__)

try:
    import tree_sitter
    import tree_sitter_c
    C_LANGUAGE = tree_sitter.Language(tree_sitter_c.language())
    _PARSER = tree_sitter.Parser(C_LANGUAGE)
except Exception as e:
    tree_sitter = None
    tree_sitter_c = None
    C_LANGUAGE = None
    _PARSER = None
    logger.warning("Tree-sitter C grammar unavailable for judge slicing: %s", e)


def _find_declarator_identifier(node: "tree_sitter.Node") -> Optional[str]:
    """Walk declarator subtree to find the identifier."""
    cursor = node.walk()
    if not cursor.goto_first_child():
        return None
    while True:
        if cursor.node.type == "identifier":
            return cursor.node.text.decode("utf8", errors="ignore")
        if not cursor.goto_next_sibling():
            break
    return None


def extract_function_name(node: "tree_sitter.Node") -> Optional[str]:
    """Extract identifier name from a function_definition node."""
    for child in node.children:
        if child.type == "function_declarator":
            for sub in child.children:
                if sub.type == "identifier":
                    return sub.text.decode("utf8", errors="ignore")
        elif "declarator" in child.type:
            ident = _find_declarator_identifier(child)
            if ident:
                return ident
    return None


def _find_all_functions(root_node: "tree_sitter.Node") -> List["tree_sitter.Node"]:
    """Traverse AST to collect all function_definition nodes."""
    functions: List["tree_sitter.Node"] = []
    nodes_to_visit = [root_node]
    while nodes_to_visit:
        curr = nodes_to_visit.pop()
        if curr.type == "function_definition":
            functions.append(curr)
        nodes_to_visit.extend(curr.children)
    return functions


def _is_function_relevant(
    fn: "tree_sitter.Node",
    code_bytes: bytes,
    context_text: str,
    sample_anchors: List[str],
    pred_words: Set[str],
) -> bool:
    """Determine if a function definition is relevant to the debate."""
    fn_name = extract_function_name(fn)
    if fn_name and re.search(r"\b" + re.escape(fn_name) + r"\b", context_text):
        return True

    fn_text = code_bytes[fn.start_byte:fn.end_byte].decode("utf8", errors="ignore")
    if any(anchor in fn_text for anchor in sample_anchors if len(anchor) > 3):
        return True

    fn_words = set(re.findall(r"[a-zA-Z_]\w{3,}", fn_text))
    return len(pred_words.intersection(fn_words)) >= 3


def _deduplicate_and_sort_nodes(matched_nodes: List["tree_sitter.Node"]) -> List["tree_sitter.Node"]:
    """Sort nodes by byte offset and discard nested duplicates."""
    matched_nodes.sort(key=lambda n: n.start_byte)
    unique: List["tree_sitter.Node"] = []
    for n in matched_nodes:
        if not any(n.start_byte >= u.start_byte and n.end_byte <= u.end_byte for u in unique):
            unique.append(n)
    return unique


def _build_slice_output(
    unique_nodes: List["tree_sitter.Node"],
    code_bytes: bytes,
    original_code: str,
    min_reduction_ratio: float,
) -> str:
    """Format slices into code text or fall back to original."""
    slices = [code_bytes[n.start_byte:n.end_byte].decode("utf8") for n in unique_nodes]
    sliced_code = "\n\n/* ... [AST Program Slice: Preserved Function Scope] ... */\n\n".join(slices)
    if len(sliced_code) < len(original_code) * min_reduction_ratio and len(sliced_code) >= 100:
        return sliced_code
    return original_code


def slice_code_for_judge(
    code: str,
    predicate: str,
    transcript: str = "",
    sample_data: Optional[dict] = None,
    min_reduction_ratio: float = 0.95,
) -> str:
    """
    Slices C code to retain only functions relevant to the predicate, anchors,
    and debate transcript using Tree-sitter AST parsing.
    
    Guarantees:
    1. Verbatim byte slices (no pretty-printing or mutation).
    2. Full enclosing function scope preserved.
    3. Safe fallback to original code on parsing error or empty match.
    """
    if not code or _PARSER is None or C_LANGUAGE is None:
        return code

    try:
        code_bytes = code.encode("utf8")
        tree = _PARSER.parse(code_bytes)
        functions = _find_all_functions(tree.root_node)

        if len(functions) <= 1:
            return code

        context_text = f"{predicate} {transcript}"
        sample_anchors = (sample_data or {}).get("anchors", [])
        pred_words = set(re.findall(r"[a-zA-Z_]\w{3,}", context_text))

        matched = [
            fn for fn in functions
            if _is_function_relevant(fn, code_bytes, context_text, sample_anchors, pred_words)
        ]
        if not matched:
            return code

        unique_nodes = _deduplicate_and_sort_nodes(matched)
        return _build_slice_output(unique_nodes, code_bytes, code, min_reduction_ratio)
    except Exception as exc:
        logger.warning("AST program slicing failed, falling back to raw code: %s", exc)
        return code
