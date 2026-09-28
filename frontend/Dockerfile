FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Empty VITE_API_URL => same-origin /api via nginx proxy (Compose + Railway private net)
# Or set VITE_API_URL=https://your-api.up.railway.app to call the API directly
ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine
RUN apk add --no-cache gettext
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
COPY --from=build /app/dist /usr/share/nginx/html
ENV PORT=80
ENV API_UPSTREAM=api:8000
EXPOSE 80
ENTRYPOINT ["/docker-entrypoint.sh"]
