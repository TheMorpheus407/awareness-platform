FROM node:20-alpine

WORKDIR /app

# Install dependencies for better caching
COPY package*.json ./
RUN npm ci --only=production

# Copy application code
COPY . .

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001 && \
    chown -R nodejs:nodejs /app

USER nodejs

# Expose port
EXPOSE 5173

# Default command
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]