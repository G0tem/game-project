FROM python:3.10
WORKDIR /
RUN pip install --no-cache-dir --upgrade fastapi uvicorn httpx
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
