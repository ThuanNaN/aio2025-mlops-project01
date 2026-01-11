import gradio as gr
import requests
import pandas as pd
import os
import logging
from typing import Tuple
from sample_retrieval import get_customer_features

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8003")


def predict_single(age, gender, tenure, usage_freq, support_calls, 
                   payment_delay, subscription, contract, total_spend, last_interaction) -> str:
    """Single prediction"""
    
    payload = {
        "Age": int(age),
        "Gender": gender,
        "Tenure": int(tenure),
        "Usage_Frequency": int(usage_freq),
        "Support_Calls": int(support_calls),
        "Payment_Delay": int(payment_delay),
        "Subscription_Type": subscription,
        "Contract_Length": contract,
        "Total_Spend": float(total_spend),
        "Last_Interaction": int(last_interaction)
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/predict/", json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        # Safely get churn value
        churn = result.get('churn', 0)
        
        # Format output with clear indication
        if churn == 1:
            output = """
## Prediction: **CHURN**

This customer is predicted to churn.
            """
        else:
            output = """
## Prediction: **ACTIVE**

This customer is predicted to stay active.
            """
        
        return output.strip()
        
    except requests.exceptions.RequestException as e:
        error_detail = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
        return f"**API Error:** {error_detail}"
    except KeyError as e:
        return f"**Error:** Missing field in API response: {str(e)}"
    except Exception as e:
        return f"**Error:** {str(e)}"


def predict_batch(file) -> Tuple[pd.DataFrame, str]:
    """
    Batch prediction from CSV file
    
    Returns:
        (results_df, summary_text)
    """
    if file is None:
        return None, "Please upload a CSV file"
    
    try:
        # Read CSV
        df = pd.read_csv(file.name)
        
        # Validate required columns
        required_cols = [
            'Age', 'Gender', 'Tenure', 'Usage_Frequency', 'Support_Calls',
            'Payment_Delay', 'Subscription_Type', 'Contract_Length', 
            'Total_Spend', 'Last_Interaction'
        ]
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return None, f"Missing columns: {', '.join(missing_cols)}"
        
        # Prepare batch payload
        records = df[required_cols].to_dict('records')
        
        # Call batch API
        response = requests.post(
            f"{API_BASE_URL}/predict/batch", 
            json=records,
            timeout=60
        )
        response.raise_for_status()
        results = response.json()
        
        # Add predictions to dataframe with readable format
        # Safely get churn value from each result
        df['Prediction'] = [r.get('churn', 0) for r in results]
        df['Status'] = df['Prediction'].map({1: 'CHURN', 0: 'ACTIVE'})
        
        # Calculate statistics
        total = len(df)
        churned = sum(df['Prediction'])
        active = total - churned
        churn_rate = churned / total * 100 if total > 0 else 0
        
        summary = f"""
## Batch Prediction Complete!

### Summary Statistics
- **Total Customers:** {total}
- **Predicted Churn:** {churned} ({churn_rate:.1f}%)
- **Predicted Active:** {active} ({100-churn_rate:.1f}%)
        """
        
        return df, summary.strip()
        
    except requests.exceptions.RequestException as e:
        return None, f"**API Error:** {str(e)}"
    except Exception as e:
        return None, f"**Error:** {str(e)}"


def map_feature_store_to_api_format(df: pd.DataFrame) -> dict:
    """
    Map feature store data format to API ChurnInput format
    
    Args:
        df: DataFrame from feature store
        
    Returns:
        Dictionary in ChurnInput format
    """
    if len(df) == 0:
        return None
    
    row = df.iloc[0]
    
    # Map feature store columns to API format
    # Default values if columns don't exist
    payload = {
        "Age": int(row.get('age', row.get('Age', 30))),
        "Gender": str(row.get('gender', row.get('Gender', 'Male'))).capitalize(),
        "Tenure": int(row.get('tenure_months', row.get('Tenure', 12))),
        "Usage_Frequency": int(row.get('usage_frequency', row.get('Usage_Frequency', row.get('avg_monthly_usage', 15)))),
        "Support_Calls": int(row.get('support_calls', row.get('Support_Calls', row.get('support_tickets_90d', 0)))),
        "Payment_Delay": int(row.get('payment_delay', row.get('Payment_Delay', row.get('late_payments_12m', 0)))),
        "Subscription_Type": str(row.get('subscription_type', row.get('Subscription_Type', row.get('plan_type', 'Standard')))).capitalize(),
        "Contract_Length": str(row.get('contract_length', row.get('Contract_Length', row.get('contract_type', 'Monthly')))).capitalize(),
        "Total_Spend": float(row.get('total_spend', row.get('Total_Spend', 500.0))),
        "Last_Interaction": int(row.get('last_interaction', row.get('Last_Interaction', row.get('num_logins_last_30d', 15))))
    }
    
    return payload


def search_customer_data(customer_id: str) -> str:
    """
    Search customer data from feature store, check for NaN, and predict churn
    
    Args:
        customer_id: Customer ID to search
        
    Returns:
        Status message with prediction result
    """
    if not customer_id or customer_id.strip() == "":
        logger.warning("Customer ID is empty")
        return "**Error:** Please enter Customer ID"
    
    try:
        customer_id = customer_id.strip()
        logger.info(f"Searching data for customer_id: {customer_id}")
        
        # Get data from feature store
        logger.info("Calling get_customer_features from sample_retrieval.py...")
        df = get_customer_features(customer_id)
        
        logger.info(f"Retrieved data from feature store. Shape: {df.shape}")
        logger.info(f"Data:\n{df.to_string()}")
        
        # Check for NaN values
        nan_counts = df.isna().sum()
        total_nan = nan_counts.sum()
        
        logger.info("=" * 50)
        logger.info(f"DATA CHECK FOR CUSTOMER ID: {customer_id}")
        logger.info("=" * 50)
        logger.info(f"Number of features: {len(df.columns)}")
        logger.info(f"Total NaN values: {total_nan}")
        
        if total_nan > 0:
            logger.warning("NaN VALUES DETECTED!")
            logger.info("Details of columns with NaN:")
            for col, count in nan_counts.items():
                if count > 0:
                    logger.warning(f"  - {col}: {count} NaN values")
            
            nan_cols = [col for col, count in nan_counts.items() if count > 0]
            return f"""
**Invalid Data**
            """.strip()
        
        # No NaN - proceed with prediction
        logger.info("No NaN values - Data is valid!")
        
        # Map feature store data to API format
        payload = map_feature_store_to_api_format(df)
        
        if payload is None:
            return "**Error:** No data found for this customer ID"
        
        logger.info(f"Mapped payload: {payload}")
        
        # Call prediction API
        try:
            response = requests.post(f"{API_BASE_URL}/predict/", json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            churn = result.get('churn', 0)
            prediction_text = "CHURN" if churn == 1 else "ACTIVE"
            
            logger.info(f"Prediction result for customer {customer_id}: {prediction_text}")
            
            return f"""
**Data Valid - Prediction Complete**

**Customer ID:** {customer_id}
**Prediction:** {prediction_text}

**Details have been logged.**
            """.strip()
            
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                except:
                    error_detail = e.response.text
            logger.error(f"API Error: {error_detail}")
            return f"**API Error:** {error_detail}"
            
    except Exception as e:
        error_msg = f"Error searching data: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"**Error:** {error_msg}"


# Build UI
with gr.Blocks(theme=gr.themes.Soft(), title="Customer Churn Prediction") as demo:
    
    gr.Markdown(
        """
        # Customer Churn Prediction System
        
        ### Powered by XGBoost Machine Learning Model
        
        Predict whether a customer is likely to churn based on their behavior and profile.
        """
    )
    
    with gr.Tabs():
        
        # ========== TAB 1: SINGLE PREDICTION ==========
        with gr.Tab("Single Prediction"):
            gr.Markdown("### Enter customer information to predict churn")
            
            with gr.Row():
                with gr.Column():
                    age = gr.Slider(18, 65, value=30, step=1, label="Age")
                    gender = gr.Radio(["Male", "Female"], value="Female", label="Gender")
                    tenure = gr.Slider(1, 60, value=20, step=1, label="Tenure (months)")
                    usage_freq = gr.Slider(1, 30, value=15, step=1, label="Usage Frequency")
                    support_calls = gr.Slider(0, 10, value=5, step=1, label="Support Calls")
                
                with gr.Column():
                    payment_delay = gr.Slider(0, 30, value=10, step=1, label="Payment Delay (days)")
                    subscription = gr.Dropdown(
                        ["Basic", "Standard", "Premium"], 
                        value="Standard", 
                        label="Subscription Type"
                    )
                    contract = gr.Dropdown(
                        ["Monthly", "Quarterly", "Annual"], 
                        value="Annual", 
                        label="Contract Length"
                    )
                    total_spend = gr.Number(value=500, label="Total Spend ($)")
                    last_interaction = gr.Slider(1, 30, value=15, step=1, label="Days Since Last Interaction")
            
            predict_btn = gr.Button("Predict Churn", variant="primary", size="lg")
            
            with gr.Row():
                single_output = gr.Markdown(label="Prediction Result")
            
            predict_btn.click(
                predict_single,
                inputs=[
                    age, gender, tenure, usage_freq, support_calls, 
                    payment_delay, subscription, contract, total_spend, last_interaction
                ],
                outputs=single_output
            )
        
        # ========== TAB 2: BATCH PREDICTION ==========
        with gr.Tab("Batch Prediction"):
            gr.Markdown(
                """
                ### Upload a CSV file to predict churn for multiple customers
                
                **Required columns:** Age, Gender, Tenure, Usage_Frequency, Support_Calls, 
                Payment_Delay, Subscription_Type, Contract_Length, Total_Spend, Last_Interaction
                """
            )
            
            with gr.Row():
                with gr.Column(scale=1):
                    file_input = gr.File(
                        label="Upload CSV File",
                        file_types=[".csv"],
                        type="filepath"
                    )
                    
                    batch_predict_btn = gr.Button("Run Batch Prediction", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    batch_summary = gr.Markdown(label="Summary")
            
            with gr.Row():
                batch_output = gr.Dataframe(
                    label="Prediction Results",
                    wrap=True,
                    interactive=False
                )
            
            # Batch prediction
            batch_predict_btn.click(
                predict_batch,
                inputs=file_input,
                outputs=[batch_output, batch_summary]
            )
        
        # ========== TAB 3: CUSTOMER DATA CHECK ==========
        with gr.Tab("Customer Data Check"):
            gr.Markdown(
                """
                ### Check Customer Data from Feature Store
                
                Enter Customer ID to retrieve data from feature store, check for NaN values, and predict churn.
                Results will be displayed here and logged.
                """
            )
            
            with gr.Row():
                with gr.Column(scale=1):
                    customer_id_input = gr.Textbox(
                        label="Customer ID",
                        placeholder="Enter Customer ID (e.g., 1, 2, 3...)",
                        value=""
                    )
                    
                    search_btn = gr.Button("Check & Predict", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    search_output = gr.Markdown(label="Result")
            
            # Search customer data
            search_btn.click(
                search_customer_data,
                inputs=customer_id_input,
                outputs=search_output
            )

if __name__ == "__main__":
    print("Starting Gradio UI...")
    print("UI will be available at: http://localhost:7860")
    
    demo.launch(
        server_name="0.0.0.0",
        # server_port=7860,
        server_port=7823,
        share=False  # Set to True to get public URL
    )