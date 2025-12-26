FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

# <-- DAS ist der wichtige Teil:
ENV PYTHONPATH=/app/src

EXPOSE 9000

CMD ["gunicorn", "mini_service.wsgi:application", "--bind", "0.0.0.0:9000", "--workers", "2", "--threads", "4"]