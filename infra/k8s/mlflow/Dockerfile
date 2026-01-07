FROM ghcr.io/mlflow/mlflow:v3.8.1

# Install PostgreSQL driver and AWS SDK for S3 compatibility
RUN pip install --no-cache-dir \
    psycopg2-binary==2.9.9 \
    boto3==1.34.84

# Set working directory
WORKDIR /mlflow

# Expose MLflow port
EXPOSE 5000

# Default command (can be overridden)
CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000"]
