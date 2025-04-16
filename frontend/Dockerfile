FROM node:23-slim

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY pnpm-lock.yaml package.json ./
RUN pnpm install

COPY . .

EXPOSE 3000
CMD ["pnpm", "start"]