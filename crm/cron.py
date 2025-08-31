import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/crm_heartbeat_log.txt"
LOW_STOCK_LOG_FILE = "/tmp/low_stock_updates_log.txt"
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

def log_crm_heartbeat():
    # Timestamp
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message = f"{timestamp} CRM is alive"

    # Optional GraphQL check using gql
    try:
        transport = RequestsHTTPTransport(
            url=GRAPHQL_ENDPOINT,
            verify=True,
            retries=3,
        )
        client = Client(transport=transport, fetch_schema_from_transport=True)

        query = gql("{ hello }")
        result = client.execute(query)
        hello_msg = result.get("hello")
        if hello_msg:
            message += f" | GraphQL hello: {hello_msg}"
    except Exception as e:
        message += f" | GraphQL check failed: {e}"

    # Append log
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")

def update_low_stock():
    """Execute UpdateLowStockProducts mutation and log updated products."""
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    message_header = f"{timestamp} Low stock update executed\n"

    # Setup GraphQL client
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL mutation
    mutation = gql("""
        mutation {
            updateLowStockProducts {
                success
                message
                updatedProducts {
                    name
                    stock
                }
            }
        }
    """)

    try:
        result = client.execute(mutation)
        updated_products = result.get("updateLowStockProducts", {}).get("updatedProducts", [])
        
        # Prepare log entries
        log_entries = [message_header]
        for product in updated_products:
            log_entries.append(f"Product: {product['name']}, New Stock: {product['stock']}\n")

        # Append to log file
        with open(LOW_STOCK_LOG_FILE, "a") as f:
            f.writelines(log_entries)

    except Exception as e:
        with open(LOW_STOCK_LOG_FILE, "a") as f:
            f.write(f"{timestamp} Error updating low stock: {e}\n")