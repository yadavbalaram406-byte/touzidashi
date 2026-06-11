from fastapi import APIRouter

from app.config import get_settings
from app.schemas.evaluation import ConfigResponse, TestLLMResponse
from app.services.llm import LLMClient

router = APIRouter(prefix="/config", tags=["config"])
settings = get_settings()


@router.get("", response_model=ConfigResponse)
async def get_config():
    llm = LLMClient()
    has_key = bool(llm.api_key and llm.api_key != "sk-ant-your-key-here" and not llm.api_key.startswith("your-"))
    return ConfigResponse(
        llm_provider=llm.provider,
        llm_model=llm.model,
        has_api_key=has_key,
    )


@router.post("/test-llm", response_model=TestLLMResponse)
async def test_llm():
    llm = LLMClient()
    success, message, actual_model = await llm.test_connection()
    return TestLLMResponse(
        success=success,
        message=message,
        provider=llm.provider if success else None,
        model=actual_model if success else None,
    )
