# Puppeteer needs a real Chromium; this base image bundles it.
FROM ghcr.io/puppeteer/puppeteer:23.4.0

WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev || true
COPY . .
RUN npm install && npm run build
EXPOSE 4000
CMD ["node", "dist/server.js"]
