import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from database import Database


PROFILES_DIR = Path(__file__).parent / "profiles"
PROFILES_DIR.mkdir(exist_ok=True)


class LSTMBaselineModel(nn.Module):
    """
    Simple LSTM-based sequence model capturing temporal behavior patterns.
    Inputs are generic numeric feature vectors; output is an embedding
    representing "normal" behavior.
    """

    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_dim, hidden_dim, num_layers=num_layers, batch_first=True
        )
        self.fc = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, input_dim)
        output, (hn, _) = self.lstm(x)
        # Use last hidden state as sequence representation
        h_last = hn[-1]  # (batch, hidden_dim)
        emb = self.fc(h_last)
        return emb


@dataclass
class AuraConfig:
    user: str = "default_user"
    learning_days: int = 7
    input_dim: int = 8  # number of numeric features extracted per event
    lstm_hidden_dim: int = 64
    lstm_layers: int = 2
    isolation_forest_estimators: int = 200
    isolation_forest_contamination: float = 0.01


class AuraEngine:
    """
    Hybrid ML engine:
      - LSTM learns temporal patterns over a 7-day learning period.
      - Isolation Forest learns a statistical baseline for anomaly detection.

    Two phases:
      - Learning Phase: accumulate normal traffic, fit models, persist `.h5` profile.
      - Defense Phase: load profile, score new events in real-time.
    """

    def __init__(self, config: Optional[AuraConfig] = None, db: Optional[Database] = None):
        self.config = config or AuraConfig()
        self.db = db or Database()
        self.user_id = self.db.get_or_create_user(self.config.user)

        self.scaler = StandardScaler()
        self.lstm = LSTMBaselineModel(
            input_dim=self.config.input_dim,
            hidden_dim=self.config.lstm_hidden_dim,
            num_layers=self.config.lstm_layers,
        )
        self.isolation_forest = IsolationForest(
            n_estimators=self.config.isolation_forest_estimators,
            contamination=self.config.isolation_forest_contamination,
            random_state=42,
        )

        self._profile_loaded = False
        self._profile_path: Optional[Path] = None

    # -------------------------------------------------------------------------
    # Feature engineering
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_features(packet_meta: Dict[str, Any]) -> np.ndarray:
        """
        Convert raw packet/session metadata into a fixed-size numeric feature vector.
        This is a simplified example; in production you'd extend with richer features.
        """
        timestamp = packet_meta.get("timestamp", datetime.utcnow().isoformat())
        dt = datetime.fromisoformat(timestamp)

        hour = dt.hour / 23.0
        minute = dt.minute / 59.0
        second = dt.second / 59.0

        # encode node (S1/S2/other)
        node = packet_meta.get("node", "S1")
        node_s1 = 1.0 if node == "S1" else 0.0
        node_s2 = 1.0 if node == "S2" else 0.0

        protocol = packet_meta.get("protocol", "TCP").upper()
        proto_tcp = 1.0 if protocol == "TCP" else 0.0
        proto_udp = 1.0 if protocol == "UDP" else 0.0

        bytes_sent = float(packet_meta.get("bytes_sent", 0))
        bytes_recv = float(packet_meta.get("bytes_recv", 0))

        features = np.array(
            [
                hour,
                minute,
                second,
                node_s1,
                node_s2,
                proto_tcp,
                proto_udp,
                np.log1p(bytes_sent + bytes_recv),
            ],
            dtype=np.float32,
        )
        return features

    # -------------------------------------------------------------------------
    # Profile persistence (.h5)
    # -------------------------------------------------------------------------
    def _profile_file_for_user(self) -> Path:
        return PROFILES_DIR / f"{self.config.user}_profile.h5"

    def _save_profile(self) -> Path:
        """
        Persist model weights and scaler statistics into an HDF5 file.
        The file is self-contained and re-loadable.
        """
        import h5py  # type: ignore

        path = self._profile_file_for_user()

        state = {
            "lstm_state_dict": self.lstm.state_dict(),
            "scaler_mean": self.scaler.mean_,
            "scaler_scale": self.scaler.scale_,
            "isolation_forest": self.isolation_forest,
            "config": self.config.__dict__,
        }

        # Store numpy arrays and torch weights as raw bytes; IF is pickled.
        with h5py.File(path, "w") as f:
            lstm_bytes = torch.save(self.lstm.state_dict(), torch.serialization.io.BytesIO())
            # torch.save above returns None; use an explicit buffer

        # Re-open and write correctly using an in-memory buffer
        with h5py.File(path, "w") as f:
            # LSTM
            buf = torch.serialization.io.BytesIO()
            torch.save(self.lstm.state_dict(), buf)
            f.create_dataset("lstm_state_dict", data=np.frombuffer(buf.getvalue(), dtype="uint8"))

            # Scaler
            f.create_dataset("scaler_mean", data=state["scaler_mean"])
            f.create_dataset("scaler_scale", data=state["scaler_scale"])

            # Isolation Forest + config as JSON string
            import pickle

            if_bytes = pickle.dumps(self.isolation_forest)
            f.create_dataset("isolation_forest", data=np.frombuffer(if_bytes, dtype="uint8"))
            f.attrs["config_json"] = json.dumps(self.config.__dict__)

        self._profile_loaded = True
        self._profile_path = path
        self.db.insert_profile(self.user_id, str(path), learning_complete=True)
        return path

    def _load_profile(self) -> None:
        """
        Load a persisted profile if exists; otherwise remain in cold start.
        """
        import h5py  # type: ignore
        import pickle

        path = self._profile_file_for_user()
        if not path.exists():
            return

        with h5py.File(path, "r") as f:
            # Restore scaler
            self.scaler.mean_ = f["scaler_mean"][()]
            self.scaler.scale_ = f["scaler_scale"][()]

            # Restore IF
            if_bytes = bytes(f["isolation_forest"][()])
            self.isolation_forest = pickle.loads(if_bytes)

            # Restore LSTM weights
            lstm_bytes = bytes(f["lstm_state_dict"][()])
            buf = torch.serialization.io.BytesIO(lstm_bytes)
            state_dict = torch.load(buf, map_location="cpu")
            self.lstm.load_state_dict(state_dict)

        self._profile_loaded = True
        self._profile_path = path

    # -------------------------------------------------------------------------
    # Learning & defense phases
    # -------------------------------------------------------------------------
    def train_profile(self, historical_events: List[Dict[str, Any]]) -> Path:
        """
        Train the hybrid model on 7 days of (assumed mostly normal) behavior.
        `historical_events` is a list of event dicts as produced by the firewall core.
        """
        if not historical_events:
            raise ValueError("No historical events provided for training.")

        # Filter to last `learning_days` if timestamps available
        cutoff = datetime.utcnow() - timedelta(days=self.config.learning_days)
        filtered: List[Dict[str, Any]] = []
        for ev in historical_events:
            ts_str = ev.get("timestamp")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str)
            except Exception:
                continue
            if ts >= cutoff:
                filtered.append(ev)

        if not filtered:
            filtered = historical_events

        feature_seqs: List[np.ndarray] = []
        flat_features: List[np.ndarray] = []

        # For simplicity, treat each event as length-1 sequence
        for ev in filtered:
            f = self.extract_features(ev)
            flat_features.append(f)
            feature_seqs.append(f[None, :])  # (1, input_dim)

        X = np.stack(flat_features, axis=0)  # (N, D)

        # Fit scaler and Isolation Forest
        X_scaled = self.scaler.fit_transform(X)
        self.isolation_forest.fit(X_scaled)

        # Prepare sequences for LSTM training
        seqs = np.stack(feature_seqs, axis=0)  # (N, 1, D)
        seqs_t = torch.tensor(seqs, dtype=torch.float32)

        # Self-supervised training: make embeddings close to their mean baseline
        optimizer = torch.optim.Adam(self.lstm.parameters(), lr=1e-3)
        self.lstm.train()

        for epoch in range(5):  # small number for prototype
            optimizer.zero_grad()
            emb = self.lstm(seqs_t)  # (N, H)
            baseline = emb.mean(dim=0, keepdim=True)
            loss = ((emb - baseline) ** 2).mean()
            loss.backward()
            optimizer.step()

        self.lstm.eval()
        return self._save_profile()

    def ensure_profile_loaded(self) -> None:
        if not self._profile_loaded:
            self._load_profile()

    def score_event(self, packet_meta: Dict[str, Any]) -> Tuple[float, bool]:
        """
        Score a single event. Returns (anomaly_score, is_anomaly).
        Anomaly score is normalized from Isolation Forest decision_function.
        """
        self.ensure_profile_loaded()
        feat = self.extract_features(packet_meta)[None, :]  # (1, D)
        X_scaled = self.scaler.transform(feat)
        score_raw = self.isolation_forest.decision_function(X_scaled)[0]
        # Lower scores = more abnormal; invert so that higher = more anomalous.
        anomaly_score = float(-score_raw)
        is_anomaly = anomaly_score > 0.2  # heuristic threshold
        return anomaly_score, is_anomaly


# -----------------------------------------------------------------------------
# Explainable AI (LLM wrapper)
# -----------------------------------------------------------------------------

class AuraExplainer:
    """
    LLM wrapper that turns raw anomaly scores + metadata into human-readable
    security explanations. By default uses OpenAI-compatible API; can be
    adapted to local models such as Ollama by customizing `_llm_call`.
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.provider = os.getenv("AURA_LLM_PROVIDER", "openai")  # 'openai' or 'ollama'

    def _llm_call(self, prompt: str) -> str:
        """
        Thin abstraction for the underlying LLM API.
        Implemented for OpenAI API and Ollama HTTP endpoint by convention.
        """
        provider = self.provider.lower()
        if provider == "openai":
            try:
                from openai import OpenAI  # type: ignore

                client = OpenAI()
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are AURA, a security copilot. "
                                "Explain anomalies in concise, user-friendly language, "
                                "emphasizing behavior deviations, timing, and device context."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=220,
                )
                return resp.choices[0].message.content.strip()
            except Exception as exc:  # fallback to raw prompt
                return f"(LLM unavailable: {exc}). Raw context: {prompt}"

        elif provider == "ollama":
            import requests  # type: ignore

            try:
                resp = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
            except Exception as exc:
                return f"(Local LLM unavailable: {exc}). Raw context: {prompt}"

        else:
            return f"(No LLM provider configured). Raw context: {prompt}"

    def explain_anomaly(
        self,
        anomaly_score: float,
        packet_meta: Dict[str, Any],
        baseline_summary: Optional[str] = None,
    ) -> str:
        """
        Construct a focused explanation based on anomaly score and metadata.
        """
        ts = packet_meta.get("timestamp", datetime.utcnow().isoformat())
        node = packet_meta.get("node", "S1")
        src_ip = packet_meta.get("src_ip", "unknown")
        dst_ip = packet_meta.get("dst_ip", "unknown")
        proto = packet_meta.get("protocol", "TCP")
        bytes_total = packet_meta.get("bytes_sent", 0) + packet_meta.get("bytes_recv", 0)

        prompt = (
            "You are part of AURA: an AI-driven behavioral firewall for IoT security.\n"
            "Turn the following anomaly context into a short human-readable alert.\n\n"
            f"Timestamp: {ts}\n"
            f"Node: {node} (e.g., S1 = primary, S2 = remote edge device)\n"
            f"Source IP: {src_ip}\n"
            f"Destination IP: {dst_ip}\n"
            f"Protocol: {proto}\n"
            f"Total bytes: {bytes_total}\n"
            f"Anomaly score: {anomaly_score:.3f} (higher = more abnormal)\n"
        )

        if baseline_summary:
            prompt += f"\nLearned baseline summary: {baseline_summary}\n"

        prompt += (
            "\nExplain what is unusual in 1–3 short sentences. "
            "Highlight timing (e.g., unusual 2 AM access), node deviation "
            "(S2 behaving unlike S1), or volume spikes. "
            "Avoid jargon; be specific about the deviation from baseline."
        )

        return self._llm_call(prompt)


__all__ = ["AuraEngine", "AuraConfig", "AuraExplainer"]

