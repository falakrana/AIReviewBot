import tree_sitter_typescript
from tree_sitter import Language, Parser

ts_lang_capsule = tree_sitter_typescript.language_typescript()
print(f"Capsule type: {type(ts_lang_capsule)}")

parser = Parser()
try:
    parser.set_language(ts_lang_capsule)
    print("Directly set capsule as language!")
except Exception as e:
    print(f"Failed to set capsule directly: {e}")

try:
    # Try wrapping it?
    # Language(ts_lang_capsule, "typescript") failed with "Expected a path or pointer"
    # What if we just call it?
    pass
except Exception as e:
    pass
