#!/bin/bash
echo "Building Java app with NATS support..."

cat > Dockerfile.quick << 'DOCKER_BUILD'
FROM gradle:8.4-jdk17 AS builder
WORKDIR /app
COPY . .
RUN gradle clean shadowJar --no-daemon

FROM openjdk:17-jdk-alpine
WORKDIR /app
COPY --from=builder /app/build/libs/k8s-cluster-manager-1.0.0.jar app.jar
RUN ls -la /app/app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
DOCKER_BUILD

docker build -f Dockerfile.quick -t k8s-manager:latest . --no-cache
rm Dockerfile.quick
echo "Build completed!"
