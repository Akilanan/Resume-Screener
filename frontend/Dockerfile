FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Expose Vite's default port
EXPOSE 5173

# Run Vite dev server, allowing external connections
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
