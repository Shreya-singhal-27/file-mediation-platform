"""Tests for the transformation module."""

from app.schemas.transformation import OutputSchema, OutputSchemaField, TransformationFieldMapping
from app.services.transformation.transformation_manager import TransformationManager


def test_transformation_manager_applies_core_transformations() -> None:
	"""Records should be mapped, formatted, converted, and defaulted correctly."""
	manager = TransformationManager()
	records = [
		{
			"name": "alice",
			"birth_date": "2026-07-16T10:30:00",
			"amount": "1234.5",
			"enabled": "yes",
		}
	]
	mappings = [
		TransformationFieldMapping(
			rule_id="name-rule",
			source_field="name",
			target_field="name",
			transformation_type="COPY",
			required=True,
		),
		TransformationFieldMapping(
			rule_id="birth-date-rule",
			source_field="birth_date",
			target_field="birth_date",
			transformation_type="DATE_FORMAT",
			parameters={"input_format": "%Y-%m-%dT%H:%M:%S", "format": "%d/%m/%Y"},
			required=True,
		),
		TransformationFieldMapping(
			rule_id="amount-rule",
			source_field="amount",
			target_field="amount",
			transformation_type="NUMBER_FORMAT",
			parameters={"format": ",.2f"},
			required=True,
		),
		TransformationFieldMapping(
			rule_id="enabled-rule",
			source_field="enabled",
			target_field="enabled",
			transformation_type="BOOLEAN_CONVERSION",
			required=True,
		),
		TransformationFieldMapping(
			rule_id="status-rule",
			source_field="status",
			target_field="status",
			transformation_type="DEFAULT_VALUE",
			default_value="active",
			required=True,
		),
	]
	output_schema = OutputSchema(
		fields=[
			OutputSchemaField(field_name="name", data_type="STRING", required=True),
			OutputSchemaField(field_name="birth_date", data_type="STRING", required=True),
			OutputSchemaField(field_name="amount", data_type="STRING", required=True),
			OutputSchemaField(field_name="enabled", data_type="BOOLEAN", required=True),
			OutputSchemaField(field_name="status", data_type="STRING", required=True),
		]
	)

	result = manager.transform_records(records, mappings, output_schema)

	assert result.statistics.total_records == 1
	assert result.statistics.transformed_records == 1
	assert result.statistics.rejected_records == 0
	assert result.transformed_records == [
		{
			"name": "alice",
			"birth_date": "16/07/2026",
			"amount": "1,234.50",
			"enabled": True,
			"status": "active",
		}
	]


def test_transformation_manager_rejects_missing_required_fields() -> None:
	"""Records missing required fields should be rejected with a useful reason."""
	manager = TransformationManager()
	result = manager.transform_records(
		[{"birth_date": "2026-07-16"}],
		[
			TransformationFieldMapping(
				rule_id="name-rule",
				source_field="name",
				target_field="name",
				transformation_type="COPY",
				required=True,
			)
		],
	)

	assert result.statistics.transformed_records == 0
	assert result.statistics.rejected_records == 1
	assert result.rejected_records[0].rule_id == "name-rule"
	assert "required" in result.rejected_records[0].reject_reason.lower()


def test_transformation_manager_rejects_output_schema_mismatches() -> None:
	"""Records should be rejected when the output schema does not match the transformed value types."""
	manager = TransformationManager()
	result = manager.transform_records(
		[{"amount": "1234.5"}],
		[
			TransformationFieldMapping(
				rule_id="amount-rule",
				source_field="amount",
				target_field="amount",
				transformation_type="NUMBER_FORMAT",
				parameters={"format": ",.2f"},
				required=True,
			)
		],
		OutputSchema(
			fields=[
				OutputSchemaField(field_name="amount", data_type="INTEGER", required=True),
			]
		),
	)

	assert result.statistics.transformed_records == 0
	assert result.statistics.rejected_records == 1
	assert result.rejected_records[0].rule_id == "amount-rule"
	assert "type" in result.rejected_records[0].reject_reason.lower()
