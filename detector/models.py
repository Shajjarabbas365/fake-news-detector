from django.db import models
from django.contrib.auth.models import User


class ScanRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # User who performed the scan
    scanned_text = models.TextField()  # Text that was analyzed
    result_label = models.CharField(max_length=50)  # FAKE NEWS or REAL NEWS
    confidence_score = models.FloatField()  # Confidence percentage
    created_at = models.DateTimeField(auto_now_add=True)  # Date and time when the scan was performed

    def __str__(self):
        # This will appear in the Django admin panel as:
        # "Ali - FAKE NEWS - 2024-05-12"
        return f"{self.user.username} - {self.result_label} - {self.created_at.strftime('%Y-%m-%d')}"