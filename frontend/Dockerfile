FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies with strict SSL disabled
# Use --force to reinstall problematic packages
RUN npm config set strict-ssl false && \
    rm -rf node_modules package-lock.json && \
    npm cache clean --force && \
    npm install --force

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Default command (can be overridden in docker-compose.yml)
CMD ["npm", "run", "dev"]

