-- Display documents belonging to Run 1.
SELECT
    document_id,
    run_id,
    file_name,
    status_,
    file_hash
FROM public.document
WHERE run_id = 1;