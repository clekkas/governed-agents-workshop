# Container image for the code-first agent service.
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV HOST=0.0.0.0
ENV PORT=8081

WORKDIR /app

COPY requirements-foundry.txt requirements.txt ./
RUN pip install --no-cache-dir -r requirements-foundry.txt

COPY src/ ./src/

EXPOSE 8081
CMD ["sh", "-c", "uvicorn discharge_transition_agent.app:app --host ${HOST} --port ${PORT}"]
