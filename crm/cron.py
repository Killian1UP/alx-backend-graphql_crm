import datetime
import requests

LOG_FILE = "/tmp/crm_heartbeat_log.txt"
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

def log_crm_heartbeat():
    # Timestamp in requested format
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    # Base message
    message = f"{timestamp} CRM is alive"

    # Optional GraphQL check
    try:
        response = requests.post(
            GRAPHQL_ENDPOINT,
            json={"query": "{ hello }"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            hello_msg = data.get("data", {}).get("hello")
            if hello_msg:
                message += f" | GraphQL hello: {hello_msg}"
    except Exception as e:
        message += f" | GraphQL check failed: {e}"

    # Append log entry
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
