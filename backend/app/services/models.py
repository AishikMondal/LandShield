from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from ..config import MODEL_DIR, ENABLE_EXPERIMENTAL_FUSION, ENABLE_RECONSTRUCTED_MODEL2


class ModelRegistry:
    """Loads and runs only the supplied artifacts that are genuinely usable.

    - Model 1: calibrated susceptibility classifier (ACTIVE).
    - Model 2: reconstructed PyTorch NN — DISABLED until the original class is
      supplied (state_dict loads, but activations/dropout are unverified).
    - Model 3: IsolationForest anomaly evidence (ACTIVE).
    - Model 4: supplied artifact is a climate classifier, NOT spatial
      vulnerability -> DISABLED.
    - Fusion: 4-input network requiring Model 2 + a Model 4
      spatial_vulnerability_score -> DISABLED unless ENABLE_EXPERIMENTAL_FUSION.
    """

    def __init__(self):
        self.status: dict[str, dict] = {}
        self.m1 = self.m2 = self.m2_pre = self.m3 = self.m3_scaler = self.fusion = self.fusion_scaler = None
        self.m1_features = self.m2_features = self.m3_features = []
        self._load()

    # ------------------------------------------------------------------
    def _load(self):
        # Model 1
        try:
            self.m1 = joblib.load(MODEL_DIR / "model1" / "model_1_pipeline.pkl")
            cfg = json.loads((MODEL_DIR / "model1" / "feature_config.json").read_text())
            self.m1_features = cfg["feature_order"]
            self.status["model1"] = {
                "name": "Terrain/Susceptibility Classifier",
                "loaded": True,
                "enabled": True,
                "status": "ACTIVE",
                "artifact": "model_1_pipeline.pkl",
                "framework": "scikit-learn CalibratedClassifierCV (LogisticRegression)",
                "n_features": len(self.m1_features),
                "default_inputs": True,
                "note": "Calibrated P(landslide) used as the primary operational score when fusion is unavailable.",
            }
        except Exception as e:  # noqa: BLE001
            self.status["model1"] = {"name": "Terrain/Susceptibility Classifier", "loaded": False,
                                     "enabled": False, "status": "ERROR", "error": str(e), "default_inputs": True}

        # Model 3
        try:
            self.m3_scaler = joblib.load(MODEL_DIR / "model3" / "model_3_scaler.pkl")
            self.m3 = joblib.load(MODEL_DIR / "model3" / "model_3_isolation_forest.pkl")
            cfg = json.loads((MODEL_DIR / "model3" / "model_3_feature_config.json").read_text())
            self.m3_features = cfg["feature_order"]
            self.status["model3"] = {
                "name": "Environmental Anomaly Detector",
                "loaded": True,
                "enabled": True,
                "status": "ACTIVE",
                "artifact": "model_3_isolation_forest.pkl",
                "framework": "scikit-learn IsolationForest",
                "n_features": len(self.m3_features),
                "note": "Anomaly evidence only; not a calibrated landslide probability.",
            }
        except Exception as e:  # noqa: BLE001
            self.status["model3"] = {"name": "Environmental Anomaly Detector", "loaded": False,
                                     "enabled": False, "status": "ERROR", "error": str(e)}

        # Model 2 (reconstructed)
        try:
            import torch
            import torch.nn as nn

            class DynamicRiskNN(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.network = nn.Sequential(
                        nn.Linear(34, 64), nn.BatchNorm1d(64), nn.ReLU(), nn.Dropout(0.3),
                        nn.Linear(64, 32), nn.BatchNorm1d(32), nn.ReLU(), nn.Dropout(0.2),
                        nn.Linear(32, 16), nn.ReLU(), nn.Linear(16, 1), nn.Sigmoid(),
                    )

                def forward(self, x):
                    return self.network(x)

            model = DynamicRiskNN()
            state = torch.load(MODEL_DIR / "model2" / "model2_dynamic_risk_nn.pth", map_location="cpu", weights_only=True)
            model.load_state_dict(state, strict=True)
            model.eval()
            self.m2 = model
            self.m2_pre = joblib.load(MODEL_DIR / "model2" / "model2_preprocessor.pkl")
            cfg = json.loads((MODEL_DIR / "model2" / "model2_feature_config.json").read_text())
            self.m2_features = cfg["feature_order"]
            self.status["model2"] = {
                "name": "Dynamic Risk Neural Network",
                "loaded": True,
                "enabled": ENABLE_RECONSTRUCTED_MODEL2,
                "status": "ACTIVE" if ENABLE_RECONSTRUCTED_MODEL2 else "DISABLED",
                "artifact": "model2_dynamic_risk_nn.pth",
                "framework": "PyTorch (state_dict)",
                "n_features": len(self.m2_features),
                "reason": ("Original Model 2 class definition missing; state_dict strictly validates a "
                           "34->64->32->16->1 architecture but activations/dropout cannot be confirmed."),
                "note": "Enable only with ENABLE_RECONSTRUCTED_MODEL2=true.",
            }
        except Exception as e:  # noqa: BLE001
            self.status["model2"] = {"name": "Dynamic Risk Neural Network", "loaded": False,
                                     "enabled": False, "status": "DISABLED",
                                     "reason": f"Cannot load state dict: {e}"}

        # Model 4
        self.status["model4"] = {
            "name": "Spatial Vulnerability Model",
            "loaded": False,
            "enabled": False,
            "status": "DISABLED",
            "reason": ("Supplied Model 4 artifact predicts a 5-class climate label, "
                       "not a 0-1 spatial_vulnerability_score required by the fusion engine."),
        }

        # Fusion
        try:
            import torch
            import torch.nn as nn

            class FusionNN(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.net = nn.Sequential(
                        nn.Linear(4, 16), nn.LayerNorm(16), nn.ReLU(), nn.Dropout(0.2),
                        nn.Linear(16, 8), nn.ReLU(), nn.Linear(8, 1), nn.Sigmoid(),
                    )

                def forward(self, x):
                    return self.net(x)

            f = FusionNN()
            f.load_state_dict(torch.load(MODEL_DIR / "fusion" / "fusion_model.pth", map_location="cpu", weights_only=True))
            f.eval()
            self.fusion = f
            self.fusion_scaler = joblib.load(MODEL_DIR / "fusion" / "feature_scaler.pkl")
            self.status["fusion"] = {
                "name": "Fusion Decision Engine",
                "loaded": True,
                "enabled": ENABLE_EXPERIMENTAL_FUSION,
                "status": "ACTIVE" if ENABLE_EXPERIMENTAL_FUSION else "DISABLED",
                "framework": "PyTorch",
                "inputs": ["susceptibility_prob", "dynamic_prob", "anomaly_score", "spatial_vulnerability_score"],
                "reason": ("Requires Model 2 dynamic_prob and a real Model 4 spatial_vulnerability_score. "
                           "Experimental mode substitutes a GIS exposure proxy."),
                "note": "Enable only with ENABLE_EXPERIMENTAL_FUSION=true.",
            }
        except Exception as e:  # noqa: BLE001
            self.status["fusion"] = {"name": "Fusion Decision Engine", "loaded": False,
                                     "enabled": False, "status": "ERROR", "error": str(e),
                                     "reason": "Fusion artifact failed to load."}

    # ------------------------------------------------------------------
    def predict(self, features: dict, spatial_proxy: Optional[float] = None) -> dict:
        out: dict = {}
        if self.m1 is not None:
            try:
                df = pd.DataFrame([[features.get(k) for k in self.m1_features]], columns=self.m1_features)
                p = float(self.m1.predict_proba(df)[0, 1])
                out["susceptibility_prob"] = max(0.0, min(1.0, p))
            except Exception as e:  # noqa: BLE001
                self.status["model1"]["inference_error"] = str(e)

        if ENABLE_RECONSTRUCTED_MODEL2 and self.m2 is not None and self.m2_pre is not None:
            try:
                import torch
                df = pd.DataFrame([[features.get(k) for k in self.m2_features]], columns=self.m2_features)
                x = self.m2_pre.transform(df)
                with torch.no_grad():
                    p = float(self.m2(torch.as_tensor(x, dtype=torch.float32)).reshape(-1)[0].item())
                out["dynamic_prob"] = max(0.0, min(1.0, p))
            except Exception as e:  # noqa: BLE001
                self.status["model2"]["inference_error"] = str(e)

        if self.m3 is not None and self.m3_scaler is not None:
            try:
                df = pd.DataFrame([[features.get(k) for k in self.m3_features]], columns=self.m3_features)
                x = self.m3_scaler.transform(df)
                decision = float(self.m3.decision_function(x)[0])
                # Map small negative decision -> high anomaly. Fixed scale (20)
                # chosen so decision==-0.15 -> ~0.95. Score is evidence, not probability.
                anomaly = float(1 / (1 + math.exp(20 * decision)))
                out["anomaly_score"] = max(0.0, min(1.0, anomaly))
                out["anomaly_decision_function"] = round(decision, 6)
            except Exception as e:  # noqa: BLE001
                self.status["model3"]["inference_error"] = str(e)

        if ENABLE_EXPERIMENTAL_FUSION and self.fusion is not None and self.fusion_scaler is not None:
            required = ["susceptibility_prob", "dynamic_prob", "anomaly_score"]
            if spatial_proxy is not None and all(k in out for k in required) and self.m2 is not None:
                try:
                    import torch
                    arr = np.array([[out["susceptibility_prob"], out["dynamic_prob"], out["anomaly_score"], spatial_proxy]])
                    scaled = self.fusion_scaler.transform(arr)
                    with torch.no_grad():
                        fp = float(self.fusion(torch.as_tensor(scaled, dtype=torch.float32)).reshape(-1)[0].item())
                    out["fusion_prob"] = max(0.0, min(1.0, fp))
                    out["spatial_vulnerability_score"] = spatial_proxy
                    out["fusion_mode"] = "experimental_proxy"
                except Exception as e:  # noqa: BLE001
                    self.status["fusion"]["inference_error"] = str(e)
        return out