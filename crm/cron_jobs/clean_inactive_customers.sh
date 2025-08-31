#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/../.."

# Detect Python executable
PYTHON=$(command -v python3 || command -v python)

# Run Django shell command to delete inactive customers
DELETED_COUNT=$($PYTHON manage.py shell -c "
import datetime
from crm.models import Customer
from django.utils import timezone

one_year_ago = timezone.now() - datetime.timedelta(days=365)

# Customers with no orders in the past year
inactive_customers = Customer.objects.exclude(orders__order_date__gte=one_year_ago)

count = inactive_customers.count()
inactive_customers.delete()
print(count)
")

# Log result with timestamp
echo \"$(date '+%Y-%m-%d %H:%M:%S') - Deleted customers: $DELETED_COUNT\" >> /tmp/customer_cleanup_log.txt
