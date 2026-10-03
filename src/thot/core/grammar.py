"""Optional T5-based grammar and punctuation fixer (English only)."""

from __future__ import annotations

from thot.config import GRAMMAR_MODEL

_BATCH_SIZE = 8
_MAX_INPUT_TOKENS = 512  # T5 context size


class GrammarCorrector:
    """Loads the model on first use so it costs nothing when grammar correction is off."""

    def __init__(self, model_name: str = GRAMMAR_MODEL) -> None:
        self.model_name = model_name
        self._model = None
        self._tokenizer = None

    def _load(self) -> None:
        try:
            from transformers import T5ForConditionalGeneration, T5Tokenizer
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "Grammar correction requires the 'grammar' extra: pip install 'thot[grammar]'"
            ) from exc
        self._tokenizer = T5Tokenizer.from_pretrained(self.model_name)
        self._model = T5ForConditionalGeneration.from_pretrained(self.model_name).eval()

    def correct(self, texts: list[str]) -> list[str]:
        """Correct each text independently, preserving the list order and length."""
        if not texts:
            return []
        if self._model is None:
            self._load()

        import torch

        results: list[str] = []
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = [f"fix: {t.strip()}" for t in texts[start : start + _BATCH_SIZE]]
            inputs = self._tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=_MAX_INPUT_TOKENS,
            )
            with torch.inference_mode():
                output_ids = self._model.generate(
                    **inputs,
                    max_new_tokens=int(inputs["input_ids"].shape[1] * 1.5) + 8,
                    num_beams=4,
                    early_stopping=True,
                    repetition_penalty=1.5,
                    no_repeat_ngram_size=3,
                )
            results.extend(self._tokenizer.batch_decode(output_ids, skip_special_tokens=True))
        return results
