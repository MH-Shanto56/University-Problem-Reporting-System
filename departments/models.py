from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. IT Helpdesk, Engineering & Maintenance, Proctor Office, Sanitation")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. IT, MAINT, PROC, SAN")
    description = models.TextField(blank=True, default='')
    contact_email = models.EmailField(blank=True, default='')

    class Meta:
        db_table = 'core_department'

    def __str__(self):
        return f"{self.name} ({self.code})"
