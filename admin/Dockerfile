# Next.js Frontend Dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat curl
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY package.json package-lock.json* ./
RUN npm ci --prefer-offline --no-audit --progress=false

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules

# Copy package files first
COPY package.json package-lock.json* ./

# Copy configuration files (these change less frequently)
COPY next.config.ts tsconfig.json postcss.config.js prettier.config.js eslint.config.mjs jsvectormap.d.ts ./

# Copy source code (this changes more frequently)
COPY src ./src
COPY public ./public

# Build the application
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_OPTIONS="--max-old-space-size=4096"
ENV NEXT_BUILD_WORKERS=1
ENV NEXT_PUBLIC_API_URL=https://royalprompts.online:8443

# Build with error handling
RUN npm run build || (echo "Build failed, trying with more memory..." && NODE_OPTIONS="--max-old-space-size=8192" npm run build)

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=https://royalprompts.online:8443

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy built application
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

CMD ["node", "server.js"]
