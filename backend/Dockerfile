FROM python:3.11.9-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY main_test.py main.py
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]