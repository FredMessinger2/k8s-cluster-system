#!/bin/bash
echo "Building Java app with fixed dependencies..."

cat > Dockerfile.quick << 'DOCKER_BUILD'
# Stage 1: Build with Gradle
FROM gradle:8.4-jdk17 AS builder
WORKDIR /app
COPY . .
RUN gradle clean shadowJar --no-daemon

# Stage 2: Runtime image
FROM openjdk:17-jdk-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/k8s-cluster-manager-1.0.0.jar app.jar

# Just verify the file exists, don't run it
RUN ls -la /app/app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
DOCKER_BUILD

# Build the image
echo "Building Docker image..."
docker build -f Dockerfile.quick -t k8s-manager:latest . --no-cache

# Clean up
rm Dockerfile.quick

echo "Build completed!"
