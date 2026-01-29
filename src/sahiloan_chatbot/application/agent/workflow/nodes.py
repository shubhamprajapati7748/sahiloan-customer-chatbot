import time
import os
from functools import lru_cache

from langchain.messages import AIMessage, ToolMessage
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sahiloan_chatbot import logger, settings
from sahiloan_chatbot.domain.prompts import (
    GENERAL_AGENT_SYSTEM_PROMPT,
    INTENT_ROUTER_SYSTEM_PROMPT,
    LOAN_AGENT_PROMPT,
    DOCUMENT_AGENT_SYSTEM_PROMPT,
)
from sahiloan_chatbot.domain.tools import get_user_loans_tool
from sahiloan_chatbot.infrastructure.db.pine_cone import get_pinecone_index
from sahiloan_chatbot.infrastructure.llm_providers import LLMFactory

from .constants import AGENT_ERROR_MESSAGE
from .schema import RouterSchema, DocumentSchema
from .state import ChatState


@lru_cache(maxsize=1)
class Nodes:
    def __init__(self):
        self.llm_factory = LLMFactory()
        self.pinecone_index = get_pinecone_index()
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
            api_key=settings.OPENAI_API_KEY.get_secret_value(),
        )

    def intent_router(self, state: ChatState) -> ChatState:
        node_start = time.perf_counter()
        logger.info("intent_router_started")
        try:
            user_message = state["messages"][-1].content
            logger.debug(f"user_message: {user_message}")

            system_msg = [
                {
                    "role": "system",
                    "content": INTENT_ROUTER_SYSTEM_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ]

            # Get LLM and invoke
            llm_fact = self.llm_factory.get_gpt_4o_mini()
            llm_structured = llm_fact["llm"].with_structured_output(RouterSchema)
            response = llm_structured.invoke(system_msg)
            logger.debug(f"llm used : {llm_fact['model_name']} | response: {response.model_dump_json()}")

            state["route_to"] = response.route_to
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"intent_router_completed | latency: {latency:.2f}ms")
            return state
        except Exception as e:
            logger.exception(f"intent_router_error: | type: {type(e).__name__} | message: {str(e)}")
            state["route_to"] = "general_agent"
            return state

    def general_agent(self, state: ChatState) -> ChatState:
        node_start = time.perf_counter()
        logger.info("general_agent_started")
        try:
            user_message = state["messages"][-1].content
            logger.debug(f"user_message: {user_message}")

            retrieved_context = self._retrieve_context(user_message)
            if retrieved_context:
                context = "\n\n---\n\n".join(retrieved_context)
                user_content = f"""Context from knowledge base: {context}\n\n
                User Query: {user_message}
                Please answer the user's question using the context provided above. Be helpful and concise."""
            else:
                user_content = f"User Query: {user_message} \n\n Note: No specific information was found in the knowledge base. Please provide a helpful general response."

            system_msg = [
                {
                    "role": "system",
                    "content": GENERAL_AGENT_SYSTEM_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ]

            llm_fact = self.llm_factory.get_gpt_4o_mini()
            response = llm_fact["llm"].invoke(system_msg)
            logger.debug(f"llm used : {llm_fact['model_name']} | response: {response}")
            state["messages"].append(AIMessage(content=response.content))
            state["route_to"] = "end"
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"general_agent_completed | latency: {latency:.2f}ms")
            return state
        except Exception as e:
            logger.exception(f"general_agent_error: | type: {type(e).__name__} | message: {str(e)}")
            return self._agent_end_state(state)

    def _retrieve_context(self, user_message: str):
        try:
            logger.debug("Fetching context from Pinecone...")
            query_embedding = self.embeddings.embed_query(user_message)

            # Search Pinecone for top relevant chunks
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=5,  # Get top 5 relevant chunks
                include_metadata=True,
            )

            context_chunks = []
            for match in search_results["matches"]:
                if match["score"] > 0.5:
                    context_chunks.append(match["metadata"]["text"])

            logger.debug(f"Retrieved {len(context_chunks)} relevant chunks")
            return context_chunks
        except Exception as e:
            logger.exception(f"retrieve_context_error: | type: {type(e).__name__} | message: {str(e)}")
            return []

    def _agent_end_state(self, state: ChatState, message: str = AGENT_ERROR_MESSAGE) -> ChatState:
        state["messages"].append(AIMessage(content=message))
        state["route_to"] = "end"
        return state

    def loan_agent(self, state: ChatState) -> ChatState:
        try:
            node_start = time.perf_counter()
            logger.info("loan_agent_started")
            logger.debug(f"current state: {state}")

            user_id = state["user"].user_id
            user_message = state["messages"][-1].content
            logger.debug(f"user_message: {user_message} | user_id: {user_id}")

            system_msg = [
                {
                    "role": "system",
                    "content": LOAN_AGENT_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": f"UserId: {user_id}\nUser Message: {user_message}",
                },
            ]

            llm_fact = self.llm_factory.get_gpt_4o_mini()
            llm_with_tools = llm_fact["llm"].bind_tools([get_user_loans_tool])
            response = llm_with_tools.invoke(system_msg)
            logger.debug(f"llm_response: {response}")

            state["messages"].append(response)
            state["route_to"] = "end"
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"loan_agent_completed | latency: {latency:.2f}ms | llm: {llm_fact['model_name']}")
            return state
        except Exception as e:
            logger.exception(f"loan_agent_error: | type: {type(e).__name__} | message: {str(e)}")
            return self._agent_end_state(state)

    def tool_node(self, state: ChatState) -> ChatState:
        logger.info("tool_node_started")
        node_start = time.perf_counter()
        tools_by_name = {tool.name: tool for tool in [get_user_loans_tool]}
        result = []

        # Get the last message (contains tool_calls from LLM)
        last_message = state["messages"][-1]

        # Execute each tool call
        for tool_call in last_message.tool_calls:
            tool = tools_by_name[tool_call["name"]]
            observation = tool.invoke(tool_call["args"])
            logger.debug(f"tool args: {tool_call['args']}")
            result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
            logger.debug(f"tool_result: {result}")

        state["messages"].extend(result)
        state["route_to"] = "loan_agent"
        latency = (time.perf_counter() - node_start) * 1000
        logger.info(f"tool_node_completed | latency: {latency:.2f}ms")
        return state

    def load_document(self, file_path: str):
        try:
            logger.debug("Document loading from {}", file_path)
            _, extension = os.path.splitext(file_path.lower())
            if extension == ".pdf":
                loader = PyPDFLoader(file_path)
            elif extension == ".docx" or extension == ".doc":
                loader = Docx2txtLoader(file_path)
            elif extension == ".txt":
                loader = TextLoader(file_path)
            else:
                logger.error("Unsupported document type: {}", extension)
                return []
            documents = loader.load()
            logger.debug("Document loaded successfully")
            return documents

        except Exception as e:
            logger.exception(f"load_document_error: | type: {type(e).__name__} | message: {str(e)}")
            return []
    def chunk_document(self, document,chunk_size:int, chunk_overlap:int):
        try:
            logger.debug("Chunking document")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_documents(document)
            return chunks
        except Exception as e:
            logger.error("Error occured while chunking document")
    def analyse_document(self,chunks,analysis_type:str):
        try:
            logger.debug("Analysing document")
            full_text = "\n\n".join([chunk.page_content for chunk in chunks[:10]])
            logger.debug(f"full_text: {full_text}")
            system_msg = [
                {
                    "role": "system",
                    "content": DOCUMENT_AGENT_SYSTEM_PROMPT.prompt,
                },
                {
                    "role": "user",
                    "content": f"Document: {full_text}",
                },
            ]
            logger.debug(f"system_msg: {system_msg}")
            
            llm_fact = self.llm_factory.get_gpt_4o_mini()
            response = llm_fact["llm"].invoke(system_msg)
            logger.debug(f"llm used : {llm_fact['model_name']} | response: {response.content}")
            return response.content
            
        except Exception as e:
            logger.error("Error occured while analysing document")
            return f"I apologize, but I encountered an error while analyzing the document: {str(e)}"

    def document_agent(self, state: ChatState) -> ChatState:
        logger.info("Document aganet started")
        node_start = time.perf_counter()
        document_temp_path=""
        if(state["document_analysis"].document_path): 
            document_temp_path = state["document_analysis"].document_path
        else:
            logger.error("No document path provided")
            return self._agent_end_state(state)
        documents = self.load_document(document_temp_path)
        chunks = self.chunk_document(documents, chunk_size=1000, chunk_overlap=300)
        analysis = self.analyse_document(chunks,analysis_type="summary")
        state["messages"].append(AIMessage(content=analysis))
        state["route_to"] = "end"
        state["document_analysis"] = DocumentSchema(document_path=document_temp_path, document_analysis=analysis)
        latency = (time.perf_counter() - node_start) * 1000
        logger.info(f"document_agent | latency: {latency:.2f}ms")
        return state
    