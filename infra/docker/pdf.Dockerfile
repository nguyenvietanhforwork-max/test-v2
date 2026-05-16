# Atlas PDF microservice — Puppeteer headless Chrome.
FROM node:20-bookworm-slim

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false

WORKDIR /app

# Chromium deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 \
    libcairo2 libcups2 libdbus-1-3 libdrm2 libexpat1 libgbm1 libglib2.0-0 \
    libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 libxdamage1 \
    libxext6 libxfixes3 libxkbcommon0 libxrandr2 wget \
 && rm -rf /var/lib/apt/lists/*

COPY package.json ./
RUN npm install -g pnpm && pnpm install

COPY . .

EXPOSE 4000
CMD ["pnpm", "start"]
