FROM openjdk:17-jdk-alpine
VOLUME /tmp

# Copy the shadow JAR (contains all dependencies)
COPY build/libs/k8s-cluster-manager-1.0.0.jar app.jar

# Expose port 8080
EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "/app.jar"]
