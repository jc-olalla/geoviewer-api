geoviewer backend

```bash
# get dictionary from the yaml file in geoviewer-db. I'll improve this later.
TENANT_DSN_MAP='{"brandweer":"postgresql://postgres:postgres@host.docker.internal:5432/brandweer_catalog","vik":"postgresql://postgres:postgres@host.docker.internal:5432/vik_catalog"}' \
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

TODOs:
Add endpoint for viewers
Add endpoint for authentication
Set up Docker properly for the API
