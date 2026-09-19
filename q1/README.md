# Q1 — Single-stage vs. multi-stage Docker

Spam-detection API: TF-IDF + MultinomialNB behind FastAPI.

## Files

```
generate_dataset.py    the assignment's dataset script, unchanged
train_model.py         trains the pipeline, writes model.joblib
app.py                 FastAPI service: POST /predict, GET /healthz
requirements.txt       pinned dependencies
Dockerfile.naive       single-stage build
Dockerfile             multi-stage build
.dockerignore          keeps the CSV and training scripts out of the context
build_and_measure.sh   builds both, verifies both, prints sizes and % reduction
```

## Running it

```bash
python generate_dataset.py
python train_model.py
bash build_and_measure.sh
```

The script builds both images, starts each one, checks `/healthz` and
`/predict` actually respond, then prints the size comparison and the evidence
for the written explanation.

## Manually

```bash
docker build -t spam-api:naive -f Dockerfile.naive .
docker build -t spam-api:multistage -f Dockerfile .
docker images spam-api

docker run -d -p 8080:8080 --name spam spam-api:multistage
curl localhost:8080/healthz
curl -X POST localhost:8080/predict \
    -H "Content-Type: application/json" \
    -d '{"text":"WIN a FREE iPhone now! Click here: bit.ly/xyz123"}'
docker rm -f spam
```

## Results

| Image | Size |
|---|---|
| `spam-api:naive` | ___ MB |
| `spam-api:multistage` | ___ MB |
| Reduction | ___ % |

## Why the multi-stage image is smaller

Fill this in from your own build output. Be specific, the rubric asks for what
was left behind in **this** image rather than a textbook definition. The
`build_and_measure.sh` output gives you the evidence: base image sizes, whether
`gcc` survives into each image, whether a pip cache is present, and the layer
breakdown from `docker history`.

## Note on model accuracy

The classifier scores 1.00 on the held-out split. That is expected rather than
suspicious: the dataset is generated from six spam and six ham templates with
no shared vocabulary, so the classes are linearly separable by design. The
assignment says as much, the modelling is deliberately trivial so the Docker
and Kubernetes work is the actual task.
