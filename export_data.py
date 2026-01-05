#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Export data from SQLite database to JSON file with proper UTF-8 encoding.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockwise_py.settings')
django.setup()

from django.core.management import call_command

# Export data with UTF-8 encoding
print("Exporting data from SQLite...")
with open('data_export.json', 'w', encoding='utf-8') as f:
    call_command(
        'dumpdata',
        '--natural-foreign',
        '--natural-primary',
        '-e', 'contenttypes',
        '-e', 'auth.Permission',
        '-e', 'sessions.session',
        '-e', 'admin.logentry',
        '--indent', '2',
        stdout=f
    )

print("✅ Data exported successfully to data_export.json")
print("File size:", os.path.getsize('data_export.json'), "bytes")

