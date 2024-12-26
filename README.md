### README for OpenShift Cluster Health Check Script

---

## Overview

This Python script performs a comprehensive health check for an OpenShift cluster, including key components such as CEPH, OpenShift Data Foundation (ODF), Single Sign-On (SSO), and 3scale API Management. It also gathers node resource usage, NTP status, MTU settings, storage utilization, and inter-node connectivity.

---

## Features

- **CEPH Monitoring**: Checks the status of the CEPH cluster using the `rook-ceph-operator`.
- **ODF Status**: Lists the pods and their states in the `openshift-storage` namespace.
- **SSO and 3scale Status**: Reports the pod states for `openshift-sso` and `3scale` namespaces.
- **Cluster Info**: Retrieves the cluster name and lists all nodes.
- **MTU Verification**: Checks MTU settings for all cluster nodes.
- **Resource Monitoring**: Displays CPU and memory usage for nodes.
- **NTP Verification**: Verifies time synchronization on all nodes.
- **Inter-Node Connectivity**: Checks connectivity between cluster nodes.
- **Storage Utilization**: Displays disk usage details.

---

## Prerequisites

1. **Python**: Ensure Python 3.6+ is installed.
2. **OpenShift CLI (oc)**: The `oc` CLI tool must be installed and configured.
3. **Access Permissions**: The user running the script should have cluster admin privileges.
4. **Python Libraries**: Install the following libraries:
   ```bash
   pip install tabulate
   ```

---

## Usage

### 1. Clone the Repository
Clone the repository or download the script.

### 2. Run the Script
Execute the script using Python:
```bash
python atp-cluster-report.py
```

### 3. Output
The script generates a detailed health check report in a text file. The file is named in the format:
```
<cluster_name>_reporte_<timestamp>.txt
```

The report includes detailed tables with the status of each component and resource.

---

## Example Output

The report will include sections like:
- **NTP Status**: Time synchronization results for all nodes.
- **CEPH Status**: Health status of the CEPH cluster.
- **MTU Settings**: Details about the MTU on each node.
- **Node Resources**: CPU and memory usage for each node.
- **ODF, SSO, and 3scale Status**: Pod statuses for these components.
- **Connectivity Tests**: Ping results between nodes.
- **Storage Utilization**: Disk usage details.

---

## Customization

- **Namespaces**: Update the namespaces for specific components in the script (`openshift-storage`, `openshift-sso`, `3scale`) if they differ in your setup.
- **Output Directory**: Modify the `generar_reporte` function to specify a custom output directory.

---

## Troubleshooting

- **Command Errors**: Ensure the `oc` CLI is configured properly and can connect to the cluster.
- **Permissions**: Verify that the user has adequate permissions to execute debug commands and fetch cluster resources.
- **Dependencies**: Ensure all required Python libraries are installed.

---
