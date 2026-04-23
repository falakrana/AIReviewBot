from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python

lang = Language(tree_sitter_python.language())
parser = Parser(lang)

code = b"""
def hello():
    pass

class Foo:
    def bar(self):
        pass
"""

tree = parser.parse(code)
root = tree.root_node

query = Query(lang, """
    (function_definition name: (identifier) @func.name) @func.def
    (class_definition name: (identifier) @class.name) @class.def
""")

cursor = QueryCursor(query)

print("=== captures ===")
captures = cursor.captures(root)
print(f"Type: {type(captures)}")
print(f"Value: {captures}")

print("\n=== matches ===")
cursor2 = QueryCursor(query)
matches = cursor2.matches(root)
print(f"Type: {type(matches)}")
print(f"Value: {matches}")
