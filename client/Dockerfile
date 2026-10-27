# Build Stage
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Serve Stage via lightweight Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Custom nginx config to support React SPA client-side routing & API proxy
RUN printf 'server {\n\
    listen 80;\n\
    location / {\n\
        root /usr/share/nginx/html;\n\
        index index.html;\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
    location /api/ {\n\
        proxy_pass http://api:8000/api/;\n\
        proxy_set_header Host $host;\n\
        proxy_set_header X-Real-IP $remote_addr;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
