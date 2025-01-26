FROM python:3.10
WORKDIR /
RUN pip install --no-cache-dir --upgrade fastapi uvicorn
COPY main.py main.py
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]