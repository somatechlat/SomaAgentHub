from __future__ import annotations

import re
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from collections.abc import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from services.common.config.base_settings import resolve_env

DATA_PATH = Path(__file__).resolve().parent / "corpus.txt"
_TOKEN_REGEX = re.compile(r"\w+|[^\w\s]")


@dataclass
class GenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


class MarkovTextGenerator:
    def __init__(self, corpus: str, order: int = 2, seed: int | None = None) -> None:
        if order < 1:
            raise ValueError("order must be >= 1")
        self.order = order
        self.random = random.Random(seed)
        self.tokens = self._tokenize(corpus)
        if len(self.tokens) < order + 1:
            raise ValueError("corpus too small")
        self.model: dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        for i in range(len(self.tokens) - order):
            state = tuple(self.tokens[i : i + order])
            nxt = self.tokens[i + order]
            self.model[state][nxt] += 1

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return _TOKEN_REGEX.findall(text.lower())

    def _temperature_sample(self, counter: Counter[str], temperature: float) -> str:
        if not counter:
            return self.random.choice(self.tokens)
        if temperature <= 0:
            return counter.most_common(1)[0][0]
        weights = np.array([c for _, c in counter.items()], dtype=float)
        adjusted = np.power(weights, 1.0 / max(temperature, 1e-3))
        probs = adjusted / adjusted.sum()
        choices = list(counter.keys())
        return self.random.choices(choices, weights=probs, k=1)[0]

    def generate(self, prompt: str, max_tokens: int = 64, temperature: float = 0.8) -> GenerationResult:
        prompt_tokens = self._tokenize(prompt) or self.tokens[: self.order]
        state = tuple(prompt_tokens[-self.order :]) if len(prompt_tokens) >= self.order else tuple(self.tokens[: self.order])
        generated: list[str] = []
        for _ in range(max_tokens):
            nxt = self._temperature_sample(self.model.get(state, Counter()), temperature)
            generated.append(nxt)
            state = tuple((*state[1:], nxt)) if len(state) == self.order else tuple((*state, nxt))
        completion = self._detokenize(generated)
        return GenerationResult(text=completion, prompt_tokens=len(prompt_tokens), completion_tokens=len(generated))

    @staticmethod
    def _detokenize(tokens: Sequence[str]) -> str:
        out: list[str] = []
        for tok in tokens:
            if not out:
                out.append(tok)
                continue
            if re.match(r"^[,.;:!?]$", tok):
                out[-1] = f"{out[-1]}{tok}"
            else:
                out.append(tok)
        return " ".join(out)


class TfidfEmbeddingModel:
    def __init__(self, documents):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.vectorizer.fit(documents)
        self.name = "local-tfidf-v1"

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.vectorizer.transform(texts).toarray().tolist()


@lru_cache(maxsize=1)
def load_corpus() -> str:
    if DATA_PATH.exists():
        return DATA_PATH.read_text(encoding="utf-8")
    return "SomaAgentHub local corpus seed."


@lru_cache(maxsize=1)
def get_text_generator() -> MarkovTextGenerator:
    return MarkovTextGenerator(load_corpus(), order=2)


@lru_cache(maxsize=1)
def get_embedding_model() -> TfidfEmbeddingModel:
    corpus = load_corpus()
    docs = [ln.strip() for ln in corpus.splitlines() if ln.strip()]
    return TfidfEmbeddingModel(docs or [corpus])
