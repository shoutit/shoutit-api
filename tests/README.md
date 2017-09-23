Tests
=====

#### Run locally
```bash
py.test --reuse-db --cov=src
```


#### Run inside docker

```bash
docker-compose --file docker-compose.test.yml up --build --abort-on-container-exit
```
