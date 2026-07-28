from fastapi import APIRouter
from app.schemas.session import PredictRequest, PredictResponse
from app.services.behavioural_rules import generate_behavioural_summary, map_zxcvbn_tier

router = APIRouter(prefix="/predict", tags=["Predict"])

@router.post("", response_model=PredictResponse)
def prototype_predict(req: PredictRequest):
    tier = map_zxcvbn_tier(req.static_features.zxcvbn_score)
    obs = generate_behavioural_summary(req.session_features, req.static_features)

    return PredictResponse(
        static_strength_tier=tier,
        zxcvbn_score=req.static_features.zxcvbn_score,
        log10_estimated_guesses=req.static_features.log10_estimated_guesses,
        behavioural_summary=obs,
        behavioural_model_status="not_trained"
    )
