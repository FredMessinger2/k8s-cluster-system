package com.k8smanager;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import com.k8smanager.service.KubernetesService;
import com.k8smanager.service.NatsService;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.Map;
import java.util.HashMap;

public class K8sManagerApplication {
    private static KubernetesService kubernetesService;
    private static NatsService natsService;
    private static ObjectMapper objectMapper;

    public static void main(String[] args) throws Exception {
        // Configure ObjectMapper with JSR310 module
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
        
        kubernetesService = new KubernetesService();
        natsService = new NatsService(kubernetesService);
        
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        
        server.createContext("/api/cluster/info", new ClusterInfoHandler());
        server.createContext("/api/nats/publish", new NatsPublishHandler());
        server.createContext("/health", new HealthHandler());
        
        server.setExecutor(null);
        server.start();
        
        System.out.println("K8s Manager Server started on port 8080");
        System.out.println("Endpoints:");
        System.out.println("  GET /api/cluster/info - Get cluster information");
        System.out.println("  POST /api/nats/publish - Publish to NATS topic");
        System.out.println("  GET /health - Health check");
        
        // Shutdown hook to clean up NATS connection
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            try {
                natsService.close();
            } catch (Exception e) {
                System.err.println("Error closing NATS connection: " + e.getMessage());
            }
        }));
    }

    static class ClusterInfoHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
            exchange.getResponseHeaders().add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            exchange.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type");
            
            if ("OPTIONS".equals(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(200, -1);
                return;
            }
            
            if ("GET".equals(exchange.getRequestMethod())) {
                try {
                    Map<String, Object> clusterInfo = kubernetesService.getClusterInfo();
                    
                    // Publish cluster info access event to NATS
                    Map<String, Object> event = new HashMap<>();
                    event.put("action", "cluster_info_accessed");
                    event.put("timestamp", System.currentTimeMillis());
                    event.put("podCount", clusterInfo.get("podCount"));
                    natsService.publishEvent("k8s.events", event);
                    
                    String jsonResponse = objectMapper.writeValueAsString(clusterInfo);
                    
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(200, jsonResponse.length());
                    
                    OutputStream os = exchange.getResponseBody();
                    os.write(jsonResponse.getBytes());
                    os.close();
                } catch (Exception e) {
                    String errorResponse = "{\"error\":\"" + e.getMessage().replaceAll("\"", "'") + "\"}";
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(500, errorResponse.length());
                    
                    OutputStream os = exchange.getResponseBody();
                    os.write(errorResponse.getBytes());
                    os.close();
                }
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }
    
    static class NatsPublishHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
            exchange.getResponseHeaders().add("Access-Control-Allow-Methods", "POST, OPTIONS");
            exchange.getResponseHeaders().add("Access-Control-Allow-Headers", "Content-Type");
            
            if ("OPTIONS".equals(exchange.getRequestMethod())) {
                exchange.sendResponseHeaders(200, -1);
                return;
            }
            
            if ("POST".equals(exchange.getRequestMethod())) {
                try {
                    // Read request body
                    String requestBody = new String(exchange.getRequestBody().readAllBytes());
                    
                    // Default to k8s.events topic if not specified
                    String topic = "k8s.events";
                    String message = requestBody;
                    
                    // Parse JSON if it contains topic
                    try {
                        Map<String, Object> request = objectMapper.readValue(requestBody, Map.class);
                        if (request.containsKey("topic")) {
                            topic = (String) request.get("topic");
                        }
                        if (request.containsKey("message")) {
                            message = objectMapper.writeValueAsString(request.get("message"));
                        }
                    } catch (Exception e) {
                        // Use raw body as message
                    }
                    
                    // Publish to NATS
                    natsService.publishEvent(topic, message);
                    
                    String response = "{\"status\":\"published\",\"topic\":\"" + topic + "\"}";
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(200, response.length());
                    
                    OutputStream os = exchange.getResponseBody();
                    os.write(response.getBytes());
                    os.close();
                } catch (Exception e) {
                    String errorResponse = "{\"error\":\"" + e.getMessage().replaceAll("\"", "'") + "\"}";
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    exchange.sendResponseHeaders(500, errorResponse.length());
                    
                    OutputStream os = exchange.getResponseBody();
                    os.write(errorResponse.getBytes());
                    os.close();
                }
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }
    
    static class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
            
            if ("GET".equals(exchange.getRequestMethod())) {
                String response = "{\"status\":\"healthy\",\"service\":\"k8s-manager\",\"nats\":\"connected\"}";
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.length());
                
                OutputStream os = exchange.getResponseBody();
                os.write(response.getBytes());
                os.close();
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
        }
    }
}
