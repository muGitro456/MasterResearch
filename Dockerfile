# ---- base: 全ステージ共通の Python 実行環境 + 依存ライブラリ ----
FROM python:3.10-slim AS base

# TZ: 結果ディレクトリ名・実行記録の時刻を JST にする（slim イメージにも zoneinfo は含まれている）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    TZ=Asia/Tokyo

WORKDIR /app

# 依存ライブラリを先にインストール（requirements.txt が変わらない限りキャッシュが効く）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- dev: テスト・静的解析用（runtime には含めない） ----
FROM base AS dev

RUN pip install --no-cache-dir \
    pytest==9.1.1 pytest-cov==7.1.0 pytest-mock==3.15.1 \
    ruff==0.15.22 mypy==2.3.0

COPY pyproject.toml VERSION.txt pytest.ini mypy.ini .ruff.toml ./
COPY masterresearch ./masterresearch
COPY tools ./tools
COPY tests ./tests
RUN pip install --no-cache-dir --no-deps -e .

CMD ["pytest"]

# ---- docs-build: Sphinx で HTML を生成（autodoc のため依存ライブラリ入りの base から派生） ----
FROM base AS docs-build

RUN pip install --no-cache-dir sphinx==8.1.3 furo==2025.12.19

COPY VERSION.txt ./
COPY masterresearch ./masterresearch
COPY tools ./tools
COPY docs ./docs
RUN sphinx-build -W -b html docs/source docs/_build/html

# ---- docs: 生成済み HTML だけを nginx で配信（Python は含まない） ----
FROM nginx:stable-alpine AS docs

COPY --from=docs-build /app/docs/_build/html /usr/share/nginx/html

# ---- runtime: シミュレーション実行用（最終ステージ = --target 省略時のデフォルト） ----
FROM base AS runtime

# ソースは後から COPY（ソース変更時に base の依存レイヤは再利用される）
COPY pyproject.toml VERSION.txt ./
COPY masterresearch ./masterresearch
RUN pip install --no-cache-dir --no-deps .

# 非 root ユーザーで実行（UID 1000 はホストの一般ユーザーと揃えるため）
RUN useradd --uid 1000 --create-home appuser \
    && mkdir -p backLog && chown appuser:appuser backLog
USER appuser

ENTRYPOINT ["masterresearch", "--log-file", "backLog/execution_log.csv"]
