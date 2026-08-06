# Stage 1: Build & dependency installation
FROM node:20-alpine AS builder

WORKDIR /usr/src/app

# Copy package descriptors
COPY package*.json ./

# Install only production dependencies
RUN npm ci --only=production

# Stage 2: Slim production runner
FROM node:20-alpine

WORKDIR /usr/src/app

# Copy node_modules from builder and source code
COPY --from=builder /usr/src/app/node_modules ./node_modules
COPY . .

# Set default production ports and node environment
ENV PORT=5005
ENV NODE_ENV=production

EXPOSE 5005

# Setup a lightweight container health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:5005/health || exit 1

CMD ["node", "server.js"]
