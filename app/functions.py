import os

def load_configuration():
    return (
        os.getenv("BASE_URL", "http://localhost"),
        os.getenv("API_KEY"),
    )