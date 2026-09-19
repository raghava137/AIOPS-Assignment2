"""Reads each pod's stdout through the Kubernetes API and prints the results."""

import ast

from kubernetes import client, config

config.load_kube_config()
v1 = client.CoreV1Api()

pods = v1.list_namespaced_pod(
    namespace="default", label_selector="job-name=shard-validation"
).items

results, skipped = [], []
for pod in pods:
    log = v1.read_namespaced_pod_log(name=pod.metadata.name, namespace="default")
    for line in log.strip().splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        # literal_eval reads both JSON and a plain Python dict repr
        try:
            results.append(ast.literal_eval(line))
        except (ValueError, SyntaxError):
            skipped.append((pod.metadata.name, line))

if skipped:
    print("lines that could not be parsed:")
    for name, line in skipped:
        print(f"  {name}: {line[:120]}")
    print()

results.sort(key=lambda r: r["shard"])

print(f"{'shard':>5} {'rows':>6} {'invalid':>8}  {'node':<16} pod")
for r in results:
    print(f"{r['shard']:>5} {r['total_rows']:>6} {r['invalid_rows']:>8}  "
          f"{r['node']:<16} {r['pod']}")

print(f"\nshards: {len(results)}/8   total invalid: "
      f"{sum(r['invalid_rows'] for r in results)}")

nodes = {}
for r in results:
    nodes[r["node"]] = nodes.get(r["node"], 0) + 1
print(f"pods per node: {nodes}")