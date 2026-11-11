from typing import Any


class StrictSchemaInspector:
    """Encontra construções que o json_schema strict da OpenAI recusa."""

    @classmethod
    def refs_with_siblings(cls, node: Any, path: str = "$") -> list[str]:
        if isinstance(node, list):
            return [
                found
                for index, child in enumerate(node)
                for found in cls.refs_with_siblings(child, f"{path}[{index}]")
            ]
        if not isinstance(node, dict):
            return []
        found = [path] if "$ref" in node and len(node) > 1 else []
        for key, child in node.items():
            found.extend(cls.refs_with_siblings(child, f"{path}.{key}"))
        return found
