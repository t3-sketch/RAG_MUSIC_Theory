"""プロジェクト全体の設定を一元管理するモジュール。"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- パス ---
BASE_DIR = Path(__file__).parent
CORPUS_DIR = BASE_DIR / "data" / "corpus"   # 教材（PDF/HTML/txt/md）を置く場所
CHROMA_DIR = BASE_DIR / "data" / "chroma"   # Chroma の永続化先

# --- ベクトルDB ---
COLLECTION_NAME = "music_theory"

# --- モデル ---
EMBED_MODEL = os.getenv("EMBED_MODEL", "BAAI/bge-m3")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# --- Songle API ---
SONGLE_API_TOKEN = os.getenv("SONGLE_API_TOKEN", "")
# 注意: ベースURLと認証方式は取得済みトークンのダッシュボードで要確認。
# 必要に応じてここを書き換えてください。
SONGLE_API_BASE = "https://widget.songle.jp/api/v1"

# --- チャンク分割（文字数ベース。日本語教材を想定）---
CHUNK_CHARS = 800
CHUNK_OVERLAP = 120

# --- 検索・生成 ---
TOP_K = 5
MAX_TOKENS = 1500
