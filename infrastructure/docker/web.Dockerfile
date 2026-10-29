# STDevsec Trading Lab web image.
FROM node:20-alpine

WORKDIR /app

# Root workspace manifest + the two JS workspace members.
COPY package.json package-lock.json* ./
COPY apps/web ./apps/web
COPY packages/shared-contracts ./packages/shared-contracts

RUN npm install
RUN npm run build --workspace apps/web

EXPOSE 3000
CMD ["npm", "run", "start", "--workspace", "apps/web"]
