geoviewer backend

Make sure to copy .env file before deploying

if deployed locally
```bash
# get dictionary from the yaml file in geoviewer-db. I'll improve this later.
TENANT_DSN_MAP='{"brandweer_zhz":"postgresql://postgres:postgres@host.docker.internal:5432/postgres?sslmode=disable","vik":"postgresql://postgres:postgres@host.docker.internal:5432/postgres?sslmode=disable"}' \
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

test on browser:
Test on browser:
https://geoviewer-api.onrender.com/tenants/brandweer_zhz/layers/

http://localhost:8000/tenants/brandweer_zhz/layers/

TODOs:
Add endpoint for viewers
Add endpoint for authentication
Set up Docker properly for the API
