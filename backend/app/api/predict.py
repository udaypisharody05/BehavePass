from fastapi import APIRouter, HTTPException, status
from app.ml.inference import (
    InferenceInputError,
    ModelArtifactError,
    ModelInferenceError,
    get_fusion_inference,
)
from app.schemas.session import PredictRequest, PredictResponse
from app.services.behavioural_rules import generate_behavioural_summary, map_zxcvbn_tier

router = APIRouter(prefix="/predict", tags=["Predict"])

@router.post("", response_model=PredictResponse)
def prototype_predict(req: PredictRequest):
    tier = map_zxcvbn_tier(req.static_features.zxcvbn_score)
    obs = generate_behavioural_summary(req.session_features, req.static_features)

    warnings = []
    fusion_prediction = None
    model_used = "Static analysis only"
    model_status = "sequence_unavailable"
    if not req.keystroke_sequence:
        warnings.append("No completed keystroke sequence was available; fusion inference was skipped.")
    else:
        if len(req.keystroke_sequence) < 6:
            warnings.append(
                "Sequence is shorter than those used during synthetic training; treat the estimate cautiously."
            )
        if len(req.keystroke_sequence) > 27:
            warnings.append(
                "Sequence is longer than those used during synthetic training; treat the estimate cautiously."
            )
        try:
            fusion_prediction = get_fusion_inference().predict(
                req.keystroke_sequence, req.static_features
            )
            model_used = "Synthetic proof-of-concept BiLSTM + MLP fusion"
            model_status = "ready_synthetic_proof_of_concept"
        except InferenceInputError as error:
            raise HTTPException(
                status_code=422, detail=str(error)
            ) from error
        except ModelArtifactError as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)
            ) from error
        except ModelInferenceError as error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fusion model inference failed; verify the backend logs and demo artifacts.",
            ) from error

    return PredictResponse(
        static_strength_tier=tier,
        zxcvbn_score=req.static_features.zxcvbn_score,
        log10_estimated_guesses=req.static_features.log10_estimated_guesses,
        behavioural_summary=obs,
        behavioural_model_status=model_status,
        fusion_log10_estimated_guesses=fusion_prediction,
        model_used=model_used,
        warnings=warnings,
    )
