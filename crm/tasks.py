import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/crm_report_log.txt"

@shared_task
def generate_crm_report():
    """Fetch CRM stats via GraphQL and log them."""
    # Setup GraphQL client
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # GraphQL query to fetch total customers, orders, and revenue
    query = gql("""
        query {
            totalCustomers: allCustomers {
                totalCount
            }
            totalOrders: allOrders {
                totalCount
                edges {
                    node {
                        totalAmount
                    }
                }
            }
        }
    """)

    try:
        result = client.execute(query)

        # Total customers
        total_customers = result.get("totalCustomers", {}).get("totalCount", 0)

        # Total orders
        total_orders = result.get("totalOrders", {}).get("totalCount", 0)

        # Total revenue
        edges = result.get("totalOrders", {}).get("edges", [])
        total_revenue = sum(edge["node"]["totalAmount"] for edge in edges)

        # Log report
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n"
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)

    except Exception as e:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp} - Error generating report: {e}\n")
