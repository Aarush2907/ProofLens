FROM node:22-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./

# The browser calls this URL. It must be reachable from the user's machine,
# not the Docker network name of the backend.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build
EXPOSE 3000

CMD ["npm", "start"]
