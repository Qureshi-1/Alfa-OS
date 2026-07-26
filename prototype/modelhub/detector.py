"""Model Detector — automatic model detection for family, architecture, modality, provider, tokenizer, runtime."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from prototype.modelhub.base import (
    ModelCapabilities, ModelInfo, ModelModality, ModelProvider, ProviderType,
)

logger = logging.getLogger("alfa.modelhub.detector")

# ── Family detection patterns ───────────────────────────────────────────────

_FAMILY_KEYWORDS: Dict[str, List[str]] = {
    "llama": ["llama", "alpaca", "vicuna", "guanaco", "wizard-vicuna", "codellama", "tree"],
    "mistral": ["mistral", "mixtral", "mistralite", "zephyr"],
    "qwen": ["qwen", "qwen2", "qwen3", "qwq"],
    "gemma": ["gemma", "gemma2"],
    "phi": ["phi-", "phi2", "phi3", "phi4"],
    "falcon": ["falcon", "refact"],
    "bloom": ["bloom", "bloomz"],
    "mpt": ["mpt", "mpt-"],
    "gpt": ["gpt2", "gpt-j", "gpt-neox", "gpt-bigcode"],
    "starcoder": ["starcoder", "starcoder2"],
    "code-llama": ["code-llama", "codellama"],
    "yi": ["yi-", "yi1", "yi2"],
    "deepseek": ["deepseek"],
    "baichuan": ["baichuan"],
    "internlm": ["internlm"],
    "dbrx": ["dbrx"],
    "command-r": ["command-r", "c4ai"],
    "gemini": ["gemini"],
    "claude": ["claude"],
    "o1": ["o1-", "o1_"],
    "o3": ["o3-", "o3_"],
    "o4": ["o4-", "o4_"],
}

_ARCHITECTURE_KEYWORDS: Dict[str, List[str]] = {
    "transformer": ["transformer", "decoder", "encoder-decoder"],
    "mamba": ["mamba", "ssm", "state-space"],
    "mixture-of-experts": ["moe", "mixture-of-experts", "mixtral", "dbrx"],
    "recurrentgemma": ["recurrent", "gru"],
    "gemma2": ["gemma2"],
}

_QUANT_PATTERNS = ["q2_k", "q3_k_s", "q3_k_m", "q3_k_l", "q4_0", "q4_k_s", "q4_k_m", "q5_0", "q5_k_s", "q5_k_m", "q6_k", "q8_0", "iq1", "iq2", "iq3", "iq4", "f16", "f32"]


class ModelDetector:
    """Automatic model detection from file paths, configs, and metadata."""

    def detect_from_file(self, path: Path) -> Dict[str, Any]:
        """Detect model attributes from a file path."""
        info: Dict[str, Any] = {"path": str(path)}

        name = path.stem if path.is_file() else path.name
        suffix = path.suffix.lower()

        info["family"] = self.detect_family(name)
        info["quantization"] = self.detect_quantization(name)
        info["parameter_count"] = self.detect_parameter_count(name)

        if suffix == ".gguf":
            info["runtime"] = "llama.cpp"
            info["architecture"] = "gguf"
            info["local"] = True
        elif suffix in {".safetensors", ".bin", ".pt", ".pth"}:
            info["runtime"] = "transformers"
            info["architecture"] = "transformer"
            info["local"] = True
        elif suffix == ".mlx":
            info["runtime"] = "mlx"
            info["architecture"] = "mlx"
            info["local"] = True
        elif suffix == ".onnx":
            info["runtime"] = "onnx"
            info["architecture"] = "onnx"
            info["local"] = True

        return info

    def detect_from_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect model attributes from HuggingFace-style config.json."""
        info: Dict[str, Any] = {}

        arch = config.get("architectures", config.get("model", ""))[0] if isinstance(config.get("architectures", config.get("model", "")), list) else config.get("architectures", "")
        info["architecture"] = arch or "unknown"

        model_type = config.get("model_type", "")
        info["family"] = model_type or self._arch_to_family(arch)

        hidden = config.get("hidden_size", 0)
        layers = config.get("num_hidden_layers", 0)
        vocab = config.get("vocab_size", 0)
        if hidden and layers:
            info["parameter_count"] = int(12 * hidden * hidden * layers + vocab * hidden)

        max_pos = config.get("max_position_embeddings", 0)
        if max_pos:
            info["max_context_length"] = max_pos

        tokenizer = config.get("tokenizer_class", "")
        if tokenizer:
            info["tokenizer"] = tokenizer

        # Detect modality from model_type
        modality_str = config.get("modalities", ["text"])
        if isinstance(modality_str, list):
            modality_map = {
                "text": ModelModality.TEXT, "image": ModelModality.IMAGE,
                "audio": ModelModality.AUDIO, "video": ModelModality.VIDEO,
            }
            if len(modality_str) > 1:
                info["modality"] = ModelModality.MULTIMODAL
            elif modality_str:
                info["modality"] = modality_map.get(modality_str[0], ModelModality.TEXT)

        return info

    def detect_from_model_info(self, model: ModelInfo) -> ModelInfo:
        """Enrich a ModelInfo with auto-detected attributes."""
        if model.family == "unknown" or not model.family:
            model.family = self.detect_family(model.name)
        if model.architecture == "unknown" or not model.architecture:
            model.architecture = self._guess_architecture(model)
        if not model.quantization:
            model.quantization = self.detect_quantization(model.name)
        if not model.parameter_count:
            model.parameter_count = self.detect_parameter_count(model.name)
        if model.tokenizer == "auto" or not model.tokenizer:
            model.tokenizer = self._guess_tokenizer(model)
        return model

    def detect_family(self, name: str) -> str:
        name_lower = name.lower()
        for family, keywords in _FAMILY_KEYWORDS.items():
            if any(kw in name_lower for kw in keywords):
                return family
        return "unknown"

    def detect_quantization(self, name: str) -> str:
        name_lower = name.lower()
        for quant in _QUANT_PATTERNS:
            if quant in name_lower:
                return quant
        return "unknown"

    def detect_parameter_count(self, name: str) -> int:
        import re
        match = re.search(r"(\d+(?:\.\d+)?)\s*[bB]", name)
        if match:
            val = float(match.group(1))
            if val < 100:
                return int(val * 1_000_000_000)
            return int(val)
        return 0

    def detect_modality(self, name: str, config: Optional[Dict] = None) -> ModelModality:
        if config:
            modalities = config.get("modalities", ["text"])
            if isinstance(modalities, list) and len(modalities) > 1:
                return ModelModality.MULTIMODAL
        name_lower = name.lower()
        if any(k in name_lower for k in ["vision", "-v", "multimodal"]):
            return ModelModality.MULTIMODAL
        if "audio" in name_lower:
            return ModelModality.AUDIO
        return ModelModality.TEXT

    def _arch_to_family(self, arch: str) -> str:
        if not arch:
            return "unknown"
        arch_lower = arch.lower()
        for family, keywords in _FAMILY_KEYWORDS.items():
            if any(kw in arch_lower for kw in keywords):
                return family
        if "llama" in arch_lower: return "llama"
        if "mistral" in arch_lower: return "mistral"
        if "gemma" in arch_lower: return "gemma"
        if "qwen" in arch_lower: return "qwen"
        return "unknown"

    def _guess_architecture(self, model: ModelInfo) -> str:
        if model.runtime in {"llama.cpp", "ollama"}:
            return "gguf"
        if model.runtime == "mlx":
            return "mlx"
        if model.runtime == "transformers":
            return "transformer"
        return "unknown"

    def _guess_tokenizer(self, model: ModelInfo) -> str:
        if model.runtime == "llama.cpp":
            return "llama"
        if model.runtime == "mlx":
            return "auto"
        if model.runtime == "transformers":
            return "auto"
        return "auto"


# ── Singleton ───────────────────────────────────────────────────────────────

_detector_instance: Optional[ModelDetector] = None


def get_model_detector() -> ModelDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = ModelDetector()
    return _detector_instance