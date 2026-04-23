from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
import tree_sitter_java
import tree_sitter_c
import tree_sitter_cpp
import os
import logging

logger = logging.getLogger(__name__)

class ParserService:
    def __init__(self):
        # Initialize languages using tree-sitter 0.22+ API
        self.languages = {
            ".py": {
                "lang": Language(tree_sitter_python.language()),
                "query": """
                    (function_definition name: (identifier) @func.name) @func.def
                    (class_definition name: (identifier) @class.name) @class.def
                """
            },
            ".js": {
                "lang": Language(tree_sitter_javascript.language()),
                "query": """
                    (function_declaration name: (identifier) @func.name) @func.def
                    (method_definition name: (property_identifier) @func.name) @func.def
                    (class_declaration name: (identifier) @class.name) @class.def
                    (variable_declarator name: (identifier) @func.name value: (arrow_function)) @func.def
                """
            },
            ".ts": {
                "lang": Language(tree_sitter_typescript.language_typescript()),
                "query": """
                    (function_declaration name: (identifier) @func.name) @func.def
                    (method_definition name: (property_identifier) @func.name) @func.def
                    (class_declaration name: (identifier) @class.name) @class.def
                """
            },
            ".java": {
                "lang": Language(tree_sitter_java.language()),
                "query": """
                    (method_declaration name: (identifier) @func.name) @func.def
                    (class_declaration name: (identifier) @class.name) @class.def
                """
            },
            ".c": {
                "lang": Language(tree_sitter_c.language()),
                "query": """
                    (function_definition declarator: (function_declarator declarator: (identifier) @func.name)) @func.def
                """
            },
            ".cpp": {
                "lang": Language(tree_sitter_cpp.language()),
                "query": """
                    (function_definition declarator: (function_declarator declarator: (identifier) @func.name)) @func.def
                    (class_specifier name: (type_identifier) @class.name) @class.def
                """
            }
        }
        
        # Mapping for secondary extensions
        self.extension_map = {
            ".tsx": ".ts",
            ".jsx": ".js",
            ".cc": ".cpp",
            ".hpp": ".cpp",
            ".h": ".c"
        }
        
        self.parser = Parser()

    def parse_file(self, file_path, relative_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {"file": relative_path, "functions": [], "classes": []}

        extension = os.path.splitext(file_path)[1].lower()
        
        # Use mapped extension if needed
        lang_ext = self.extension_map.get(extension, extension)
        
        if lang_ext not in self.languages:
            logger.warning(f"Unsupported file extension: {extension}")
            return {"file": relative_path, "functions": [], "classes": []}

        lang_config = self.languages[lang_ext]
        lang = lang_config["lang"]
        
        self.parser.language = lang
        
        tree = self.parser.parse(bytes(code, "utf8"))
        root_node = tree.root_node
        
        # Query execution moved to QueryCursor in newer tree-sitter releases.
        query = Query(lang, lang_config["query"])
        captures = QueryCursor(query).captures(root_node)
        
        features = {
            "file": relative_path,
            "functions": [],
            "classes": []
        }
        
        processed_nodes = set()

        for node, tag in self._iter_capture_pairs(captures):
            if node in processed_nodes:
                continue
                
            if tag == "func.def":
                name = self._get_name_from_captures(node, captures, "func.name")
                features["functions"].append({
                    "name": name,
                    "code": code[node.start_byte:node.end_byte],
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1
                })
                processed_nodes.add(node)
            elif tag == "class.def":
                name = self._get_name_from_captures(node, captures, "class.name")
                features["classes"].append({
                    "name": name,
                    "code": code[node.start_byte:node.end_byte],
                    "start_line": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1
                })
                processed_nodes.add(node)
                
        return features

    def _iter_capture_pairs(self, captures):
        if isinstance(captures, dict):
            for tag, nodes in captures.items():
                for node in nodes:
                    yield node, tag
            return

        for node, tag in captures:
            yield node, tag

    def _get_name_from_captures(self, parent_node, captures, tag_name):
        for node, tag in self._iter_capture_pairs(captures):
            if tag == tag_name and (node.parent == parent_node or (node.parent and node.parent.parent == parent_node)):
                return node.text.decode('utf8')
        return "anonymous"
