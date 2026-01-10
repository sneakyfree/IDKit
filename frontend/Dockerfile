# IDKit Frontend Dockerfile
# Multi-stage build for optimized production image

# =============================================================================
# Dependencies Stage
# =============================================================================
FROM node:20-alpine AS deps

# Check for required build args
ARG NEXT_PUBLIC_API_URL

WORKDIR /app

# Install dependencies based on lockfile
COPY package.json package-lock.json* ./
RUN npm ci --only=production=false

# =============================================================================
# Builder Stage
# =============================================================================
FROM node:20-alpine AS builder

ARG NEXT_PUBLIC_API_URL
ARG BUILD_DATE
ARG GIT_SHA

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8000}
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# =============================================================================
# Production Stage
# =============================================================================
FROM node:20-alpine AS production

WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Set environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Copy built assets from builder
COPY --from=builder /app/public ./public

# Copy standalone output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Build arguments for versioning
ARG BUILD_DATE
ARG GIT_SHA

# Set labels for image metadata
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${GIT_SHA}" \
    org.opencontainers.image.title="IDKit Frontend" \
    org.opencontainers.image.description="IDKit Frontend Application"

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start the application
CMD ["node", "server.js"]
