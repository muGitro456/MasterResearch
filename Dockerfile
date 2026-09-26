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
