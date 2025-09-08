FROM node:18-alpine as build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM node:18-alpine as stage-1
RUN apk add --no-cache curl
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/vite.config.ts ./

HEALTHCHECK --interval=30s --timeout=10s --retries=3 CMD curl -f http://localhost:5173/ || exit 1

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
