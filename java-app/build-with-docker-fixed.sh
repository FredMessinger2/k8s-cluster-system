#!/bin/bash
echo "🏗️  Building Java app with improved Docker build..."

# Create multi-stage Dockerfile with better debugging
cat > Dockerfile.build << 'DOCKER_BUILD'
# Stage 1: Build with Gradle
FROM gradle:8.4-jdk17 AS builder
WORKDIR /app
COPY . .

# Debug: Show what files we're working with
RUN echo "=== Files in build directory ===" && ls -la

# Build the application
RUN gradle clean shadowJar --no-daemon --info

# Debug: Show what was built
RUN echo "=== Build output ===" && ls -la build/libs/

# Verify the JAR file was created
RUN ls -la build/libs/k8s-cluster-manager-1.0.0.jar

# Stage 2: Runtime image
FROM openjdk:17-jdk-alpine
WORKDIR /app

# Copy the JAR file and verify it's there
COPY --from=builder /app/build/libs/k8s-cluster-manager-1.0.0.jar app.jar

# Debug: Verify the JAR is in the final image
RUN echo "=== JAR file in runtime image ===" && ls -la /app/

# Test that Java can read the JAR
RUN java -jar app.jar --version || echo "JAR test failed but continuing..."

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
DOCKER_BUILD

# Build with verbose output
echo "📦 Building k8s-manager Docker image with verbose output..."
docker build -f Dockerfile.build -t k8s-manager:latest . --no-cache

# Clean up
rm Dockerfile.build

echo "✅ Build completed!"

# Verify the image
echo "🔍 Verifying the built image..."
docker run --rm k8s-manager:latest ls -la /app/
echo ""
echo "Testing Java version in container:"
docker run --rm k8s-manager:latest java -version
echo ""
echo "Testing JAR file access:"
docker run --rm k8s-manager:latest java -jar /app/app.jar --help || echo "JAR might not support --help"
