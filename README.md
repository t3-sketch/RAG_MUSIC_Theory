# 🎵 music-rag — RAG 楽曲解説システム

音楽理論教材を知識ベースにした **RAG（検索拡張生成）** で、楽曲についての質問に音楽理論の観点から答えるローカルアプリ。
ローカル音源（Librosa）または web 上の楽曲（Songle API）の音響特徴を解析し、教材の理論と結びつけて Claude が日本語で解説する。

> 個人利用を前提とした最小構成。Python ワンスタック（Streamlit）で、サーバー不要。

---

## ✨ 特徴

- **教材ベースの解説** — 投入した教材（SoundQuest / musicplanz など）を根拠に回答。資料外の知識は明示。
- **2系統の音響解析**
  - ローカルファイル（mp3/wav/flac）→ Librosa で BPM・キー・音色を推定
  - web 上の楽曲 URL → Songle API（産総研）で **実際のコード進行・ビート・サビ構造** を取得
- **透明性** — 回答に使った教材チャンクの出典と、解析した音響特徴を画面で確認できる。
- **ローカル完結** — Chroma DB はローカル永続化。外部公開なし。

---

## 🧭 パイプライン

```
質問テキスト ─┐
              ├─→ クエリ統合 → BGE-M3 埋め込み → Chroma 検索(top-k) ─┐
音源(任意) ───┘                                                      ├─→ Claude API → 解説テキスト
   ├ ローカル → Librosa(BPM/Key/音色)                                │
   └ URL     → Songle(コード進行/ビート/構造) ──→ 音響特徴をテキスト化 ┘
                                                  教材コーパス(事前にChromaへ投入)
```

---

## 🛠 必要環境

- Python 3.10+
- `ffmpeg`（mp3 をローカル解析する場合に推奨）
- Anthropic API キー
- （任意）Songle API トークン

---

## 🚀 セットアップ

```bash
# 1. 依存をインストール
pip install -r requirements.txt

# 2. 環境変数を設定
cp .env.example .env
#   .env を編集し、ANTHROPIC_API_KEY を入れる

# 3. 教材を置く（PDF / HTML / txt / md に対応）
#   data/corpus/ 以下に配置

# 4. 教材を Chroma に投入（1回だけ。初回は BGE-M3 を自動DL ≈2GB）
python ingest.py

# 5. アプリ起動
streamlit run app.py
```

---

## 📖 使い方

1. ブラウザで開いたアプリに質問を入力。
2. 必要なら音源を指定：
   - **ローカルファイル**：自分の制作中の曲などをアップロード（Librosa 解析）
   - **Songle (URL)**：YouTube / ニコニコ等の URL を入力（Songle で解析済みの曲）
3. 「解説を生成」をクリック。
4. 解説本文・参照した教材チャンク・音響特徴が表示される。

---

## 📁 構成

```
music-rag/
├── app.py            # Streamlit UI 本体
├── ingest.py         # 教材投入スクリプト（1回実行）
├── retriever.py      # Chroma + BGE-M3 ラッパー（検索）
├── audio.py          # Librosa(ローカル) / Songle(URL) 音響解析
├── llm.py            # Claude API 呼び出し
├── config.py         # 設定の一元管理
├── requirements.txt
├── .env.example
└── data/
    ├── corpus/       # ここに教材を置く
    └── chroma/       # Chroma の永続化先（自動生成）
```

---

## ⚠️ 注意

- **Songle**：対象 URL が Songle 側で **事前解析済み** である必要がある。未解析なら songle.jp で解析申請を。
  REST のベース URL と認証方式は取得済みトークンのダッシュボードで確認し、必要に応じて `config.py` の `SONGLE_API_BASE` を調整すること。Songle は産総研（後藤真孝氏ら）の音楽理解技術による解析結果を提供するサービス。利用時はクレジット表記の規約を確認。
- **教材の著作権**：本構成は個人学習用途を前提とする。第三者への公開・配布を行う場合は教材の利用許諾を別途確認すること。
- **キー/BPM 推定**：Librosa 経路は信号からの統計的推定で誤差を含む。正確なコード進行が必要なら Songle 経路を使う。
- **初回実行**：BGE-M3（約2GB）のダウンロードが走るため、最初の `ingest.py` は時間がかかる。

---

## 🔧 設定（config.py / .env）

| 項目 | 既定値 | 説明 |
|---|---|---|
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | 生成モデル。高品質なら `claude-opus-4-8`、低コストなら `claude-haiku-4-5-20251001` |
| `EMBED_MODEL` | `BAAI/bge-m3` | 多言語埋め込みモデル |
| `CHUNK_CHARS` | `800` | チャンクの文字数 |
| `TOP_K` | `5` | 検索で取得するチャンク数 |
