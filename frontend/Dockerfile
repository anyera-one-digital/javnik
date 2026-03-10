# ===========================================
# Frontend Dockerfile (Production)
# ===========================================

# Stage 1: Build
FROM node:20-alpine AS builder

RUN apk add --no-cache python3 make g++

RUN corepack enable && corepack prepare pnpm@10.26.1 --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm rebuild better-sqlite3

ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NODE_ENV=production

#ARG NUXT_PUBLIC_API_BASE_URL=/api
#ARG API_BASE_URL=http://backend:8000

#ENV NUXT_PUBLIC_API_BASE_URL=${NUXT_PUBLIC_API_BASE_URL}
#ENV API_BASE_URL=${API_BASE_URL}

RUN pnpm build

# Stage 2
FROM node:20-alpine

WORKDIR /app

ENV NODE_ENV=production
ENV NUXT_HOST=0.0.0.0
ENV NUXT_PORT=3000

COPY --from=builder /app/.output ./.output
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]