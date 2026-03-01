# Fidelity Pipeline

End-to-end transaction pipeline with:

- a Python producer that publishes transaction records to Kafka
- a Spring Boot consumer that persists records to PostgreSQL and exposes a REST API
- a React frontend that reads the consumer API and displays transactions
- Prometheus, Grafana, Loki, and Promtail for observability

## Project layout

- [`producer/`](/Users/dylan/source/github/fidelity-pipeline/producer) Python producer for Kafka
- [`consumer/`](/Users/dylan/source/github/fidelity-pipeline/consumer) Spring Boot consumer and API
- [`frontend/`](/Users/dylan/source/github/fidelity-pipeline/frontend) React + Vite frontend
- [`infra/`](/Users/dylan/source/github/fidelity-pipeline/infra) SQL and observability config
- [`docker-compose.yml`](/Users/dylan/source/github/fidelity-pipeline/docker-compose.yml) local multi-service environment

## Services

- `redpanda`: Kafka-compatible broker
- `postgres`: transaction storage
- `producer`: publishes transaction records to Kafka
- `consumer`: consumes Kafka records, writes to Postgres, exposes `GET /api/transactions`
- `frontend`: React UI served by Nginx
- `prometheus`, `grafana`, `loki`, `promtail`: metrics and logs

## Default ports

- Frontend: `http://localhost:5173`
- Consumer API: `http://localhost:8080`
- PostgreSQL: `localhost:5432`
- Redpanda external listener: `localhost:19092`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- Loki: `http://localhost:3100`

## Fastest way to run everything

From the project root:

```bash
docker compose up --build
```

Then open:

```text
http://localhost:5173
```

The frontend calls `/api/transactions`, and the frontend container proxies those requests to the Spring Boot consumer.

## Minimal stack for the UI

If you only want the app path needed for the transaction dashboard:

```bash
docker compose up --build frontend consumer postgres redpanda producer
```

Open:

```text
http://localhost:5173
```

## Local development without full Compose

### Backend

Run the Spring Boot consumer locally:

```bash
cd consumer
./mvnw spring-boot:run
```

The API will be available at:

```text
http://localhost:8080/api/transactions
```

### Frontend

Run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually:

```text
http://localhost:5173
```

In local frontend development, Vite proxies `/api/*` to `http://localhost:8080`.

### Hybrid local setup

A common workflow is:

1. Run `postgres` and `redpanda` in Docker Compose.
2. Run `consumer` locally.
3. Run `frontend` locally.

That keeps the infrastructure containerized while letting you iterate on app code quickly.

## API

Current main endpoint:

- `GET /api/transactions`

Response shape:

```json
[
  {
    "eventId": "evt-123",
    "eventTs": "2026-03-01T10:15:30Z",
    "customerId": "cust-1",
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 10,
    "price": 182.45,
    "sourceFile": "transactions.csv"
  }
]
```

## Notes

- The frontend is the intended primary UI path.
- The consumer still contains a temporary Spring-served static UI under `consumer/src/main/resources/static/`, but that is transitional.
- The consumer uses PostgreSQL `ON CONFLICT DO NOTHING` semantics for idempotent inserts during Kafka consumption.

## Repo-specific docs

- Frontend details: [`frontend/README.md`](/Users/dylan/source/github/fidelity-pipeline/frontend/README.md)
- Producer details: [`producer/README.md`](/Users/dylan/source/github/fidelity-pipeline/producer/README.md)
