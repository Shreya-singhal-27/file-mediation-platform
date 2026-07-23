# File Mediation and Transformation Platform

The **File Mediation and Transformation Platform** is a robust, modular, and configurable data pipeline designed to ingest, decode, filter, transform, and transmit data files across different protocols and formats. It is built as a FastAPI application in Python, utilizing SQLAlchemy for persistent storage, Alembic for migrations, and Pydantic for settings and schema validation.

---

## 🚀 Key Features

*   **Multi-Protocol File Ingestion (Acquisition)**: Pull files from local paths, FTP servers, or SFTP servers.
*   **Flexible Format Decoding**: Support for CSV, ASN.1 (BER encoded `.dat`), Pipe-separated (and `.txt`), and Fixed-Width format decoding.
*   **Dynamic Filtering Engine**: Configurable, condition-based filtering rules using logical operator evaluation (e.g., `=`, `!=`, `>`, `<`, etc.).
*   **Configurable Data Transformation**: Map fields, convert types (Boolean conversion, string defaults), and formats (Date formatting, Number formatting).
*   **Reliable File Transmission**: Delivery of processed outputs to local directories, FTP, or SFTP destinations.
*   **Job & Event Log Audit Trail**: Automatic creation of jobs showing stage transitions (`ACQUISITION` ➔ `DECODING` ➔ `FILTERING` ➔ `TRANSFORMING` ➔ `TRANSMITTING` ➔ `COMPLETED` / `FAILED`), record-level statistics, performance tracking, and event logs.
*   **Full OpenAPI REST App**: Endpoints to manage roles, users, source-configs, destination-configs, transformation rules, and run pipeline executables manually.

---

## 🏗️ Architecture & Component Design

The platform uses a layered architecture, dividing concerns between the **API layer**, the **Business Domain logic**, the **Persistence layer**, and the core **Service engines**.

### Project Structure

```text
├── alembic/                # DB Schema migration scripts
├── app/
│   ├── api/                # FastAPI HTTP routes (Auth, Filtering, Pipeline, Transform)
│   ├── business/           # Domain business operations (job, pipeline services)
│   ├── core/               # App configuration (JWT, settings, Logger, security)
│   ├── database/           # SQLAlchemy DB setup & session lifespans
│   ├── models/             # SQLAlchemy ORM models (AuditLog, Pipeline, Job, etc.)
│   ├── repositories/       # Database access objects / repository decorators
│   ├── schemas/            # Pydantic validation schemas
│   ├── services/           # Processing Engines
│   │   ├── acquisition/    # File pull (Local, FTP, SFTP)
│   │   ├── audit/          # Recording system actions & pipeline run statuses
│   │   ├── decoder/        # Decoding logic (CSV, Pipe, Fixed Width, ASN.1 BER)
│   │   ├── filtering/      # Engine translating conditions to filtering rules
│   │   ├── pipeline/       # Orchestration pipeline context, executor, and engine
│   │   ├── transformation/ # Field mapping, formatting, and validation engine
│   │   └── transmission/   # File push (Local, FTP, SFTP) e2e delivery
│   ├── utils/              # Parsing, coercion, and file utilities
│   ├── config.py           # Pydantic Settings implementation
│   ├── dependencies.py     # FastAPI Injection dependencies (DB, services, auth)
│   └── main.py             # App entrypoint & lifecycles
├── configs/                # Reference JSON configs for sources, mappings, destinations
├── tests/                  # Integration and Unit tests
└── docker-compose.yml / Dockerfile # Deployment definitions
```

### Pipeline Flow Diagram

```mermaid
graph TD
    A[Acquisition: FTP/SFTP/Local] -->|Raw File| B[Decoding: Parse CSV/ASN/Pipe/FixedWidth]
    B -->|Decoded Dict Records| C[Filtering: Evaluate Rules & Field Operators]
    C -->|Accepted Records| D[Transformation: Field Map, Date/Number Formatting & Coercion]
    D -->|Transformed Records| E[Transmission: Deliver Output File to Destination]
    E -->|Success/Failure| F[Auditing & Job Logs: Record Stats & State Changes]
```

---

## ⚙️ Configuration (.env)

The environment parameters are loaded dynamically via `pydantic-settings` from the `.env` file at the root.

To configure the application, create a `.env` file at the root using the following template:

```env
APP_NAME=File Mediation and Transformation Platform
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=false

API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=["*"]
CORS_ALLOW_HEADERS=["*"]

# Database configuration (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://postgres:yourPassword@localhost:5432/file_mediation

# Logging Setup
LOG_LEVEL=INFO
LOG_PATH=logs/application.log

# Authentication Secrets
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

---

## 🛠️ Setup & Installation

### Prerequisites
*   Python 3.10+
*   PostgreSQL Database (for local use or containerized)

### Step-by-Step Installation

1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd file-mediation-platform
    ```

2.  **Set Up a Virtual Environment & Activate**:
    *   **Windows**:
        ```powershell
        python -m venv venv
        .\venv\Scripts\activate
        ```
    *   **Linux/macOS**:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Database Migrations**:
    Apply database schema migrations using Alembic:
    ```bash
    alembic upgrade head
    ```

---

## 🚀 Running the Application

### Local Development
To launch the API server locally:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

*   **Interactive OpenAPI Documentation (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
*   **Alternative Schema Documentation (Redoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🔌 REST API Endpoints Summary

Below is an overview of the core REST routes available:

| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :---: |
| **POST** | `/api/v1/auth/register` | Register a new system user | No |
| **POST** | `/api/v1/auth/login` | Login to retrieve JWT Access Token | No |
| **POST** | `/api/v1/auth/refresh` | Refresh an authorization access token | No |
| **POST** | `/api/v1/pipelines` | Configure a new mediation pipeline | Yes |
| **GET** | `/api/v1/pipelines` | Retrieve list of configured pipelines | No |
| **GET** | `/api/v1/pipelines/{pipeline_id}` | Fetch a pipeline setup by id | No |
| **PUT** | `/api/v1/pipelines/{pipeline_id}` | Update pipeline configurations | Yes |
| **DELETE** | `/api/v1/pipelines/{pipeline_id}`| Remove a pipeline definition | Yes |
| **GET** | `/health` | Application health-check & DB check | No |

---

## 🧩 Pipeline Workflows & Engines

When a pipeline runs, data goes through a series of dedicated processing engines:

### 1. File Acquisition
The acquisition engine (`App/services/acquisition/`) fetches incoming records from a designated source.
*   **LOCAL**: Reads files from directories locally.
*   **FTP / SFTP**: Authenticates with remote repositories and down-streams requested formats into temporary paths.

### 2. Decoding
The `DecoderFactory` instantiates the decoder matching the file extension:
*   **CSVDecoder (`.csv`)**: Processes standard CSV format.
*   **PipeDecoder (`.pipe`, `.txt`)**: Processes pipe-delimited data.
*   **FixedWidthDecoder (`.fw`)**: Slices characters based on strict column length definitions.
*   **ASN1Decoder (`.dat`)**: Parses ASN.1 BER structures into readable schemas.

### 3. Rule-Based Filtering
Filters use operators like `=`, `!=`, `>`, `<`, etc., mapped to `FilterCondition` structures. Records that do not meet the criteria are split, updating count statistics, and saved to `rejected` folders.

### 4. Transformation
Mapping configurations instruct how to transform source keys into final target fields:
*   **COPY**: Direct copy of the value.
*   **BOOLEAN_CONVERSION**: Direct boolean transformations (normalizes values like "yes"/"no", "true"/"false").
*   **DATE_FORMAT**: Formats and parses date-times between input and output formats.
*   **NUMBER_FORMAT**: Normalizes floats/decimals/integers.

### 5. Transmission
Output files are written into the target location depending on the destination config details.

---

## 🧪 Testing

The project uses `pytest` for all automation, including unit and integration tests.

### Running All Tests
To run all tests in the workspace:
```bash
pytest
```

To run tests with verbose logging:
```bash
pytest -v
```

### End-To-End Integration Test
The E2E suite (`tests/test_end_to_end_pipeline.py`) validates the full mediation flow:
1. Generates local directory structures.
2. Injects fixtures for role, user, local source/destination paths, and pipeline setup.
3. Defines a pipeline with filters (e.g. `status = ACTIVE`) and mappings.
4. Generates an input `.csv` file.
5. Invokes `PipelineEngine().execute()`.
6. Validates the output dataset, checksum, database state metrics, and audit logs.
