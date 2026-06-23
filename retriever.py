"""
Chroma DB を使ったベクトル検索のラッパー。BGE-M3 埋め込み関数を使用し、投入と検索の埋め込みを統一する。
- get_collection(): DB取得・ingest/内部で使用
- count(): BGE-M3モデル初期化。
- search(query, top_k): 類似検索
"""

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
    """
    登録数確認。app.py のサイドバーで使用。
    例外が起きたら 0 を返す（未投入 or コレクション破損の可能性）。
    """

    try:
        return get_collection().count()
    except Exception:
        return 0


def search(query: str, top_k: int = config.TOP_K) -> list[dict]:
    """
    クエリに近いチャンクを top_k 件返す。 
    app.py の質問実行時に使用。返り値はリストで、各要素は 
    {"text": ..., "meta": ..., "distance": ...} の形式。
    """

    col = get_collection()
    res = col.query(query_texts=[query], n_results=top_k)
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    return [
        {"text": d, "meta": m, "distance": dist}
        for d, m, dist in zip(docs, metas, dists)
    ]
