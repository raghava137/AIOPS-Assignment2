"""Collects each shard's invalid-row count by reading pod logs through the
Kubernetes API.

Why the API and not a shared volume: minikube's default storage provisioner
(standard / hostPath) binds a PersistentVolume to whichever node first claims
it. On a multi-node cluster the Job's pods are spread across nodes, so a pod
scheduled onto a different node than the one holding the volume cannot read or
write it reliably. Pod stdout has no such constraint: the kubelet on each node
captures it locally and the API server serves it back on request, so results
come home regardless of where the pod ran.

  python collect_results.py
  python collect_results.py --job shard-validation --namespace default
"""

import argparse
import json

from kubernetes import client, config


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--job", default="shard-validation")
    p.add_argument("--namespace", default="default")
    args = p.parse_args()

    config.load_kube_config()
    v1 = client.CoreV1Api()

    pods = v1.list_namespaced_pod(
        namespace=args.namespace,
        label_selector=f"job-name={args.job}",
    ).items
    print(f"Found {len(pods)} pods for job/{args.job}\n")

    results = []
    for pod in pods:
        name = pod.metadata.name
        phase = pod.status.phase
        if phase != "Succeeded":
            print(f"skipping {name}: phase={phase}")
            continue

        # this is the API call that replaces a shared volume
        log = v1.read_namespaced_pod_log(name=name, namespace=args.namespace)

        for line in log.strip().splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    results.sort(key=lambda r: r["shard_index"])

    print(f"{'shard':>5}  {'rows':>5}  {'invalid':>7}  {'valid':>6}  {'node':<22} {'pod'}")
    print("-" * 95)
    for r in results:
        print(f"{r['shard_index']:>5}  {r['total_rows']:>5}  {r['invalid_rows']:>7}  "
              f"{r['valid_rows']:>6}  {r['node_name']:<22} {r['pod_name']}")

    total_invalid = sum(r["invalid_rows"] for r in results)
    total_rows = sum(r["total_rows"] for r in results)
    print("-" * 95)
    print(f"{'TOTAL':>5}  {total_rows:>5}  {total_invalid:>7}  {total_rows - total_invalid:>6}")

    nodes = {}
    for r in results:
        nodes[r["node_name"]] = nodes.get(r["node_name"], 0) + 1
    print(f"\npods per node: {nodes}")

    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Wrote results.json")


if __name__ == "__main__":
    main()
