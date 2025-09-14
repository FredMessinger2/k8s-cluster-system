// Block diagram rendering for Kubernetes cluster visualization

function renderClusterDiagram(data) {
    // Clear previous diagram
    d3.select("#cluster-diagram").selectAll("*").remove();
    
    const container = d3.select("#cluster-diagram");
    const containerRect = container.node().getBoundingClientRect();
    const width = containerRect.width || 800;
    const height = 600;
    
    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height);
    
    // Create tooltip
    const tooltip = d3.select("body").append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);
    
    // Process data into hierarchical structure
    const hierarchyData = processClusterData(data);
    
    if (currentLayout === 'hierarchical') {
        renderHierarchicalLayout(svg, hierarchyData, width, height, tooltip);
    } else {
        renderForceLayout(svg, hierarchyData, width, height, tooltip);
    }
}

function processClusterData(data) {
    const namespaces = {};
    const deployments = {};
    
    // Group pods by namespace
    (data.pods || []).forEach(pod => {
        if (!namespaces[pod.namespace]) {
            namespaces[pod.namespace] = {
                name: pod.namespace,
                type: 'namespace',
                pods: [],
                deployments: {}
            };
        }
        namespaces[pod.namespace].pods.push(pod);
    });
    
    // Group deployments by namespace
    (data.deployments || []).forEach(deployment => {
        if (!namespaces[deployment.namespace]) {
            namespaces[deployment.namespace] = {
                name: deployment.namespace,
                type: 'namespace',
                pods: [],
                deployments: {}
            };
        }
        namespaces[deployment.namespace].deployments[deployment.name] = deployment;
    });
    
    return {
        namespaces: Object.values(namespaces),
        totalPods: data.podCount || 0,
        totalDeployments: data.deploymentCount || 0
    };
}

function renderHierarchicalLayout(svg, data, width, height, tooltip) {
    const margin = { top: 20, right: 20, bottom: 20, left: 20 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Calculate layout
    const namespaceHeight = Math.min(150, innerHeight / Math.max(data.namespaces.length, 1));
    const namespaceWidth = innerWidth - 40;
    
    data.namespaces.forEach((namespace, nsIndex) => {
        const nsY = nsIndex * (namespaceHeight + 20);
        
        // Draw namespace container
        const nsGroup = g.append("g")
            .attr("class", "namespace-group");
        
        nsGroup.append("rect")
            .attr("class", "cluster-node namespace")
            .attr("x", 0)
            .attr("y", nsY)
            .attr("width", namespaceWidth)
            .attr("height", namespaceHeight)
            .attr("rx", 8);
        
        // Namespace title
        nsGroup.append("text")
            .attr("class", "cluster-text title")
            .attr("x", 20)
            .attr("y", nsY + 20)
            .text(`Namespace: ${namespace.name}`);
        
        // Deployment info
        const deploymentCount = Object.keys(namespace.deployments).length;
        nsGroup.append("text")
            .attr("class", "cluster-text subtitle")
            .attr("x", 20)
            .attr("y", nsY + 35)
            .text(`Deployments: ${deploymentCount}, Pods: ${namespace.pods.length}`);
        
        // Draw pods
        const podStartX = 30;
        const podStartY = nsY + 50;
        const podWidth = 80;
        const podHeight = 40;
        const podsPerRow = Math.floor((namespaceWidth - 60) / (podWidth + 10));
        
        namespace.pods.forEach((pod, podIndex) => {
            const row = Math.floor(podIndex / podsPerRow);
            const col = podIndex % podsPerRow;
            const podX = podStartX + col * (podWidth + 10);
            const podY = podStartY + row * (podHeight + 10);
            
            // Pod container
            const podGroup = nsGroup.append("g")
                .attr("class", "pod-group");
            
            podGroup.append("rect")
                .attr("class", `cluster-node pod ${pod.status.toLowerCase()}`)
                .attr("x", podX)
                .attr("y", podY)
                .attr("width", podWidth)
                .attr("height", podHeight)
                .attr("rx", 4)
                .on("mouseover", function(event) {
                    tooltip.transition()
                        .duration(200)
                        .style("opacity", .9);
                    tooltip.html(`
                        <strong>${pod.name}</strong><br/>
                        Status: ${pod.status}<br/>
                        Namespace: ${pod.namespace}<br/>
                        Created: ${formatTimestamp(pod.creationTimestamp)}
                    `)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 28) + "px");
                })
                .on("mouseout", function() {
                    tooltip.transition()
                        .duration(500)
                        .style("opacity", 0);
                });
            
            // Pod name (truncated)
            const truncatedName = pod.name.length > 12 ? 
                pod.name.substring(0, 12) + "..." : pod.name;
            
            podGroup.append("text")
                .attr("class", "cluster-text")
                .attr("x", podX + podWidth/2)
                .attr("y", podY + podHeight/2 - 5)
                .text(truncatedName);
            
            // Pod status
            podGroup.append("text")
                .attr("class", "cluster-text subtitle")
                .attr("x", podX + podWidth/2)
                .attr("y", podY + podHeight/2 + 8)
                .text(pod.status);
        });
    });
    
    // Clean up tooltip on diagram refresh
    setTimeout(() => {
        d3.selectAll(".tooltip").remove();
    }, 100);
}

function renderForceLayout(svg, data, width, height, tooltip) {
    // Create nodes and links for force simulation
    const nodes = [];
    const links = [];
    
    // Add cluster root node
    nodes.push({
        id: 'cluster',
        name: 'Cluster',
        type: 'cluster',
        level: 0
    });
    
    // Add namespace nodes
    data.namespaces.forEach(namespace => {
        const nsId = `ns-${namespace.name}`;
        nodes.push({
            id: nsId,
            name: namespace.name,
            type: 'namespace',
            level: 1,
            data: namespace
        });
        
        links.push({
            source: 'cluster',
            target: nsId
        });
        
        // Add pod nodes
        namespace.pods.forEach((pod, index) => {
            const podId = `pod-${pod.name}`;
            nodes.push({
                id: podId,
                name: pod.name,
                type: 'pod',
                level: 2,
                data: pod
            });
            
            links.push({
                source: nsId,
                target: podId
            });
        });
    });
    
    // Force simulation
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(d => getNodeRadius(d.type) + 5));
    
    // Create links
    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .attr("class", "connection-line");
    
    // Create nodes
    const node = svg.append("g")
        .selectAll("g")
        .data(nodes)
        .enter().append("g")
        .attr("class", "node-group")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
    
    // Add circles for nodes
    node.append("circle")
        .attr("class", d => `cluster-node ${d.type}`)
        .attr("r", d => getNodeRadius(d.type))
        .on("mouseover", function(event, d) {
            if (d.data) {
                tooltip.transition()
                    .duration(200)
                    .style("opacity", .9);
                
                let content = `<strong>${d.name}</strong><br/>Type: ${d.type}`;
                if (d.data.status) {
                    content += `<br/>Status: ${d.data.status}`;
                }
                if (d.data.creationTimestamp) {
                    content += `<br/>Created: ${formatTimestamp(d.data.creationTimestamp)}`;
                }
                
                tooltip.html(content)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
            }
        })
        .on("mouseout", function() {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });
    
    // Add labels
    node.append("text")
        .attr("class", "cluster-text")
        .attr("dy", 4)
        .text(d => d.name.length > 10 ? d.name.substring(0, 10) + "..." : d.name);
    
    // Update positions on simulation tick
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        node
            .attr("transform", d => `translate(${d.x},${d.y})`);
    });
    
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
}

function getNodeRadius(type) {
    switch(type) {
        case 'cluster': return 40;
        case 'namespace': return 30;
        case 'deployment': return 25;
        case 'pod': return 20;
        default: return 15;
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleString();
}
