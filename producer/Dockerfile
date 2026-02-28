FROM python:3.13-slim
RUN pip install --no-cache-dir uv

WORKDIR /app

# 1) Copy only dependency metadata
COPY pyproject.toml uv.lock README.md ./

# 2) Install ONLY third-party dependencies (no project install)
RUN uv sync --frozen --no-dev --no-install-project

# 3) Now copy your source code
COPY src ./src

# 4) Install your project (fast, local)
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "producer"]