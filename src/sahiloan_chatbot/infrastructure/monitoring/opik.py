from sahiloan_chatbot import settings, logger
from functools import lru_cache
from opik import Opik
import opik

COMET_API_KEY = settings.COMET_API_KEY.get_secret_value()

@lru_cache(maxsize=1)
def configure_opik_tracing() -> None:
    if COMET_API_KEY and settings.COMET_PROJECT:
        try:
            opik.configure(api_key=COMET_API_KEY, workspace=settings.COMET_WORKSPACE, use_local=False, force=True)
            Opik(project_name=settings.COMET_PROJECT, api_key=COMET_API_KEY)
            logger.info("Opik configured successfully")
        except Exception as e:
            logger.warning(f"Failed to configure Opik: {e}")
    else:
        logger.warning("COMET_API_KEY and COMET_PROJECT not set. Opik monitoring disabled")