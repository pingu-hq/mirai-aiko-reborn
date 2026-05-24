from fastapi import  Request
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore






class CharacterVectorStore:
    def __init__(self, request: Request):
        self.request = request

    @property
    def index(self) -> VectorStoreIndex:
        return self.request.app.state.character_index

    @staticmethod
    def _memory_organizer(raw_memories: list[NodeWithScore]):
        cleansed_parts = []

        for i, mem in enumerate(raw_memories):
            score = f"{mem.score:.3f}"
            description = mem.metadata.get("description", "No description available.")
            dialogue = mem.metadata.get("dialogue", "")

            template = (
                f"<memory_node index='{i + 1}'>\n"
                f"  <confidence>{score}</confidence>\n"
                f"  <trait>{description}</trait>\n"
                f"  <behavioral_sample>{dialogue}</behavioral_sample>\n"
                f"</memory_node>"
            )
            cleansed_parts.append(template)

        final_context = "<retrieved_memories>\n" + "\n".join(cleansed_parts) + "\n</retrieved_memories>"
        return final_context

    async def search_memories_by_query(self, query: str):
        memories = self.index.as_retriever(similarity_top_k=5)
        raw_memories = await memories.aretrieve(query)
        cleaned_memories = self._memory_organizer(raw_memories=raw_memories)
        return cleaned_memories