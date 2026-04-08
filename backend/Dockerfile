FROM python:3.14-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY backend/ ./backend/

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8000"]
