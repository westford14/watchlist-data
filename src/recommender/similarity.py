"""Semantic similarity model."""

import json
import logging
import os
from typing import Any, List, Optional, Tuple

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


class SimilarityMeasure:
    def __init__(
        self,
        embed_model_name: str = "all-MiniLM-L6-v2",
        embed_device: str = "cpu",
        embed_batch_size: int = 64,
        embed_max_seq_length: int = 512,
    ) -> None:
        self.embed_model_name = embed_model_name
        self.embed_device = embed_device
        self.embed_batch_size = embed_batch_size
        self.embed_max_seq_length = embed_max_seq_length

        self.embeddings = None
        self.faiss_index = None
        self.cluster_labels = None
        self.texts = None
        self.projections = None

        self.embed_model = SentenceTransformer(
            self.embed_model_name, device=self.embed_device
        )
        self.embed_model.max_seq_length = self.embed_max_seq_length

        self.index_to_id = None

    def fit(
        self, texts: List[str], ids: List[int], embeddings: Optional[Any] = None
    ) -> Tuple[List[Any], List[int]]:
        self.texts = texts  # type: ignore

        if embeddings is None:
            logging.info("embedding texts...")
            self.embeddings = self.embed(texts)  # type: ignore
        else:
            logging.info("using precomputed embeddings...")
            self.embeddings = embeddings

        logging.info("building faiss index...")
        self.faiss_index = self.build_faiss_index(self.embeddings)  # type: ignore
        self.index_to_id = dict(
            zip(list(range(self.faiss_index.ntotal)), ids)  # type: ignore
        )
        return self.embeddings  # type: ignore

    def infer(self, texts: List[str], top_k: int = 1) -> Tuple[List[int], List[Any]]:
        embeddings = self.embed(texts)
        _, neighbours = self.faiss_index.search(embeddings, top_k)  # type: ignore

        return neighbours, embeddings

    def embed(self, texts: List[str]) -> List[Any]:
        embeddings = self.embed_model.encode(
            texts,
            batch_size=self.embed_batch_size,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings  # type: ignore

    def build_faiss_index(self, embeddings: List[Any]) -> List[int]:
        index = faiss.IndexFlatL2(embeddings.shape[1])  # type: ignore
        index.add(embeddings)
        return index  # type: ignore

    def save(self, folder: str) -> None:
        if not os.path.exists(folder):
            os.makedirs(folder)

        with open(f"{folder}/embeddings.npy", "wb") as f:
            np.save(f, self.embeddings)  # type: ignore

        with open(f"{folder}/index_to_id.json", "w") as f:
            json.dump(self.index_to_id, f)

        faiss.write_index(self.faiss_index, f"{folder}/faiss.index")

    def load(self, folder: str) -> None:
        if not os.path.exists(folder):
            raise ValueError(f"The folder '{folder}' does not exsit.")

        with open(f"{folder}/embeddings.npy", "rb") as f:
            self.embeddings = np.load(f)

        with open(f"{folder}/index_to_id.json", "r") as f:
            self.index_to_id = json.load(f)

        self.faiss_index = faiss.read_index(f"{folder}/faiss.index")
