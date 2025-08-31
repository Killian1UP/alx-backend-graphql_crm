#!/usr/bin/env python3
import sys
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

LOG_FILE = "/tmp/order_reminders_log.txt"
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"

def main():
    # Setup GraphQL client
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Calculate date 7 days ago
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()

    # GraphQL query (adjust field names if needed)
    query = gql("""
        query GetRecentOrders($date: DateTime!) {
            orders(orderDate_Gte: $date) {
                id
                customer {
                    email
                }
            }
        }
    """)

    try:
        result = client.execute(query, variable_values={"date": seven_days_ago})
        orders = result.get("orders", [])

        with open(LOG_FILE, "a") as f:
            for order in orders:
                order_id = order["id"]
                email = order["customer"]["email"]
                log_entry = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} - Order ID: {order_id}, Customer Email: {email}\n"
                f.write(log_entry)

        print("Order reminders processed!")

    except Exception as e:
        print(f"Error processing order reminders: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
