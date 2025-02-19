# Generated by Django 4.2.1 on 2025-02-11 12:34

from django.db import migrations
from django.db.models import ExpressionWrapper, F, Func, fields

STATUS_RENAME_MAP = {
    "ExecutionStatus.PENDING": "PENDING",
    "ExecutionStatus.INITIATED": "INITIATED",
    "ExecutionStatus.QUEUED": "QUEUED",
    "ExecutionStatus.READY": "READY",
    "ExecutionStatus.EXECUTING": "EXECUTING",
    "ExecutionStatus.COMPLETED": "COMPLETED",
    "ExecutionStatus.STOPPED": "STOPPED",
    "ExecutionStatus.ERROR": "ERROR",
}

REVERSE_STATUS_RENAME_MAP = {v: k for k, v in STATUS_RENAME_MAP.items()}


def rename_statuses_and_update_execution_time(apps, schema_editor):
    """Rename statuses and calculate execution_time in a single DB query per status."""
    WorkflowFileExecution = apps.get_model("file_execution", "WorkflowFileExecution")

    # Calculate execution_time as (modified_at - created_at) in seconds
    execution_time_expr = ExpressionWrapper(
        Func(
            Func(
                F("modified_at") - F("created_at"),
                function="EXTRACT",
                template="EXTRACT(EPOCH FROM %(expressions)s)",
            ),
            3,  # Round to 3 decimal places
            function="ROUND",
        ),
        output_field=fields.FloatField(),
    )

    for old_status, new_status in STATUS_RENAME_MAP.items():
        WorkflowFileExecution.objects.filter(status=old_status).update(
            status=new_status,
            execution_time=execution_time_expr,
        )


# NOTE: The reverse migration does affect unintended rows which were not affected during
# the forward migration - however every status and execution time gets computed as
# expected and this doesn't warrant maintaining a temp table / additional column to
# track the affected rows.
def restore_statuses_and_reset_execution_time(apps, schema_editor):
    """Revert status names and reset execution_time to 0.0 in a single query per status."""
    WorkflowFileExecution = apps.get_model("file_execution", "WorkflowFileExecution")

    for new_status, old_status in REVERSE_STATUS_RENAME_MAP.items():
        WorkflowFileExecution.objects.filter(status=new_status).update(
            status=old_status,
            execution_time=0.0,  # Reset execution time on rollback
        )


class Migration(migrations.Migration):

    dependencies = [
        ("file_execution", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            rename_statuses_and_update_execution_time,
            restore_statuses_and_reset_execution_time,
        ),
    ]
