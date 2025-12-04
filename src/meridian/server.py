from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from .core import FeatureStore
import structlog

logger = structlog.get_logger()


class FeatureRequest(BaseModel):
    entity_name: str
    entity_id: str
    features: List[str]


def create_app(store: FeatureStore) -> FastAPI:
    app = FastAPI(title="Meridian Feature Store API")

    @app.post("/features")
    async def get_features(request: FeatureRequest) -> Dict[str, Any]:
        """
        Retrieves online features for a specific entity.
        """
        try:
            features = store.get_online_features(
                entity_name=request.entity_name,
                entity_id=request.entity_id,
                features=request.features,
            )
            return features
        except Exception as e:
            logger.error("Error retrieving features", error=str(e))
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    return app
