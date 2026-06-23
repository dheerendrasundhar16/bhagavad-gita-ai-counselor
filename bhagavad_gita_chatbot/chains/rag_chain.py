from typing import List, Dict, Any, Tuple
from langchain_classic.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.documents import Document

from services.gemini_service import gemini_service
from vectorstore.database import gita_db
from chains.prompts import rephrase_prompt, qa_prompt
from utils.logger import logger

class GitaRAGChain:
    def __init__(self, api_key: str = None):
        """Initializes the RAG chain components using the provided API key."""
        logger.info("Initializing GitaRAGChain components...")
        self.db = gita_db.init_db(api_key)
        self.llm = gemini_service.get_llm(model_name="gemini-2.5-flash", temperature=0.2)
        
        # Setup vectorstore retriever with MMR search
        # MMR (Maximum Marginal Relevance) ensures diverse verse retrieval —
        # avoiding repetitive verse recommendations across a long conversation.
        # fetch_k=12 gives a wide candidate pool; k=5 selects top diverse results.
        self.retriever = self.db.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "fetch_k": 12}
        )
        
        # History-aware retriever to rephrase queries in context
        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, rephrase_prompt
        )
        
        # Stuff documents chain to generate answers from context
        self.question_answer_chain = create_stuff_documents_chain(
            self.llm, qa_prompt
        )
        
        # End-to-end retrieval QA chain
        self.rag_chain = create_retrieval_chain(
            self.history_aware_retriever, self.question_answer_chain
        )
        logger.info("GitaRAGChain successfully initialized.")

    @staticmethod
    def parse_chat_history(history_dicts: List[Dict[str, str]]) -> List[BaseMessage]:
        """Converts raw list of dict history (e.g. from API/Streamlit) to LangChain messages."""
        messages = []
        for msg in history_dicts:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role in ["assistant", "ai", "bot"]:
                messages.append(AIMessage(content=content))
        return messages

    def get_response(self, question: str, history_dicts: List[Dict[str, str]]) -> Tuple[str, List[Document]]:
        """Invokes the retrieval chain to generate a structured answer.
        
        Args:
            question: The latest user question.
            history_dicts: Conversation history.
            
        Returns:
            Tuple[str, List[Document]]: (Structured answer string, list of retrieved source documents).
        """
        chat_history = self.parse_chat_history(history_dicts)
        logger.info(f"Invoking RAG chain for question: '{question}' with {len(chat_history)} history messages.")
        
        try:
            result = self.rag_chain.invoke({
                "input": question,
                "chat_history": chat_history
            })
            
            answer = result.get("answer", "")
            context_docs = result.get("context", [])
            
            logger.info("RAG chain successfully generated response.")
            return answer, context_docs
        except Exception as e:
            logger.error(f"Error in RAG chain invoke: {e}")
            raise e
