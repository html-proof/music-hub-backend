FROM node:20-slim

WORKDIR /app
# Install production dependencies
COPY package*.json ./
RUN npm config delete production && npm ci --omit=dev

# Copy source
COPY . .

# Railway injects PORT at runtime
EXPOSE 8080

# Basic health check against local HTTP endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD sh -c "node -e \"const http=require('http');const p=process.env.PORT||8080;http.get('http://127.0.0.1:'+p+'/health',res=>process.exit(res.statusCode===200?0:1)).on('error',()=>process.exit(1));\""

CMD ["node", "server.js"]
