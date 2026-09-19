docker build -t spam-api:naive -f Dockerfile.naive .
docker build -t spam-api:multistage -f Dockerfile .

check () {   
    docker rm -f q1check > /dev/null 2>&1
    docker run -d --name q1check -p "$2:8080" "$1" > /dev/null
    sleep 5
    curl -s "http://localhost:$2/healthz"; echo ""
    curl -s -X POST "http://localhost:$2/predict" \
         -H 'Content-Type: application/json' \
         -d '{"text":"WIN a FREE iPhone now! Click here: bit.ly/xyz123"}'; echo ""
    curl -s -X POST "http://localhost:$2/predict" \
         -H 'Content-Type: application/json' \
         -d '{"text":"Hey, are we still meeting for lunch on Friday?"}'; echo ""
    docker rm -f q1check > /dev/null
}

check spam-api:naive      8081
check spam-api:multistage 8082

docker images spam-api --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"

N=$(docker image inspect spam-api:naive      --format '{{.Size}}')
M=$(docker image inspect spam-api:multistage --format '{{.Size}}')
python3 -c "
n, m = $N, $M
mb = lambda b: b/1024/1024
print(f'naive       : {mb(n):.0f} MB')
print(f'multi-stage : {mb(m):.0f} MB')
print(f'reduction   : {100*(n-m)/n:.1f} %')
"
