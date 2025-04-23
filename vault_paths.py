"""
Configuration file for Vault paths. Because who doesn't love a good organization system? 📁
"""

VAULT_PATHS = {
    "helios": {
        "prod": [
            "kv/engineering/v1/airflow/data-engineering/cie-inference",
            "kv/engineering/v1/airflow/data-engineering/helios",
            "kv/engineering/v1/airflow/data-engineering/model-service",
            "kv/engineering/v1/c2fo-chat/data-engineering/chat-env",
            "kv/engineering/ec2/data-engineering/atlas-spark-apps/helios",
            "kv/engineering/ec2/data-engineering/helios/secrets"
        ],
        "non_prod": [
            "kv/engineering/v1/fss-c2fo-chat/data-engineering/chat-env"
        ]
    },
    "pricing": {
        "prod": [
            "kv/engineering/v1/dummy-shadow-pricing-service/data-engineering/pricing-env",
            "kv/engineering/v1/nmr-shadow-pricing-service/data-engineering/pricing-env",
            "kv/engineering/v1/pricing-service/data-engineering/pricing-env",
            "kv/engineering/v1/prod-pricing-service/data-engineering/pricing-env",
            "kv/engineering/v1/ps-shadow-pricing-service/data-engineering/pricing-env",
            "kv/engineering/v1/shadow-pricing-service/data-engineering/pricing-env"
        ],
        "non_prod": [
            "kv/engineering/v1/fss-pricing-service/data-engineering/pricing-env"
        ]
    }
}

def get_paths(app: str, env: str) -> list:
    """
    Get vault paths for a specific app and environment.
    Like a GPS for your secrets! 🗺️
    """
    if app not in VAULT_PATHS:
        raise ValueError(f"App '{app}' not found! Did it go on vacation? 🏖️")
    
    if env not in VAULT_PATHS[app]:
        raise ValueError(f"Environment '{env}' not found! Are we in a parallel universe? 🌌")
    
    return VAULT_PATHS[app][env]

def get_available_apps() -> list:
    """
    Get list of available apps.
    Like a menu at a fancy restaurant! 🍽️
    """
    return list(VAULT_PATHS.keys())

def get_available_envs(app: str) -> list:
    """
    Get list of available environments for an app.
    Like checking the weather before going out! ⛅
    """
    if app not in VAULT_PATHS:
        raise ValueError(f"App '{app}' not found! Did it get lost in the cloud? ☁️")
    
    return list(VAULT_PATHS[app].keys())