# Frontend dev/preview server for the local stack (web shell; desktop build uses Tauri natively).
FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
