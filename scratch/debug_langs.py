import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_java
import tree_sitter_c
import tree_sitter_cpp
from tree_sitter import Language

langs = {
    "python": tree_sitter_python.language(),
    "javascript": tree_sitter_javascript.language(),
    "typescript": tree_sitter_typescript.language_typescript(),
    "java": tree_sitter_java.language(),
    "c": tree_sitter_c.language(),
    "cpp": tree_sitter_cpp.language()
}

for name, lang in langs.items():
    print(f"{name}: {type(lang)}")
    try:
        # Try to wrap it
        l = Language(lang, name)
        print(f"  Successfully wrapped {name}")
    except Exception as e:
        print(f"  Failed to wrap {name}: {e}")
