from langchain.graphs.graph_document import Node, Relationship
from typing import  Any, Dict



def format_property_key(s: str) -> str:
    words = s.split()
    if not words:
        return s
    first_word = words[0].lower()
    capitalized_words = [word.capitalize() for word in words[1:]]
    return "".join([first_word] + capitalized_words)

def props_to_dict(props) -> dict:
    """Convert properties to a dictionary."""
    properties = {}
    if not props:
      return properties
    for p in props:
        properties[format_property_key(p["key"])] = p["value"]
    return properties

def map_to_base_node(node: Any) -> Node:
    """Map the KnowledgeGraph Node to the base Node."""
    properties = props_to_dict(node["properties"]) if "properties" in node else {}
    # Add name property for better Cypher statement generation according to the langchain docs. Not sure if relevant for cosmos/gremlin.
    properties["name"] = node.id
    type = node.type.capitalize()
    nodex = Node(
        id=node.id, type=type, properties=properties
    )
    return nodex
    

def map_to_base_relationship(rels: [Any], nodes: [Node]) -> Relationship:
    """Map the KnowledgeGraph Relationship to the base Relationship."""
    mapped_rels = []
    for rel in rels:
        s = next((n for n in nodes if n.id == rel.source), None)
        source = s if s else map_to_base_node(rel.source)
        t = next((n for n in nodes if n.id == rel.target), None)
        target = t if t else map_to_base_node(rel.target)
        properties = props_to_dict(rel["properties"]) if "properties" in rel else {}
        mapped_rels.append(Relationship(
            source=source, target=target, type=rel.type, properties=properties
        ))
    return mapped_rels