---
name: health
allowed-tools: Bash, Read, Glob
description: >-
  Comprehensive health assessment of deployed environments — cluster
  infrastructure, Azure PaaS resources, workloads, and OSDU platform services.
  Supports both CIMPL (AKS-only) and SPI (AKS + Azure PaaS) environments.
  Use when the user asks about environment health, cluster status, Azure PaaS
  health, CosmosDB status, Service Bus health, or wants a report on their
  deployed environments. Trigger on phrases like "report on my environments",
  "environment health", "how is my cluster", "cluster status", "is CosmosDB
  healthy", "environment status", or "what's deployed".
  Not for: deploying or modifying infrastructure (use the iac skill), fork
  management (use the forks skill), installing tools (use the setup skill).
---

# Environment Health Report

Comprehensive health assessment of deployed AZD environments — cluster infrastructure,
Azure PaaS resources, workloads, and OSDU platform services.

## The Iron Law

```
EVERY HEALTH REPORT MUST USE LIVE DATA — NEVER ASSUME STATUS
```

Connect to the actual cluster and query real endpoints. Cached or assumed status is worthless.

## Quick Start

```bash
kubectl version --client && az version
```
If either is not found, **stop and use the `setup` skill**.

## Report Procedure

Follow phases in order. Do NOT skip phases — partial reports must be clearly labeled as incomplete.

### Phase 1: Enumerate Environments

```bash
# List azd environments
ls -d .azure/*/

# For each, extract key config
grep -E "^(AZURE_ENV_NAME|AZURE_LOCATION|AZURE_RESOURCE_GROUP|AZURE_AKS_CLUSTER_NAME)" .azure/<env>/.env
```

Present a summary table:

| Environment | Location | Resource Group | AKS Cluster |
|-------------|----------|---------------|-------------|

**Detect environment type:** Check for Azure PaaS resources to determine CIMPL vs SPI:
```bash
RG="<resource-group>"
PAAS_COUNT=$(az cosmosdb list -g "$RG" --query "length(@)" -o tsv 2>/dev/null || echo "0")
if [ "$PAAS_COUNT" -gt 0 ]; then
  echo "SPI environment detected (Azure PaaS resources found)"
else
  echo "CIMPL environment detected (AKS-only)"
fi
```

### Phase 2: Connect to Cluster

```bash
az aks get-credentials -g <resource-group> -n <cluster-name>
kubelogin convert-kubeconfig -l azurecli
```

If connection fails, report the failure and skip to next environment.

### Phase 3: Cluster Infrastructure Health

```bash
# Node status
kubectl get nodes -o wide

# Pod health
kubectl get pods -A --no-headers | grep -v Running | grep -v Completed

# Resource pressure
kubectl top nodes 2>/dev/null || echo "Metrics server not available"
```

### Phase 4: Azure PaaS Health (SPI environments only)

**Skip this phase for CIMPL environments** (no PaaS resources).

```bash
RG="<resource-group>"

# CosmosDB accounts
az cosmosdb list -g "$RG" --query "[].{name:name, kind:kind, state:provisioningState}" -o table

# Service Bus namespaces
az servicebus namespace list -g "$RG" --query "[].{name:name, status:status}" -o table

# Storage accounts
az storage account list -g "$RG" --query "[].{name:name, status:statusOfPrimary, kind:kind}" -o table

# Key Vault
az keyvault list -g "$RG" --query "[].{name:name, state:properties.provisioningState}" -o table
```

**Per-partition checks:**
```bash
# CosmosDB SQL databases per partition
for acct in $(az cosmosdb list -g "$RG" --query "[?kind=='GlobalDocumentDB' && !contains(capabilities[].name, 'EnableGremlin')].name" -o tsv); do
  echo "=== $acct ==="
  az cosmosdb sql database list --account-name "$acct" -g "$RG" --query "[].{name:id}" -o table
done

# Service Bus topics per partition
for ns in $(az servicebus namespace list -g "$RG" --query "[].name" -o tsv); do
  TOPIC_COUNT=$(az servicebus topic list --namespace-name "$ns" -g "$RG" --query "length(@)" -o tsv 2>/dev/null || echo "?")
  echo "$ns: $TOPIC_COUNT topics"
done
```

### Phase 5: Workload Health

```bash
# Helm releases
helm list -A --no-headers 2>/dev/null

# Key namespace status (adjust namespaces per environment type)
# CIMPL: osdu-system, airflow, cert-manager, ingress-nginx, monitoring
# SPI: platform, osdu, osdu-core, osdu-reference, airflow, cert-manager
for ns in osdu-system platform osdu osdu-core airflow cert-manager; do
  echo "=== $ns ==="
  kubectl get pods -n "$ns" --no-headers 2>/dev/null | awk '{print $3}' | sort | uniq -c
done

# Gateway / Ingress
kubectl get gateway -A 2>/dev/null
kubectl get httproute -A 2>/dev/null
kubectl get ingress -A 2>/dev/null

# Certificates
kubectl get certificates -A 2>/dev/null
```

### Phase 6: OSDU Platform Health

Use the OSDU MCP server tools if available:
- `osdu_health_check` with `include_services: true`
- `osdu_partition_list`
- `osdu_search_query` (kind `*:*:*:*`, limit 1)
- `osdu_entitlements_mine`

**Do NOT attempt to probe OSDU endpoints directly via curl or kubectl port-forward.** The OSDU MCP server handles authentication, SSL, and endpoint resolution.

If MCP server is not configured, skip and note:
> OSDU platform API health check skipped — MCP server not connected.

### Phase 7: Summary

```
## Environment Health: <env-name> (<CIMPL|SPI>)

Overall: Healthy / Degraded / Unhealthy

### Infrastructure
- Nodes: X/Y Ready
- K8s: vX.Y.Z
- Pods: X running, Y failing

### Azure PaaS (SPI only)
- CosmosDB: X accounts (all Succeeded / N degraded)
- Service Bus: X namespaces (all Active / N degraded)
- Storage: X accounts (all available / N degraded)
- Key Vault: Accessible / Inaccessible

### OSDU Services
- X/Y services healthy
- Key issues: [list any]

### Action Items
- [Any recommended actions]
```

## Red Flags

| Signal | Meaning |
|--------|---------|
| Nodes NotReady | Cluster infrastructure problem |
| Pods in CrashLoopBackOff | Application/config failure |
| CosmosDB provisioningState != Succeeded | Database provisioning issue (SPI) |
| Service Bus status != Active | Messaging disrupted (SPI) |
| Storage statusOfPrimary != available | Object storage outage (SPI) |
| OSDU auth failure | Keycloak/identity issue |
| Certificates not ready | TLS/ingress will fail |

## Integration

- Issues found → suggest `iac` skill to investigate
- After fixes → re-run health check to verify
