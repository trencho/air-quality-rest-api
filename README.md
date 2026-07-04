# Air Quality REST API (AQRA)

A Flask REST API that collects air-quality and weather data per city/sensor, trains machine-learning
regression models on it, and serves **current readings, history, pollutant metrics, and multi-model
forecasts** — with interactive Swagger docs and prediction/error plots. It currently covers sensors
across North Macedonia (`MK`).

## Feature overview

- **Locations** — list countries and cities, and the sensors within a city (by id or nearest to a
  coordinate).
- **History** — time-series weather or pollution readings for a city/sensor or a coordinate.
- **Pollutants** — the latest per-pollutant values (`AQI, CO, NH3, NO, NO2, O3, PM2.5, PM10, SO2`)
  for a city/sensor or coordinate.
- **Forecasts** — model-driven pollutant predictions for a city, a specific sensor, or a coordinate.
- **Plots** — rendered prediction and error plots per city/sensor/pollutant.
- **Ops** — OpenAPI/Swagger UI, liveness/readiness health checks, CORS, in-process caching, and (in
  prod) an APScheduler pipeline that fetches data, trains models, and publishes forecasts on a cron.

## Tech stack

- **Python** (3.14-slim in the prod image) · **Flask** · **Waitress** (dev) / **Gunicorn + nginx** (prod).
- **flasgger** (OpenAPI/Swagger) · **Flask-Caching** · **Flask-Cors** · **flask-healthz** · **APScheduler**.
- **pandas / numpy / scipy / scikit-learn / statsmodels** and the model backends
  **LightGBM / Random Forest / XGBoost**; **matplotlib / seaborn** for plots.
- **MongoDB** (via **pymongo**) in prod; an in-memory repository in dev. **SQLAlchemy** backs the
  APScheduler job store.
- **Black** (formatting) · **pytest** + **Flask-Testing** (tests).

## API

All routes are prefixed with **`/api/v1`**. Swagger UI: **`/api/v1/apidocs/`**.

| Area       | Endpoint                                                                              |
|------------|---------------------------------------------------------------------------------------|
| Countries  | `GET /countries/`, `GET /countries/<country_code>/`                                    |
| Cities     | `GET /cities/`, `GET /cities/<city_name>/`                                             |
| Sensors    | `GET /cities/<city_name>/sensors/`, `GET /cities/<city_name>/sensors/<sensor_id>/`     |
| History    | `GET /cities/<city_name>/sensors/<sensor_id>/history/<data_type>/` · `GET /coordinates/<lat>,<lon>/history/<data_type>/` |
| Pollutants | `GET /cities/<city_name>/sensors/<sensor_id>/pollutants/` · `GET /coordinates/<lat>,<lon>/pollutants/` |
| Forecast   | `GET /cities/<city_name>/forecast/` · `GET /cities/<city_name>/sensors/<sensor_id>/forecast/` · `GET /cities/coordinates/<lat>,<lon>/forecast/` · `GET /sensors/coordinates/<lat>,<lon>/forecast/` |
| Plots      | `GET /plots/predictions/cities/<city_name>/sensors/<sensor_id>/pollutants/<pollutant>/` · `GET /plots/errors/cities/<city_name>/sensors/<sensor_id>/pollutants/<pollutant>/errors/<error_type>/` |
| Health     | `GET /healthz/live`, `GET /healthz/ready`                                              |

`data_type` is `weather` or `pollution`. The `fetch` and `train` blueprints exist in the source but
are intentionally **not registered** (data fetching and model training run via the scheduler, not HTTP).

## Project structure

```text
definitions.py             # env-var keys, filesystem paths, and constants (POLLUTANTS, REGRESSION_MODELS, URL_PREFIX…)
src/
├── api/
│   ├── app.py             # entry point (waitress serve)
│   ├── config/            # create_app() factory + init_* (blueprints, cache, cors, health, swagger, scheduler, repository…)
│   └── blueprints/        # one dir per resource: <name>.py (+ *.yml flasgger specs) — registered in config/blueprints.py
├── preparation/           # location + weather data fetchers (upstream APIs)
├── processing/            # feature generation / imputation / scaling / selection, forecasting, index calc
├── modeling/              # train + evaluate regression models
├── models/                # model implementations (base + LightGBM / RandomForest / XGBoost enabled)
├── visualization/         # prediction & error plots
└── utils.py
data/  models/  results/   # runtime artifacts (raw location JSON is committed; processed CSVs/models are generated)
docker/  kubernetes/       # deployment
tests/                     # pytest (Flask-Testing) endpoint tests
```

## Architecture

- **App factory** — `src/api/config/__init__.py:create_app()` composes small `init_*` functions
  (logger, GC, system paths, converters, blueprints, cache, CORS, health, swagger, data).
- **Repository** — `config/repository.py` exposes a `Repository` interface with two implementations
  selected by `APP_ENV`: `RegularRepository` (MongoDB) in prod, `InMemoryRepository` in dev/tests.
- **Scheduler** (prod only) — APScheduler cron jobs fetch hourly data, dump/back up data to a Git
  repo, train models, and publish forecasts; the job store is SQLite via SQLAlchemy.
- **Data pipeline** — `preparation` (fetch) → `processing` (clean/feature-engineer) → `modeling`
  (train/evaluate) → forecasts + `visualization` plots.

## Environment configuration

Selected by **`APP_ENV`** (`development` — default — or `production`). In production the app validates
the required variables at startup and exits if any are missing.

| Variable                                                              | Purpose                                             |
|----------------------------------------------------------------------|-----------------------------------------------------|
| `APP_ENV`                                                            | `development` (in-memory repo, no scheduler) or `production` |
| `MONGODB_CONNECTION` / `MONGODB_HOSTNAME` / `MONGO_DATABASE` / `MONGO_USERNAME` / `MONGO_PASSWORD` | MongoDB datasource (prod) |
| `OPEN_WEATHER_TOKEN`                                                 | upstream weather/air-quality API token              |
| `GITHUB_TOKEN` / `REPO_NAME`                                         | data-dump backup to a Git repository (scheduler)    |
| `REDIS_URL`                                                          | optional shared Redis for the cache + rate limiter (multi-worker/pod); falls back to a filesystem cache + in-memory limits when unset |
| `VOLUME_PATH`                                                        | root for `data/`, `logs/`, `models/`, `results/` (defaults to the project dir) |

## Running

### Local (dev)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install --no-cache-dir -r requirements/dev.txt
python src/api/app.py                                   # http://127.0.0.1:5000  (docs at /api/v1/apidocs/)
```

Dev uses the in-memory repository (no MongoDB required) and the committed `data/raw/*.json` seed.

### Docker

```bash
cd docker
cp .env .env.local   # then fill in the values
docker compose up --build
```

## Testing

```bash
pytest            # tests/ run in parallel (-n logical); see pytest.ini
```

The tests are endpoint integration tests (Flask-Testing) run against the in-memory repository. Note
that importing the app triggers `create_app()`, which fetches upstream location data — the suite is
not fully hermetic and needs network access.

## Formatting

```bash
black .           # format
black --check .   # verify (use before committing)
```

## Deployment

Production runs as a **Docker Compose** stack (Flask image + MongoDB) or on **Kubernetes**
(`kubernetes/`: deployments, sealed secrets, cert-manager issuers, MetalLB, ingress-nginx). CI
(`.github/workflows/build-deploy.yml`) connects to the host over OpenVPN + SSH and builds/deploys on
`master`. See `docker/README.md` and `kubernetes/README.md`.
