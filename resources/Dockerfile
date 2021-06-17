FROM node:lts-alpine3.13 as builder

WORKDIR /app
COPY . .

ENV PATH /app/node_modules/.bin:$PATH

RUN npm ci --silent
RUN npm run build


FROM nginx:stable-alpine
WORKDIR /usr/share/nginx/html

RUN mkdir -p resources/guardry

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build ./resources/guardry
