FROM python:3.10
WORKDIR /
RUN pip install --no-cache-dir --upgrade fastapi uvicorn
COPY app.py app.py
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
