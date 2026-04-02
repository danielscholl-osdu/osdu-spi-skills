---
title: Agents
description: Specialist agents and their capabilities
---

## Overview

Agents are specialist execution contexts that handle complex, domain-specific operations. The default assistant delegates to them when the task requires deep domain knowledge.

## @osdu — Platform Orchestrator

**Scope:** OSDU platform services on GitLab (`community.opengroup.org/osdu/platform`).

**When to use:** Builds, test runs, dependency remediation, complex multi-step platform operations.

**Skills:**
| Skill | Purpose |
|-------|---------|
| maven | Java builds and dependency management |
| dependencies | Dependency analysis and risk scoring |
| build-runner | Build execution with structured output |
| acceptance-test | Java tests against live environments |
| osdu-qa | QA test execution, environments, reporting |
| fossa | FOSSA NOTICE file fixes |
| maintainer | Trusted branch sync for MR review |

**Sub-agents:** @osdu orchestrates QA workflows through specialized sub-agents:

| Sub-agent | Purpose |
|-----------|---------|
| qa-runner | Parallel test execution across environments |
| qa-analyzer | Root cause analysis of test failures |
| qa-comparator | Cross-environment result comparison |
| qa-reporter | QA dashboards and formatted reports |

## @cimpl — CIMPL Infrastructure

**Scope:** `cimpl-azure-provisioning` repository only.

**When to use:** Terraform modules, Helm charts, AKS configuration, `azd` provisioning, deployment debugging, infrastructure verification.

**Skills:**
| Skill | Purpose |
|-------|---------|
| iac | Terraform, AVM, Helm, AKS Safeguards |
| health | AZD environment + cluster health |
| setup | CLI dependency checking |

**Deployment layers:**
| Layer | Path | Technology |
|-------|------|-----------|
| L1 Infrastructure | `infra/` | Terraform + AVM modules |
| L2 Platform | `software/foundation/` | Terraform + Helm |
| L3 Software | `software/stack/` | Helm + Kustomize |

## @spi — SPI Infrastructure

**Scope:** `osdu-spi-infra` and `osdu-spi-*` fork repositories on GitHub.

**When to use:** Azure PaaS Terraform (CosmosDB, Service Bus, Storage, Key Vault), fork lifecycle management, three-branch strategy, upstream sync, cascade integration.

**Skills:**
| Skill | Purpose |
|-------|---------|
| iac | Terraform, Azure PaaS, Helm, azd |
| health | Environment + Azure PaaS resource health |
| forks | Three-branch fork lifecycle |
| status | Cross-repo dashboard |
| setup | CLI dependency checking |

**Fork repos (8 services):**

| Service | Upstream (GitLab) |
|---------|-------------------|
| Partition | `osdu/platform/system/partition` |
| Entitlements | `osdu/platform/security-and-compliance/entitlements` |
| Legal | `osdu/platform/security-and-compliance/legal` |
| Schema | `osdu/platform/system/schema-service` |
| File | `osdu/platform/system/file` |
| Storage | `osdu/platform/system/storage` |
| Indexer | `osdu/platform/system/indexer-service` |
| Search | `osdu/platform/system/search-service` |

## Shared Skills

These skills are available to all contexts — the default assistant and all agents:

`brain`, `briefing`, `learn`, `consolidate`, `glab`, `send`, `mr-review`, `contribute`, `clone`, `setup`, `osdu-activity`, `osdu-engagement`, `osdu-quality`, `osdu-data-load`

## Cross-Plugin Routing

When context is ambiguous between CIMPL and SPI:

| Signal | Routes to |
|--------|-----------|
| `cimpl-azure-provisioning` in path | @cimpl |
| `osdu-spi-infra` in path | @spi |
| GitHub context (`gh` CLI) | @spi |
| GitLab context (`glab` CLI) | @cimpl or @osdu |
| Azure PaaS (CosmosDB, Service Bus) | @spi |
| In-cluster middleware (RabbitMQ, MinIO) | @cimpl |
| Fork management | @spi |
