package com.k8smanager;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import com.k8smanager.service.KubernetesService;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.Map;

public class K8sManagerApplication {
    private static KubernetesService kubernetesService;
    private static ObjectMapper objectMapper;

    public static void main(String[] args) throws Exception {
        // Configure ObjectMapper with JSR310 module
        objectMapper = new ObjectMapper();
        objectMapper.registerModule(new JavaTimeModule());
        
        kubernetesService = new KubernetesService();
        
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        
        server.createContext("/api/cluster/info", new ClusterInfoHandler());
        server.createContext("/health", new HealthHandler());
        
        server.setExecutor(null);
        server.start();
        
        System.out.println("K8s Manager Server started on port 8080");
        System.out.println("Endpoints:");
        System.out.println("  GET /api/cluster/info - Get cluster information");
        System.out.println("  GET /health - Health check");
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
    
    static class HealthHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            exchange.getResponseHeaders().add("Access-Control-Allow-Origin", "*");
            
            if ("GET".equals(exchange.getRequestMethod())) {
                String response = "{\"status\":\"healthy\",\"service\":\"k8s-manager\"}";
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
