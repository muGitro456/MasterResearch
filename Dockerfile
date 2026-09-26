# Phase 1: 最小構成。Phase 2 の比較基準とするため、あえて最適化していない
FROM python:3.10

WORKDIR /app
COPY . .
RUN pip install .

# 実行記録 CSV もマウント先の backLog/ に出す（コンテナ破棄で消えないように）
ENTRYPOINT ["masterresearch", "--log-file", "backLog/execution_log.csv"]
