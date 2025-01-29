FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# Add verbose pip install to see what's happening
RUN pip install --no-cache-dir -r requirements.txt --verbose

COPY ./app /app/app

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
