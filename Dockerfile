FROM python:3.10-slim

# TZ: 結果ディレクトリ名・実行記録の時刻を JST にする（slim イメージにも zoneinfo は含まれている）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib \
    TZ=Asia/Tokyo

WORKDIR /app

# 依存ライブラリを先にインストール（requirements.txt が変わらない限りキャッシュが効く）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ソースは後から COPY（ソース変更時に上の依存レイヤは再利用される）
COPY pyproject.toml VERSION.txt ./
COPY masterresearch ./masterresearch
RUN pip install --no-cache-dir --no-deps .

# 非 root ユーザーで実行（UID 1000 はホストの一般ユーザーと揃えるため）
RUN useradd --uid 1000 --create-home appuser \
    && mkdir -p backLog && chown appuser:appuser backLog
USER appuser

ENTRYPOINT ["masterresearch", "--log-file", "backLog/execution_log.csv"]
