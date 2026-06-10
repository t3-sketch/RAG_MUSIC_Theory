"""Chroma DB のラッパー。BGE-M3 埋め込み関数を使い、投入と検索の埋め込みを統一する。"""
from functools import lru_cache

import chromadb
from chromadb.utils import embedding_functions

import config


@lru_cache(maxsize=1)
def _embed_fn():
    # 初回呼び出し時に BGE-M3（約2GB）をダウンロードする。
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBED_MODEL
    )


@lru_cache(maxsize=1)
def get_collection():
    """コレクションを取得（なければ作成）。cosine 距離で固定。"""
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        embedding_function=_embed_fn(),
        metadata={"hnsw:space": "cosine"},
    )


def count() -> int:
    """投入済みチャンク数。"""
    try:
        return get_collection().count()
    except Exception:
        return 0


def search(query: str, top_k: int = config.TOP_K) -> list[dict]:
    """クエリに近いチャンクを top_k 件返す。"""
    col = get_collection()
    res = col.query(query_texts=[query], n_results=top_k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    return [
        {"text": d, "meta": m, "distance": dist}
        for d, m, dist in zip(docs, metas, dists)
    ]
