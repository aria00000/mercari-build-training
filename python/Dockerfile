FROM alpine

RUN apk add --no-cache python3 py3-pip && ln -sf python3 /usr/bin/python

RUN addgroup -S mercari && adduser -S trainee -G mercari
#RUN chown -R trainee:mercari /path/to/db

# 作業ディレクトリを設定
WORKDIR /app

# 必要な依存関係をコピー
COPY .. /app
# 仮想環境の作成
RUN python3 -m venv /app/venv

# 仮想環境に必要なパッケージをインストール
RUN /app/venv/bin/pip install -r /app/requirements.txt

# アプリケーションコードをコピー


# 仮想環境でmain.pyを実行するためのCMD
CMD ["/app/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]

