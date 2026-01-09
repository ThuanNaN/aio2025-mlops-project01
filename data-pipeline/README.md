# Data Pipeline MLOps – Customer Churn Feature Store

This repository demonstrates an **end-to-end data pipeline** for a customer churn use case, including:

- Data versioning with **DVC**
- Feature engineering & storage with **Feast**
- Online feature serving with **Redis**

---

## 1. Repository Installation

Clone the repository:

```bash
git clone https://github.com/dangnha/data-pipeline.git
cd data-pipeline
```

---

## 2. Environment Setup

### Option A: Conda (Recommended)

```bash
conda create -n churn_mlops python=3.10 -y
conda activate churn_mlops
```

### Option B: Virtual Environment (venv)

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Data Versioning with DVC

Pull tracked data artifacts:

```bash
dvc pull
```

---

## 5. Feast Feature Store Setup

### 5.1 Apply Feast Repository

```bash
cd churn_feature_store/churn_features/feature_repo
feast apply
```

---

### 5.2 Start Redis (Online Store)

Run Redis using Docker:

```bash
docker run -d -p 6379:6379 --name redis-feast redis:7
```

Verify Redis is running:

```bash
docker ps
```

---

### 5.3 Materialize Features to Online Store

Run incremental materialization using the current timestamp:

```bash
for /f "delims=" %i in ('powershell -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"') do feast materialize-incremental %i
```

---

## 6. Online Feature Retrieval

Return to the project root and run the sample retrieval script:

```bash
python scripts/sample_retrieval.py
```

Expected output:

- Feature values retrieved from Redis
- One row per `customer_id`

---
