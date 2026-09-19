# AI Use Disclosure

Raghava · DA24B021 · AIOps Module 3
The AI assistant I used for this assignment is Claude-Opus
I used an AI assistant for:

- **Template code.** Starting points for the Dockerfiles, the Compose file, the
  Job and Deployment manifests.
- **Writing and formatting the markdown and LaTeX files.** The README, this
  file, and the layout of the report.
- **Debugging.** Working out what was wrong when things failed:
  - `ModuleNotFoundError: No module named 'redis'` in the Compose stack, from a
    `requirements.txt` that was missing the dependency
  - curl returning timings in the tens of microseconds, which turned out to be
    the API not being up and the timings measuring how fast curl failed
  - `ErrImagePull` on every Job pod, caused by `minikube docker-env` not working
    on multi-node clusters so the image never reached the nodes
  - `0/2 nodes are available: 2 Insufficient cpu`, from CPU requests that did
    not account for what kube-system pods had already reserved
  - minikube starting with 6 CPUs per node instead of 2, because `--cpus` is
    only read at cluster creation and the old profile overrode it
  - a `JSONDecodeError` when collecting results, from a log line that was a
    Python dict repr rather than JSON
