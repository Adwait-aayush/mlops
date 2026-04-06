
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json .
RUN npm install

COPY public/ public/
COPY src/ src/

RUN npm run build

FROM nginx:alpine


COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 3000


RUN echo 'server { listen 3000; location / { root /usr/share/nginx/html; try_files $uri /index.html; } }' \
    > /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]