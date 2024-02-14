# llm-knowledge-graph
Example how to construct knowledge graph from a document with LLM and use it with Langchain as part of your RAG

3 Notebooks:

1. [Construct knowledge graph with LLM](./knowledgegraph.ipynb)
2. [Use Graph with Neo4j](./knowledgegraph-neo4j.ipynb)
3. [Use Graph with Azure CosmosDB](./knowledgegraph-cosmosdb.ipynb)


# Instructions

You need to copy `.env.example` file to `.env` and fill the variables with your own values.

After that, run notebook 1 to create the knowledge graph (stored in file) and then run notebook 2 or 3 to use it with either Neo4j or CosmosDB.

## Neo4j

If you run the neo4j database with docker compose, edit the `docker-compose.yml` file for a volume mount before starting it.

