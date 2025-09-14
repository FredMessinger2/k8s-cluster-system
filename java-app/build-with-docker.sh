#!/bin/bash
echo "🏗️  Building Java app using Docker (no local Gradle needed)..."

# Create multi-stage Dockerfile for building
cat > Dockerfile.build << 'DOCKER_BUILD'
# Stage 1: Build with Gradle
FROM gradle:8.4-jdk17 AS builder
WORKDIR /app
COPY . .
RUN gradle clean shadowJar --no-daemon

# Stage 2: Runtime image
FROM openjdk:17-jdk-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/k8s-cluster-manager-1.0.0.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app.jar"]
DOCKER_BUILD

# Build the Docker image
echo "📦 Building k8s-manager Docker image..."
docker build -f Dockerfile.build -t k8s-manager:latest .

# Clean up
rm Dockerfile.build

echo "✅ Java application built successfully!"
