from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crm.settings")

# Initialize Celery app
app = Celery("crm", broker="redis://localhost:6379/0")

# Load task modules from all registered Django apps
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Celery task {self.request.id} executed")
