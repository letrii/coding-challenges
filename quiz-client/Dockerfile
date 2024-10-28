FROM node:20-alpine AS base

FROM base AS builder
RUN npm install -g pnpm
RUN apk add --no-cache libc6-compat
RUN apk update

ENV PNPM_HOME=/app/.pnpm
ENV PATH=$PNPM_HOME:$PATH

WORKDIR /app

ADD . .

RUN pnpm install

CMD ["pnpm", "start"]