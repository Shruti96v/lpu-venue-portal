# Stage 1: Build the React application
FROM node:20-alpine AS builder

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm ci

COPY . .

# Set Vite API URL to /api so it calls the Nginx reverse proxy
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy build artifacts to Nginx html directory
COPY --from=builder /usr/src/app/dist /usr/share/nginx/html

# Copy the Nginx configuration template for environment variable replacement at startup
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# Default backend URL for local compose networking
ENV BACKEND_URL=http://backend:5005

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
