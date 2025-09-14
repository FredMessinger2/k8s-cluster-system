package com.k8smanager.service;

import io.nats.client.Connection;
import io.nats.client.Nats;
import io.nats.client.Message;
import io.nats.client.Subscription;
import io.nats.client.Dispatcher;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.Map;
import java.util.HashMap;

public class NatsService {
    private Connection natsConnection;
    private ObjectMapper objectMapper;
    private KubernetesService kubernetesService;
    private Dispatcher dispatcher;
    
    public NatsService(KubernetesService kubernetesService) throws Exception {
        this.kubernetesService = kubernetesService;
        this.objectMapper = new ObjectMapper();
        this.objectMapper.registerModule(new JavaTimeModule());
        
        // Connect to NATS server
        String natsUrl = System.getenv("NATS_URL");
        if (natsUrl == null) {
            natsUrl = "nats://nats-service:4222";
        }
        
        this.natsConnection = Nats.connect(natsUrl);
        System.out.println("Connected to NATS at: " + natsUrl);
        
        // Create dispatcher for handling messages
        this.dispatcher = natsConnection.createDispatcher();
        
        // Set up subscriptions
        setupSubscriptions();
        
        // Start publishing cluster info periodically
        startPeriodicPublishing();
    }
    
    private void setupSubscriptions() throws Exception {
        // Subscribe to requests for cluster info
        dispatcher.subscribe("k8s.cluster.info.request", (msg) -> {
            try {
                System.out.println("Received cluster info request");
                Map<String, Object> clusterInfo = kubernetesService.getClusterInfo();
                String response = objectMapper.writeValueAsString(clusterInfo);
                
                if (msg.getReplyTo() != null) {
                    natsConnection.publish(msg.getReplyTo(), response.getBytes(StandardCharsets.UTF_8));
                }
            } catch (Exception e) {
                System.err.println("Error handling cluster info request: " + e.getMessage());
            }
        });
        
        // Subscribe to general events
        dispatcher.subscribe("k8s.events", (msg) -> {
            String data = new String(msg.getData(), StandardCharsets.UTF_8);
            System.out.println("Received k8s event: " + data);
        });
        
        // Subscribe to commands
        dispatcher.subscribe("k8s.commands", (msg) -> {
            String command = new String(msg.getData(), StandardCharsets.UTF_8);
            System.out.println("Received command: " + command);
            handleCommand(command, msg.getReplyTo());
        });
        
        System.out.println("NATS subscriptions established");
    }
    
    private void handleCommand(String command, String replyTo) {
        try {
            Map<String, Object> response = new HashMap<>();
            
            switch (command) {
                case "status":
                    response.put("status", "healthy");
                    response.put("service", "k8s-manager");
                    break;
                case "cluster-info":
                    response = kubernetesService.getClusterInfo();
                    break;
                default:
                    response.put("error", "Unknown command: " + command);
            }
            
            if (replyTo != null) {
                String responseJson = objectMapper.writeValueAsString(response);
                natsConnection.publish(replyTo, responseJson.getBytes(StandardCharsets.UTF_8));
            }
        } catch (Exception e) {
            System.err.println("Error handling command: " + e.getMessage());
        }
    }
    
    private void startPeriodicPublishing() {
        CompletableFuture.runAsync(() -> {
            while (!Thread.currentThread().isInterrupted()) {
                try {
                    Thread.sleep(30000); // 30 seconds
                    
                    Map<String, Object> status = new HashMap<>();
                    status.put("timestamp", System.currentTimeMillis());
                    status.put("service", "k8s-manager");
                    status.put("status", "running");
                    
                    String statusJson = objectMapper.writeValueAsString(status);
                    natsConnection.publish("app.status", statusJson.getBytes(StandardCharsets.UTF_8));
                    
                    // Also publish cluster metrics
                    Map<String, Object> clusterInfo = kubernetesService.getClusterInfo();
                    Map<String, Object> metrics = new HashMap<>();
                    metrics.put("podCount", clusterInfo.get("podCount"));
                    metrics.put("deploymentCount", clusterInfo.get("deploymentCount"));
                    metrics.put("timestamp", System.currentTimeMillis());
                    
                    String metricsJson = objectMapper.writeValueAsString(metrics);
                    natsConnection.publish("k8s.metrics", metricsJson.getBytes(StandardCharsets.UTF_8));
                    
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    System.err.println("Error publishing periodic updates: " + e.getMessage());
                }
            }
        });
    }
    
    public void publishEvent(String subject, Object data) throws Exception {
        String json = objectMapper.writeValueAsString(data);
        natsConnection.publish(subject, json.getBytes(StandardCharsets.UTF_8));
    }
    
    public void close() throws Exception {
        if (natsConnection != null) {
            natsConnection.close();
        }
    }
}
