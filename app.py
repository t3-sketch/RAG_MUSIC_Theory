"""Streamlit アプリ本体。

    streamlit run app.py
"""
import tempfile
from pathlib import Path

import streamlit as st

import audio
import config
import llm
import retriever

import logging
from fastapi import FastAPI
import inngest
import inngest.fast_api
from inngest.experimental import ai

# Initialize the FastAPI app
app = FastAPI()
app.add_middleware(inngest.fast_api.Middleware)

st.set_page_config(page_title="音楽理論RAG解説", page_icon="🎵", layout="centered")
st.title("🎵 RAG 楽曲解説")
st.caption("教材コーパス × 音響解析 × Claude による音楽理論解説（個人用）")

# --- サイドバー ---
with st.sidebar:
    st.subheader("状態")
    n = retriever.count()
    st.metric("投入済みチャンク数", n)
    if n == 0:
        st.warning("先に `python ingest.py` で教材を投入してください。")
    st.text(f"埋め込み: {config.EMBED_MODEL}")
    st.text(f"生成: {config.GEMINI_MODEL}")
    st.text(f"生成: {config.GEMINI_MODEL}")
    if not config.GEMINI_API_KEY:
        st.error("GEMINI_API_KEY が未設定です（.env）。")

# --- 入力 ---
query = st.text_area(
    "質問",
    placeholder="例: この曲のコード進行はなぜ切なく聞こえる? Kawaii Future Bass によくある進行と比べて説明して。",
    height=100,
)

st.markdown("##### 音響解析（任意）")
mode = st.radio(
    "音源の指定方法",
    ["なし", "ローカルファイル", "Songle (URL)"],
    horizontal=True,
    label_visibility="collapsed",
)

uploaded = None
songle_url = ""
if mode == "ローカルファイル":
    uploaded = st.file_uploader("音声ファイル", type=["mp3", "wav", "flac"])
elif mode == "Songle (URL)":
    songle_url = st.text_input(
        "楽曲URL（YouTube / ニコニコ / SoundCloud など、Songle解析済みのもの）"
    )

run = st.button("解説を生成", type="primary")

# --- 実行 ---
if run:
    if not query.strip():
        st.warning("質問を入力してください。")
        st.stop()
    if not config.GEMINI_API_KEY:
        st.error("GEMINI_API_KEY が未設定です。")
        st.stop()

    audio_desc = None

    # 1) 音響解析
    if mode == "ローカルファイル" and uploaded is not None:
        with st.spinner("Librosa で音源を解析中..."):
            suffix = Path(uploaded.name).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded.getbuffer())
                tmp_path = tmp.name
            try:
                feats = audio.extract_local(tmp_path)
                audio_desc = audio.describe_local(feats)
            except Exception as e:
                st.error(f"音源解析に失敗しました: {e}")
    elif mode == "Songle (URL)" and songle_url.strip():
        with st.spinner("Songle API から解析結果を取得中..."):
            try:
                data = audio.fetch_songle(songle_url.strip())
                audio_desc = audio.describe_songle(data)
            except Exception as e:
                st.error(f"Songle 取得に失敗しました（未解析のURLの可能性）: {e}")

    # 2) 検索
    with st.spinner("教材を検索中..."):
        try:
            chunks = retriever.search(query)
        except Exception as e:
            st.error(f"検索に失敗しました: {e}")
            st.stop()

    # 3) 生成
    with st.spinner("Claude が解説を生成中..."):
        try:
            answer = llm.explain(query, chunks, audio_desc)
        except Exception as e:
            st.error(f"生成に失敗しました: {e}")
            st.stop()

    # --- 出力 ---
    st.markdown("### 解説")
    st.markdown(answer)

    if audio_desc:
        with st.expander("解析した音響特徴"):
            st.text(audio_desc)

    with st.expander(f"参照した教材チャンク（{len(chunks)}件）"):
        for i, c in enumerate(chunks, 1):
            st.markdown(
                f"**{i}. {c['meta'].get('source', '?')}** "
                f"(distance={c['distance']:.3f})"
            )
            st.text(c["text"][:400] + ("…" if len(c["text"]) > 400 else ""))
