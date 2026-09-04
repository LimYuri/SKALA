# 빌드 스테이지
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .

ARG VITE_API_BASE_URL=http://localhost:8080
ARG VITE_AUTH_SERVER_URL=/auth
ARG VITE_CLIENT_ID=web-client
ARG VITE_CLIENT_SECRET=web-secret
ARG VITE_REDIRECT_URI=http://localhost:3000/callback
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_AUTH_SERVER_URL=${VITE_AUTH_SERVER_URL} \
    VITE_CLIENT_ID=${VITE_CLIENT_ID} \
    VITE_CLIENT_SECRET=${VITE_CLIENT_SECRET} \
    VITE_REDIRECT_URI=${VITE_REDIRECT_URI}

RUN npm run build

# 서빙 스테이지
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
