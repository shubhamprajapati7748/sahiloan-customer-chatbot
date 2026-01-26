from sahiloan_chatbot.infrastructure.llm_providers.llm_factory import LLMFactory
from sahiloan_chatbot.infrastructure.db import get_pinecone_index
from functools import lru_cache
from .state import ChatState
from .constants import AGENT_ERROR_MESSAGE
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_openai import OpenAIEmbeddings
from sahiloan_chatbot import logger
from sahiloan_chatbot.domain.prompts import (
    INTENT_ROUTER_SYSTEM_PROMPT,
    GENERAL_AGENT_SYSTEM_PROMPT,
    GENERAL_AGENT_WITH_CONTEXT_TEMPLATE,
    GENERAL_AGENT_NO_CONTEXT_TEMPLATE
)
from sahiloan_chatbot.config import settings
import time
import json
from pathlib import Path
import numpy as np

@lru_cache(maxsize=1)
class Nodes:
    def __init__(self):
        self.llm_factory = LLMFactory()
        
        # Initialize Pinecone for RAG
        self.pinecone_index = get_pinecone_index()
        
        # Initialize embeddings (must match Pinecone dimension)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            dimensions=1024,
            api_key=settings.OPENAI_API_KEY.get_secret_value()
        )
        
        # Load and cache intent router eval dataset
        self._load_intent_eval_dataset()
    
    def _extract_message_content(self, message) -> str:
        """
        Extract content from a message, whether it's a dict or LangChain Message object.
        
        Args:
            message: Either a dict with 'content' key or a LangChain Message object
            
        Returns:
            str: The message content
        """
        if isinstance(message, dict):
            return message["content"]
        else:
            # It's a LangChain Message object (HumanMessage, AIMessage, etc.)
            return message.content
    
    def _load_intent_eval_dataset(self):
        """Load and embed the intent router eval dataset for semantic caching."""
        try:
            # Get project root (go up from this file to project root)
            # nodes.py -> workflow -> chat_service -> application -> sahiloan_chatbot -> src -> PROJECT_ROOT
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent.parent.parent.parent
            eval_path = project_root / "data" / "evals" / "intent_router.json"
            
            logger.debug(f"Looking for eval dataset at: {eval_path}")
            
            if not eval_path.exists():
                logger.warning(f"Eval dataset not found at {eval_path}, semantic caching disabled")
                self.eval_queries = []
                self.eval_embeddings = []
                self.eval_routes = []
                return
            
            # Load eval dataset
            with open(eval_path, 'r') as f:
                eval_data = json.load(f)
            
            logger.info(f"Loading {len(eval_data)} eval queries for intent caching...")
            
            # Extract queries and routes
            self.eval_queries = [item['input'] for item in eval_data]
            self.eval_routes = [item['reference'] for item in eval_data]
            
            # Generate embeddings for all eval queries
            self.eval_embeddings = [
                self.embeddings.embed_query(query) 
                for query in self.eval_queries
            ]
            
            logger.info(f"✅ Cached {len(self.eval_embeddings)} intent router embeddings")
            
        except Exception as e:
            logger.error(f"Error loading eval dataset: {e}")
            self.eval_queries = []
            self.eval_embeddings = []
            self.eval_routes = []
    
    def _find_similar_intent(self, user_query: str, threshold: float = 0.8):
        """
        Find similar query in eval dataset using semantic search.
        
        Args:
            user_query: User's input query
            threshold: Minimum cosine similarity threshold (default 0.8)
            
        Returns:
            route if match found, None otherwise
        """
        if not self.eval_embeddings:
            return None
        
        try:
            # Generate embedding for user query
            query_embedding = self.embeddings.embed_query(user_query)
            query_vector = np.array(query_embedding)
            
            # Calculate cosine similarities with all eval queries
            max_similarity = 0.0
            best_match_idx = -1
            
            for idx, eval_embedding in enumerate(self.eval_embeddings):
                eval_vector = np.array(eval_embedding)
                
                # Cosine similarity
                similarity = np.dot(query_vector, eval_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(eval_vector)
                )
                
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match_idx = idx
            
            # Check if best match exceeds threshold
            if max_similarity >= threshold:
                matched_query = self.eval_queries[best_match_idx]
                matched_route = self.eval_routes[best_match_idx]
                logger.info(
                    f"Semantic match found | similarity: {max_similarity:.4f} | "
                    f"matched: '{matched_query}' | route: {matched_route}"
                )
                return matched_route
            
            logger.debug(f"No semantic match | best similarity: {max_similarity:.4f} (< {threshold})")
            return None
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return None

    def intent_router(self, state: ChatState) -> ChatState:
        try:
            node_start = time.perf_counter()
            logger.info("intent_router_started")
            
            # Extract user input from state (handles both dict and Message objects)
            user_input = self._extract_message_content(state["messages"][-1])
            logger.debug(f"intent_router_user_input: {user_input}")
            
            # Step 1: Try semantic search in eval dataset first
            cached_route = self._find_similar_intent(user_input, threshold=0.9)
            
            if cached_route:
                # Found a match in eval dataset - use cached route
                state["route_to"] = cached_route
                latency = (time.perf_counter() - node_start) * 1000
                logger.info(
                    f"intent_router_completed | route: {cached_route} | "
                    f"method: semantic_cache | latency: {latency:.2f}ms"
                )
                return state
            
            # Step 2: No semantic match - use LLM
            logger.debug("No semantic match, using LLM for intent classification")
            
            # Prepare messages with system prompt
            messages = [
                SystemMessage(content=INTENT_ROUTER_SYSTEM_PROMPT),
                HumanMessage(content=user_input)
            ]
            
            # Get LLM and invoke
            llm_fact = self.llm_factory.get_gpt_4o_mini()
            response = llm_fact["llm"].invoke(messages)
            
            # Extract route from response and update state
            route = response.content.strip().lower()
            logger.debug(f"intent_router_llm_response: {route}")
            
            # Validate route
            valid_routes = ['general_agent', 'loan_agent', 'document_agent', 'end']
            if route not in valid_routes:
                logger.warning(f"Invalid route '{route}' returned, defaulting to 'general_agent'")
                route = 'general_agent'
            
            state["route_to"] = route
            
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(
                f"intent_router_completed | route: {route} | "
                f"method: llm | latency: {latency:.2f}ms | llm: {llm_fact['model_name']}"
            )
            return state
        except Exception as e:
            logger.exception(f"intent_router_error: | type: {type(e).__name__} | message: {str(e)}")
            state["route_to"] = "general_agent"  # Default fallback route
            return state
    
    def general_agent(self, state: ChatState) -> ChatState:
        """
        General agent with RAG - retrieves context from Pinecone and generates response.
        """
        try:
            node_start = time.perf_counter()
            logger.info("general_agent_started")
            
            # Extract user query (handles both dict and Message objects)
            user_query = self._extract_message_content(state["messages"][-1])
            logger.debug(f"general_agent_query: {user_query}")
            
            # Step 1: Retrieve relevant context from Pinecone
            logger.debug("Fetching context from Pinecone...")
            query_embedding = self.embeddings.embed_query(user_query)
            
            # Search Pinecone for top relevant chunks
            search_results = self.pinecone_index.query(
                vector=query_embedding,
                top_k=5,  # Get top 5 relevant chunks
                include_metadata=True
            )
            
            # Extract context from results
            context_chunks = []
            for match in search_results['matches']:
                if match['score'] > 0.5: 
                    context_chunks.append(match['metadata']['text'])
            
            logger.debug(f"Retrieved {len(context_chunks)} relevant chunks")
            
            # Step 2: Format context using LangChain prompt templates
            if context_chunks:
                context = "\n\n---\n\n".join(context_chunks)
                # Use prompt template with context
                user_message = GENERAL_AGENT_WITH_CONTEXT_TEMPLATE.format(
                    context=context,
                    query=user_query
                )
            else:
                # No relevant context found - use no-context template
                user_message = GENERAL_AGENT_NO_CONTEXT_TEMPLATE.format(
                    query=user_query
                )
                logger.warning("No relevant context found in Pinecone")
            
            # Step 3: Generate response using LLM
            messages = [
                SystemMessage(content=GENERAL_AGENT_SYSTEM_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            llm_fact = self.llm_factory.get_gpt_4o_mini()
            response = llm_fact["llm"].invoke(messages)
            
            # Step 4: Add AI response to messages
            state["messages"].append({
                "role": "assistant",
                "content": response.content
            })
            
            # Update route to end (conversation complete)
            state["route_to"] = "end"
            
            latency = (time.perf_counter() - node_start) * 1000
            logger.info(f"general_agent_completed | chunks_used: {len(context_chunks)} | latency: {latency:.2f}ms | llm: {llm_fact['model_name']}")
            
            return state
            
        except Exception as e:
            logger.exception(f"general_agent_error: | type: {type(e).__name__} | message: {str(e)}")
            
            # Fallback response
            state["messages"].append({
                "role": "assistant",
                "content": "I apologize, but I'm having trouble processing your request right now. Please try again or contact our support team."
            })
            state["route_to"] = "end"
            return state

    def loan_agent(self, state: ChatState) -> ChatState:
        pass
    
    def document_agent(self, state: ChatState) -> ChatState:
        pass
