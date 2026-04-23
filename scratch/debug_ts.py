import tree_sitter_python
from tree_sitter import Language, Parser

lang_ptr = tree_sitter_python.language()
lang = Language(lang_ptr, "python")

query_text = """
(function_definition name: (identifier) @func.name) @func.def
"""

print("Attempting to create query via lang.query()...")
try:
    q = lang.query(query_text)
    print("Query created successfully!")
except Exception as e:
    print(f"Failed to create query: {e}")

print("\nTesting Parser...")
parser = Parser()
parser.set_language(lang)
print("Parser language set!")
