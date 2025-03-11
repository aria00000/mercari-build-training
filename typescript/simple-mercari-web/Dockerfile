FROM node:20-alpine

# ユーザー作成
RUN addgroup -S mercari && adduser -S trainee -G mercari

WORKDIR /app

COPY package.json package-lock.json .

# 所有者を trainee に変更
RUN chown -R trainee:mercari /app

# ユーザーを切り替え
USER trainee

# npm install を実行
RUN npm ci

COPY . .  

# .vite フォルダの作成と権限変更（root で実行）
USER root
RUN rm -rf /app/node_modules/.vite && mkdir -p /app/node_modules/.vite && chown -R trainee:mercari /app/node_modules/.vite

# .vite-temp フォルダの作成と権限変更
RUN rm -rf /app/node_modules/.vite-temp && mkdir -p /app/node_modules/.vite-temp && chown -R trainee:mercari /app/node_modules/.vite-temp


# ユーザーを戻す
USER trainee

CMD ["npm", "start"]