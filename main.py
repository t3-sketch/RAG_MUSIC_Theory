"""
music-rag のオーケストレーション層。
各 step の「入力 → 出力の型」をここで先に固定する。
実装は各モジュール（ingest / embedder / retriever / llm / audio）に委譲する。

このファイルの構造:
  ① import
  ② inngest_client 定義
  ③ rag_ingest function
  ④ rag_query function
  ⑤ app = FastAPI() / serve
"""
from __future__ import annotations

import logging

import inngest
import inngest.fast_api
import pydantic
from fastapi import FastAPI
from dotenv import load_dotenv

import config
from custom_types import (
    # ingest 側
    ScrapeEntry,
    ChunkWithSource,
    UpsertResult,
    # query 側
    QueryEventData,
    RetrievedChunk,
    QueryResult,
)

# 処理モジュール（接着剤である main.py だけが全部を知る）
import ingest
# import embedder      # TODO: BGE-M3（Phase 1 で作る）
# import retriever     # TODO: Qdrant 版（Phase 1 で作る）
# import audio
# import llm

load_dotenv()


# ─────────────────────────────────────────────
#  ② Inngest client（function より先に定義する）
#     ※ @inngest_client.create_function はデコレータ評価時に
#       inngest_client が存在している必要がある。
# ─────────────────────────────────────────────
inngest_client = inngest.Inngest(
    app_id="music-rag",
    logger=logging.getLogger("uvicorn"),
    is_production=False,
    serializer=inngest.PydanticSerializer(),
)


# ─────────────────────────────────────────────
#  ingest 側のイベント入力モデル
#  （query 側の QueryEventData は custom_types にある。
#    ingest 側は url 1個だけなのでここに置く。後で custom_types に
#    移してもよい）
# ─────────────────────────────────────────────
class IngestEventData(pydantic.BaseModel):
    url: str


# =============================================================
#  rag_ingest function
#  流れ: scrape → chunk → embed → upsert
# =============================================================
@inngest_client.create_function(
    fn_id="rag-ingest",
    trigger=inngest.TriggerEvent(event="rag/ingest"),
)
async def rag_ingest(ctx: inngest.Context) -> dict:
    data = IngestEventData.model_validate(ctx.event.data)

    # ── step1: スクレイプ ───────────────────────────
    # in : str (url)   out: list[ScrapeEntry]
    # TODO: ingest.scrape(data.url) を呼び、ScrapeEntry に詰める
    entries = await ctx.step.run(
        "scrape",
        lambda: ...,  # TODO
    )

    # ── step2: チャンク分割 ─────────────────────────
    # in : list[ScrapeEntry]   out: list[ChunkWithSource]
    # TODO: ingest.chunk(entries, source_id) を呼ぶ
    chunks = await ctx.step.run(
        "chunk",
        lambda: ...,  # TODO
    )

    # ── step3: embed ───────────────────────────────
    # in : list[str]   out: list[list[float]]（各1024次元）
    # TODO: embedder.embed_documents([c.text for c in chunks])
    vectors = await ctx.step.run(
        "embed",
        lambda: ...,  # TODO
    )

    # ── step4: Qdrant upsert ───────────────────────
    # in : list[ChunkWithSource], list[list[float]]   out: UpsertResult
    # TODO: retriever.upsert(chunks, vectors)
    result = await ctx.step.run(
        "upsert",
        lambda: ...,  # TODO
    )

    return {"ingested": ..., "source": data.url}  # TODO: result.model_dump()


# =============================================================
#  rag_query function
#  流れ: embed → search →（任意）audio → generate
# =============================================================
@inngest_client.create_function(
    fn_id="rag-query",
    trigger=inngest.TriggerEvent(event="rag/query"),
)
async def rag_query(ctx: inngest.Context) -> dict:
    data = QueryEventData.model_validate(ctx.event.data)

    # ── step1: クエリを embed ───────────────────────
    # in : str (query)   out: list[float]（1024次元）
    # TODO: embedder.embed_query(data.query)
    query_vector = await ctx.step.run(
        "embed-query",
        lambda: ...,  # TODO
    )

    # ── step2: Qdrant 検索 ──────────────────────────
    # in : list[float], int (top_k)   out: list[RetrievedChunk]
    # TODO: retriever.search(query_vector, data.top_k)
    found = await ctx.step.run(
        "search",
        lambda: ...,  # TODO
    )

    # ── step3: 音声解析（任意）─────────────────────
    # in : str | None (songle_url)   out: str | None
    # TODO: data.songle_url があれば audio.fetch_songle → describe_songle
    audio_desc = await ctx.step.run(
        "analyze-audio",
        lambda: ...,  # TODO（None もありうる）
    )

    # ── 変換（step の外。重い処理ではないのでリトライ単位にしない）──
    #   retriever は RetrievedChunk を返すが、llm.explain は
    #   c["meta"]["source"] / c["text"] という dict を期待する。
    #   この不一致をここ（接着剤）で吸収する。
    chunks_for_llm = [{"text": c.text, "meta": {"source": c.source}} for c in found]

    # ── step4: Gemini で生成 ────────────────────────
    # in : str (query), list[dict], str | None   out: str
    # TODO: llm.explain(data.query, chunks_for_llm, audio_desc)
    answer = await ctx.step.run(
        "generate",
        lambda: ...,  # TODO
    )

    return {
        "answer": ...,        # TODO: answer
        "sources": ...,       # TODO: [c.source for c in found]
        "num_contexts": ...,  # TODO: len(found)
    }


# ─────────────────────────────────────────────
#  ⑤ FastAPI 入口（薄い箱）+ Inngest マウント
# ─────────────────────────────────────────────
app = FastAPI()

inngest.fast_api.serve(
    app,
    inngest_client,
    [rag_ingest, rag_query],
)