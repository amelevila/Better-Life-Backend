FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --no-deps

# Copiar el resto del código del proyecto
COPY . .

# Exponer el puerto del backend
EXPOSE 8000

# Comando para arrancar el servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
