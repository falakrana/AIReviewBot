import tree_sitter_python
from tree_sitter import Language, Parser

# In 0.22+, language() returns the Language object
lang = Language(tree_sitter_python.language())
print(f"Language object: {lang}")

parser = Parser(lang)
print("Parser created with language!")

query_text = """
(function_definition name: (identifier) @func.name) @func.def
"""

print("Attempting to create query...")
# In 0.22+, query is created from the language object OR the query class
query = lang.query(query_text)
print("Query created successfully!")
