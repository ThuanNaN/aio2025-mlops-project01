from feast import FeatureStore
import pandas as pd
import os
from typing import Union, List

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_path = os.path.join(project_root, "churn_feature_store", "churn_features", "feature_repo")

FEATURES = [
    # ---------- customer_demographics ----------
    "customer_demographics:age",
    "customer_demographics:gender",
    "customer_demographics:tenure_months",
    "customer_demographics:subscription_type",
    "customer_demographics:contract_length",
    # ---------- customer_behavior ----------
    "customer_behavior:usage_frequency",
    "customer_behavior:support_calls",
    "customer_behavior:payment_delay_days",
    "customer_behavior:total_spend",
    "customer_behavior:last_interaction_days",
]


def get_customer_features(customer_id: Union[int, str, List[Union[int, str]]]) -> pd.DataFrame:
    """
    Get features from feature store for customer_id or list of customer_ids
    
    Args:
        customer_id: Customer ID (int, str) or list of customer IDs
        
    Returns:
        DataFrame containing features
    """
    store = FeatureStore(repo_path=repo_path)
    
    # Convert customer_id to list if single value
    if not isinstance(customer_id, list):
        customer_ids = [customer_id]
    else:
        customer_ids = customer_id
    
    # Prepare entity rows
    entity_rows = []
    for cid in customer_ids:
        try:
            # Try to convert to int if possible
            cid_int = int(cid)
            entity_rows.append({"customer_id": cid_int})
        except (ValueError, TypeError):
            # If not int, use as string
            entity_rows.append({"customer_id": str(cid)})
    
    # Get features from feature store
    df = store.get_online_features(
        entity_rows=entity_rows,
        features=FEATURES,
    ).to_df()
    print(f"Features for customer_id: {customer_id} - Shape: {df.shape}")
    return df


# Main execution when run as script
if __name__ == "__main__":
    entity_rows = [{"customer_id": i} for i in range(2, 40)]
    store = FeatureStore(repo_path=repo_path)
    df = store.get_online_features(
        entity_rows=entity_rows,
        features=FEATURES,
    ).to_df()
    print(df)


# from feast import FeatureStore
# import pandas as pd
# import os

# project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# repo_path = os.path.join(project_root, "churn_feature_store", "churn_features", "feature_repo")

# store = FeatureStore(repo_path=repo_path)

# entity_rows = [{"customer_id": i} for i in range(2, 40)]

# FEATURES = [
#     # ---------- customer_demographics ----------
#     "customer_demographics:age",
#     "customer_demographics:gender",
#     "customer_demographics:tenure_months",
#     "customer_demographics:subscription_type",
#     "customer_demographics:contract_length",
#     # ---------- customer_behavior ----------
#     "customer_behavior:usage_frequency",
#     "customer_behavior:support_calls",
#     "customer_behavior:payment_delay_days",
#     "customer_behavior:total_spend",
#     "customer_behavior:last_interaction_days",
# ]

# df = store.get_online_features(
#     entity_rows=entity_rows,
#     features=FEATURES,
# ).to_df()

# print(df)
