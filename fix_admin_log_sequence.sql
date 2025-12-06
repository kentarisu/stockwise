-- Fix for Django Admin Log sequence issue in PostgreSQL
-- This happens when records are deleted from django_admin_log table
-- and the sequence counter gets out of sync

-- Run this SQL directly on your PostgreSQL database in DigitalOcean

-- Step 1: Find the current max ID in django_admin_log
-- SELECT MAX(id) FROM django_admin_log;

-- Step 2: Reset the sequence to be higher than the max ID
-- Replace 178 (or whatever the max ID is) with the actual maximum ID from step 1
SELECT setval('django_admin_log_id_seq', (SELECT MAX(id) FROM django_admin_log) + 1, false);

-- If the above doesn't work, try this alternative:
-- SELECT setval('django_admin_log_id_seq', COALESCE((SELECT MAX(id) FROM django_admin_log), 1), true);

-- To verify it worked:
-- SELECT nextval('django_admin_log_id_seq');

-- Note: You may need to run this for other tables that have sequence issues too
-- Common ones include:
-- SELECT setval('django_content_type_id_seq', (SELECT MAX(id) FROM django_content_type) + 1, false);
-- SELECT setval('core_product_product_id_seq', (SELECT MAX(id) FROM core_product) + 1, false);
-- etc.

