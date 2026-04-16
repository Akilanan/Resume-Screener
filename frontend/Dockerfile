FROM node:20-alpine

WORKDIR /app

# Set build arguments BEFORE copying files
ARG VITE_API_URL=http://localhost:8000/api/v1

COPY package*.json ./
RUN npm install

COPY . .

ENV VITE_API_URL=$VITE_API_URL

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
