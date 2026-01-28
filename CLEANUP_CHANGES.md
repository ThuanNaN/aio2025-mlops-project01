# Cleanup Changes Log

---

## 1. Files đã xóa

### 1.1 `serving_pipeline/test.py`

### 1.2 `data-pipeline/scripts/sample_retrieval.py`
- **Lý do**: Code trùng lặp với `serving_pipeline/sample_retrieval.py`

---

## 2. Code dư thừa đã xóa

### 2.1 `serving_pipeline/sample_retrieval.py`
- **Vị trí**: Lines 74-105 (cuối file)

### 2.2 `model_pipeline/src/scripts/train.py`
- **Vị trí**: Lines 9-12
- **Nội dung đã xóa**: Import trùng lặp
  ```python
  # Đã xóa (trùng lặp):
  import pandas as pd
  import yaml
  from loguru import logger
  ```

### 2.3 `model_pipeline/src/model/xgboost_trainer.py`
- **Vị trí**: Lines 229-238 (cuối file)
- **Nội dung đã xóa**: Method `load_model()` đã comment out
  ```python
  # def load_model(self, model_uri: str):
  #     """Load a trained model from MLflow"""
  #     ...
  ```
- **Lý do**: Code không còn sử dụng, đã có cách load model khác thông qua MLflow

### 2.4 `model_pipeline/src/mlflow_utils/experiment_tracker.py`
---

## 3. Refactoring đã thực hiện

### 3.1 Environment Variables

**Vấn đề**: Các file scripts có hardcoded environment variables.

**Giải pháp đã áp dụng**:

1. **Tạo file `.env.example`** tại `model_pipeline/.env.example`:
   ```env
   AWS_ACCESS_KEY_ID=minio
   AWS_SECRET_ACCESS_KEY=minio123
   AWS_DEFAULT_REGION=us-east-1
   MLFLOW_S3_ENDPOINT_URL=http://localhost:9000
   ```

2. **Thêm function `load_env()`** vào `model_pipeline/src/utility/helper.py`:
   ```python
   from dotenv import load_dotenv
   
   def load_env(env_path: str | None = None) -> None:
       """Load environment variables from .env file"""
       # Auto-detect .env location or use .env.example as fallback
   ```

3. **Cập nhật các scripts** để sử dụng `load_env()`:
   - `model_pipeline/src/scripts/train.py`
   - `model_pipeline/src/scripts/eval.py`
   - `model_pipeline/src/scripts/register_model.py`

**Cách sử dụng**:
```bash
# Copy .env.example thành .env và chỉnh sửa nếu cần
cp model_pipeline/.env.example model_pipeline/.env

# Các scripts sẽ tự động load từ .env
python -m src.scripts.train --config config/random_forest.yaml
```
---
