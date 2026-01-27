from itertools import cycle
from typing import Any, Dict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from sahiloan_chatbot import settings


class LLMFactory:
    DEFAULT_TEMPERATURE = 0.0
    DEFAULT_TIMEOUT = 5
    DEFAULT_MAX_RETRIES = 1

    def __init__(self):
        self._init_openai()
        self._init_gemini()
        self._init_groq()
        self._init_rotations()

    # -------------------------
    # Builders
    # -------------------------
    def _build_groq(
        self,
        model: str,
        api_key: str,
        max_tokens: int | None = None,
        reasoning_format: str | None = None,
    ) -> ChatGroq:
        return ChatGroq(
            model=model,
            api_key=api_key,
            temperature=self.DEFAULT_TEMPERATURE,
            max_tokens=max_tokens,
            timeout=self.DEFAULT_TIMEOUT,
            max_retries=self.DEFAULT_MAX_RETRIES,
            reasoning_format=reasoning_format,
        )

    def _build_gemini(self, model: str, api_key: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=model,
            api_key=api_key,
            temperature=self.DEFAULT_TEMPERATURE,
            timeout=15,
            max_retries=3,
        )

    # -------------------------
    # Init Groups
    # -------------------------
    def _init_openai(self):
        self.gpt_4o_mini = ChatOpenAI(
            model=settings.GPT_4O_MINI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=self.DEFAULT_TEMPERATURE,
        )

    def _init_gemini(self):
        self.gemini_2_5_flash_lite = self._build_gemini(settings.GEMINI_2_5_FLASH_LITE_MODEL, settings.GEMINI_API_KEY1)

        self.gemini_2_5_flash = self._build_gemini(settings.GEMINI_2_5_FLASH_MODEL, settings.GEMINI_API_KEY1)

    def _init_groq(self):
        self.llama_3_3_70b = self._build_groq(
            settings.LLAMA_3_3_70B_MODEL,
            settings.GROQ_API_KEY1,
        )

        self.llama_3_1_8b = self._build_groq(
            settings.LLAMA_3_1_8B_MODEL,
            settings.GROQ_API_KEY1,
            max_tokens=500,
        )

        self.qwen_3_32b = self._build_groq(
            settings.QWEN_3_32B_MODEL,
            settings.GROQ_API_KEY1,
            reasoning_format="parsed",
        )

    def _init_rotations(self):
        # Llama 3.1 8b
        self.llama_8b_50_cycle = self._create_groq_rotation(settings.LLAMA_3_1_8B_MODEL, 50)
        self.llama_8b_200_cycle = self._create_groq_rotation(settings.LLAMA_3_1_8B_MODEL, 200)
        self.llama_70b_cycle = self._create_groq_rotation(settings.LLAMA_3_3_70B_MODEL, 500)

        # Gemini 2.5 Models
        self.gemini_2_5_flash_cycle = self._create_gemini_rotation(settings.GEMINI_2_5_FLASH_MODEL)
        self.gemini_2_5_flash_lite_cycle = self._create_gemini_rotation(settings.GEMINI_2_5_FLASH_LITE_MODEL)

    # -------------------------
    # Rotation Helper
    # -------------------------
    def _create_groq_rotation(self, model_name: str, max_tokens: int | None = None):
        llms = [
            self._build_groq(model_name, settings.GROQ_API_KEY1, max_tokens),
            self._build_groq(model_name, settings.GROQ_API_KEY2, max_tokens),
            self._build_groq(model_name, settings.GROQ_API_KEY3, max_tokens),
        ]
        return cycle(llms)

    def _create_gemini_rotation(self, model_name: str):
        llms = [
            self._build_gemini(model_name, settings.GEMINI_API_KEY1),
            self._build_gemini(model_name, settings.GEMINI_API_KEY2),
            self._build_gemini(model_name, settings.GEMINI_API_KEY3),
        ]
        return cycle(llms)

    # -------------------------
    # Unified Getter
    # -------------------------
    def _response(self, llm: Any, model_name: str, max_tokens: int | None = None) -> Dict[str, Any]:
        return {"llm": llm, "model_name": model_name, "max_tokens": max_tokens}

    # -------------------------
    # Public APIs
    # -------------------------
    def get_llama_8b_50(self) -> Dict[str, Any]:
        return self._response(next(self.llama_8b_50_cycle), settings.LLAMA_3_1_8B_MODEL, max_tokens=50)

    def get_llama_70b_500(self) -> Dict[str, Any]:
        return self._response(next(self.llama_70b_cycle), settings.LLAMA_3_3_70B_MODEL, max_tokens=500)

    def get_gemini_flash(self) -> Dict[str, Any]:
        return self._response(next(self.gemini_2_5_flash_cycle), settings.GEMINI_2_5_FLASH_MODEL)

    def get_gemini_flash_lite(self) -> Dict[str, Any]:
        return self._response(next(self.gemini_2_5_flash_lite_cycle), settings.GEMINI_2_5_FLASH_LITE_MODEL)

    def get_llama_8b(self) -> Dict[str, Any]:
        return self._response(self.llama_3_1_8b, settings.LLAMA_3_1_8B_MODEL)

    def get_llama_70b(self) -> Dict[str, Any]:
        return self._response(self.llama_3_3_70b, settings.LLAMA_3_3_70B_MODEL)

    def get_qwen_32b(self) -> Dict[str, Any]:
        return self._response(self.qwen_3_32b, settings.QWEN_3_32B_MODEL)

    def get_gpt_4o_mini(self) -> Dict[str, Any]:
        return self._response(self.gpt_4o_mini, settings.GPT_4O_MINI_MODEL)
