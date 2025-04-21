FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py collectstatic --noinput
COPY . .
EXPOSE 8000

CMD ["gunicorn", "customer_app.wsgi:application", "--bind", "0.0.0.0:8000"]