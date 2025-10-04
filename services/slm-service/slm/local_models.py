"""Local deterministic models powering the SLM service.

The implementation avoids mocks by training lightweight statistical models
on a real corpus that ships with the repository. The text generator uses a
second-order Markov chain, while the embedding model relies on TF-IDF vectors.
Both models are deterministic once initialised and do not require external
network calls.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Sequence
import random
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_PATH = Path(__file__).resolve().parent / "data" / "corpus.txt"
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
    """A simple second-order Markov chain text generator."""

    def __init__(self, corpus: str, order: int = 2, seed: int | None = None) -> None:
        if order < 1:
            raise ValueError("order must be >= 1")
        self.order = order
        self.random = random.Random(seed)
        self.tokens = self._tokenize(corpus)
        if len(self.tokens) < order + 1:
            raise ValueError("corpus too small for markov chain")
        self.model: Dict[tuple[str, ...], Counter[str]] = defaultdict(Counter)
        for idx in range(len(self.tokens) - order):
            state = tuple(self.tokens[idx : idx + order])
            nxt = self.tokens[idx + order]
            self.model[state][nxt] += 1

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return _TOKEN_REGEX.findall(text.lower())

    def _temperature_sample(self, counter: Counter[str], temperature: float) -> str:
        if not counter:
            return self.random.choice(self.tokens)
        if temperature <= 0:
            return counter.most_common(1)[0][0]
        weights = np.array([count for _, count in counter.items()], dtype=float)
        adjusted = np.power(weights, 1.0 / max(temperature, 1e-3))
        probs = adjusted / adjusted.sum()
        choices = list(counter.keys())
        return self.random.choices(choices, weights=probs, k=1)[0]

    def generate(self, prompt: str, max_tokens: int = 64, temperature: float = 0.8) -> GenerationResult:
        prompt_tokens = self._tokenize(prompt)
        if not prompt_tokens:
            prompt_tokens = self.tokens[: self.order]
        state = tuple(prompt_tokens[-self.order :]) if len(prompt_tokens) >= self.order else tuple(self.tokens[: self.order])
        generated: List[str] = []
        for _ in range(max_tokens):
            next_token = self._temperature_sample(self.model.get(state, Counter()), temperature)
            generated.append(next_token)
            if len(state) == self.order:
                state = tuple((*state[1:], next_token))
            else:
                state = tuple((*state, next_token))
        completion = self._detokenize(generated)
        return GenerationResult(
            text=completion,
            prompt_tokens=len(prompt_tokens),
            completion_tokens=len(generated),
        )

    @staticmethod
    def _detokenize(tokens: Sequence[str]) -> str:
        pieces: List[str] = []
        for token in tokens:
            if not pieces:
                pieces.append(token)
                continue
            if re.match(r"^[,.;:!?]$", token):
                pieces[-1] = f"{pieces[-1]}{token}"
            else:
                pieces.append(token)
        return " ".join(pieces)


class TfidfEmbeddingModel:
    """Vectorises text using TF-IDF on the shipped corpus."""

    def __init__(self, documents: Iterable[str]) -> None:
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.vectorizer.fit(documents)
        self.name = "somasuite-tfidf-v1"

    def embed(self, texts: List[str]) -> List[List[float]]:
        matrix = self.vectorizer.transform(texts)
        return matrix.toarray().tolist()


@lru_cache(maxsize=1)
def load_corpus() -> str:
    return DATA_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def get_text_generator() -> MarkovTextGenerator:
    return MarkovTextGenerator(load_corpus(), order=2)


@lru_cache(maxsize=1)
def get_embedding_model() -> TfidfEmbeddingModel:
    corpus = load_corpus()
    documents = [line.strip() for line in corpus.splitlines() if line.strip()]
    return TfidfEmbeddingModel(documents)