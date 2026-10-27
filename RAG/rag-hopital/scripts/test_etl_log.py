from rag_hopital.etl.log_etl import (
    start_run,
    log_event,
    finish_run,
)

run_id = start_run(
    stage="logger_test",
    configuration={"mode": "test"},
)

log_event(
    run_id,
    step="postgres_connection",
    status="success",
)

finish_run(
    run_id,
    status="success",
    summary={"checks": 1},
)

print("ETL logging OK")
print("Run ID:", run_id)