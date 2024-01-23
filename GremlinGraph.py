# This is not part of LangChain at the moment, but I will contribute it there.
import sys
from typing import Any, Dict, List, Optional

from langchain_core.utils import get_from_env

from langchain_community.graphs.graph_document import GraphDocument
from langchain_community.graphs.graph_store import GraphStore

node_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output

"""

rel_properties_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
"""

rel_query = """
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type = "RELATIONSHIP" AND elementType = "node"
UNWIND other AS other_node
RETURN {start: label, type: property, end: toString(other_node)} AS output
"""


class GremlinGraph(GraphStore):
    """Gremlin wrapper for graph operations.

    *Security note*: Make sure that the database connection uses credentials
        that are narrowly-scoped to only include necessary permissions.
        Failure to do so may result in data corruption or loss, since the calling
        code may attempt commands that would result in deletion, mutation
        of data if appropriately prompted or reading sensitive data if such
        data is present in the database.
        The best way to guard against such negative outcomes is to (as appropriate)
        limit the permissions granted to the credentials used with this tool.

        See https://python.langchain.com/docs/security for more information.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = "/dbs/cosmicworks/colls/products",
        password: Optional[str] = None,
        traversal_source: str = "g",
        message_serializer: Optional[Any] = None,
    ) -> None:
        """Create a new Gremlin graph wrapper instance."""
        try:
            from gremlin_python.driver import client, serializer
            import asyncio
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except ImportError:
            raise ValueError(
                "Please install gremlin-python first: "
                "`pip3 install gremlinpython"
            )
        
        self.client = client.Client(
            url=get_from_env("url", "GREMLIN_URI", url),
            traversal_source=traversal_source,
            username=get_from_env("username", "GREMLIN_USERNAME", username),
            password=get_from_env("password", "GREMLIN_PASSWORD", password),
            message_serializer=message_serializer if message_serializer else serializer.GraphSONSerializersV2d0(),
        )

       
    @property
    def get_schema(self) -> str:
        """Returns the schema of the Graph"""
        return self.schema


    def query(self, query: str, params: dict = {}) -> List[Dict[str, Any]]:
        """Query Neo4j database."""
        from neo4j.exceptions import CypherSyntaxError

        with self._driver.session(database=self._database) as session:
            try:
                data = session.run(query, params)
                return [r.data() for r in data]
            except CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

    def refresh_schema(self) -> None:
        """
        Refreshes the Neo4j graph schema information.
        """
        node_properties = [el["output"] for el in self.query(node_properties_query)]
        rel_properties = [el["output"] for el in self.query(rel_properties_query)]
        relationships = [el["output"] for el in self.query(rel_query)]

        self.structured_schema = {
            "node_props": {el["labels"]: el["properties"] for el in node_properties},
            "rel_props": {el["type"]: el["properties"] for el in rel_properties},
            "relationships": relationships,
        }

        # Format node properties
        formatted_node_props = []
        for el in node_properties:
            props_str = ", ".join(
                [f"{prop['property']}: {prop['type']}" for prop in el["properties"]]
            )
            formatted_node_props.append(f"{el['labels']} {{{props_str}}}")

        # Format relationship properties
        formatted_rel_props = []
        for el in rel_properties:
            props_str = ", ".join(
                [f"{prop['property']}: {prop['type']}" for prop in el["properties"]]
            )
            formatted_rel_props.append(f"{el['type']} {{{props_str}}}")

        # Format relationships
        formatted_rels = [
            f"(:{el['start']})-[:{el['type']}]->(:{el['end']})" for el in relationships
        ]

        self.schema = "\n".join(
            [
                "Node properties are the following:",
                ",".join(formatted_node_props),
                "Relationship properties are the following:",
                ",".join(formatted_rel_props),
                "The relationships are the following:",
                ",".join(formatted_rels),
            ]
        )

    def add_graph_documents(self, graph_documents: List[GraphDocument], include_source: bool = False) -> None:
        """
        Take GraphDocument as input as uses it to construct a graph.
        """
        for document in graph_documents:
            # Import nodes
            for el in document.nodes:            
                node = self.g.V().hasLabel(el.type).has('id', el.id).tryNext().orElseGet(lambda: self.g.addV(el.type).property('id', el.id).next())
                for key, value in el.properties.items():
                    node.property(key, value)
                #if include_source:
                #    doc = self.g.V().hasLabel('Document').has('text', document.source.page_content).tryNext().orElseGet(lambda: self.g.addV('Document').property('text', document.source.page_content).next())
                #    for key, value in document.source.metadata.items():
                #        doc.property(key, value)
                #    doc.addEdge('MENTIONS', node)
            # Import relationships
            for el in document.relationships:
                source = self.g.V().hasLabel(el.source.type).has('id', el.source.id).tryNext().orElseGet(lambda: self.g.addV(el.source.type).property('id', el.source.id).next())
                target = self.g.V().hasLabel(el.target.type).has('id', el.target.id).tryNext().orElseGet(lambda: self.g.addV(el.target.type).property('id', el.target.id).next())
                edge = source.addEdge(el.type.replace(" ", "_").upper(), target)
                for key, value in el.properties.items():
                    edge.property(key, value)
