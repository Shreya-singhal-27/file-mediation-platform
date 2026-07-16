from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from typing import Any

from app.schemas.transformation import OutputSchema, TransformationFieldMapping
from app.services.decoder.decoder_factory import DecoderFactory
from app.services.filtering.filter_manager import FilterManager
from app.services.pipeline.pipeline_context import PipelineExecutionContext
from app.services.transformation.transformation_manager import TransformationManager
from app.services.transmission.transmission_manager import TransmissionManager
from app.utils.file_utils import FileUtils


class PipelineExecutor:
	"""Executes the decode, filter, transform and transmit stages for one file."""

	def __init__(
		self,
		filter_manager: FilterManager | None = None,
		transformation_manager: TransformationManager | None = None,
		transmission_manager: TransmissionManager | None = None,
	) -> None:
		self._filter_manager = filter_manager or FilterManager()
		self._transformation_manager = transformation_manager or TransformationManager()
		self._transmission_manager = transmission_manager or TransmissionManager()

	def execute(self, context: PipelineExecutionContext) -> PipelineExecutionContext:
		"""Process a single acquired file through the downstream pipeline stages."""
		context.logs.append(f"Starting processing for '{context.acquired_file.filename}'.")
		try:
			decoder_kwargs = self._extract_decoder_kwargs(context)
			decoder = DecoderFactory.create_decoder(context.acquired_file.path, **decoder_kwargs)
			context.stage = "DECODING"
			context.decoded_records = decoder.decode(context.acquired_file.path)
			context.logs.append(f"Decoded {len(context.decoded_records)} record(s).")

			context.stage = "FILTERING"
			filter_rules = self._active_filter_rules(context)
			if filter_rules:
				filter_result = self._filter_manager.filter_records(context.decoded_records, filter_rules)
				context.filter_result = filter_result
				filtered_records = filter_result.accepted_records
				context.logs.append(
					f"Filtered {filter_result.statistics.rejected_records} record(s); {len(filtered_records)} record(s) remain."
				)
			else:
				filtered_records = context.decoded_records
				context.logs.append("No active filter rules configured; skipping filtering stage.")

			context.stage = "TRANSFORMATION"
			mapping_rules = self._active_mapping_rules(context)
			output_schema = self._resolve_output_schema(context)
			transformed_result = self._transformation_manager.transform_records(
				filtered_records,
				mapping_rules,
				output_schema,
			)
			context.transformed_result = transformed_result
			context.logs.append(
				f"Transformed {transformed_result.statistics.transformed_records} record(s); {transformed_result.statistics.rejected_records} record(s) rejected."
			)

			if transformed_result.rejected_records and not transformed_result.transformed_records:
				context.stage = "TRANSFORMATION"
				context.error_message = transformed_result.rejected_records[0].reject_reason
				return context

			context.stage = "SERIALIZATION"
			context.output_file = self._serialize_output(context, transformed_result.transformed_records)
			context.logs.append(f"Serialized output to '{context.output_file}'.")

			context.stage = "TRANSMISSION"
			transmission_result = self._transmission_manager.transmit_file(
				context.output_file,
				context.destination,
			)
			context.transmission_result = transmission_result
			context.logs.extend(
				[
					f"Transmission status: {transmission_result.status}.",
					f"Transmission attempts: {transmission_result.attempts}.",
				]
			)

			if not transmission_result.success:
				context.error_message = transmission_result.error_message
				return context

			context.completed = True
			context.stage = "COMPLETED"
			return context
		except Exception as exc:
			context.error_message = str(exc)
			context.stage = "FAILED"
			context.logs.append(f"Pipeline processing failed: {exc}")
			return context

	def _active_filter_rules(self, context: PipelineExecutionContext) -> list[Any]:
		"""Return the configured active filter rules for the current pipeline."""
		return [rule for rule in context.pipeline.filter_rules if rule.is_active]

	def _active_mapping_rules(self, context: PipelineExecutionContext) -> list[Any]:
		"""Return the configured active mapping rules for the current pipeline."""
		return [rule for rule in context.pipeline.mapping_rules if getattr(rule, "is_active", True)]

	def _resolve_output_schema(self, context: PipelineExecutionContext) -> OutputSchema | None:
		"""Resolve an optional output schema from the destination configuration."""
		output_schema = context.destination.config.get("output_schema")
		if output_schema is None:
			return None
		if isinstance(output_schema, OutputSchema):
			return output_schema
		return OutputSchema.model_validate(output_schema)

	def _extract_decoder_kwargs(self, context: PipelineExecutionContext) -> dict[str, Any]:
		"""Collect optional decoder settings from the source configuration."""
		config = context.source.config if isinstance(context.source.config, dict) else {}
		decoder_kwargs: dict[str, Any] = {}
		for key in ("schema_path", "record_type", "column_specifications"):
			if key in config:
				decoder_kwargs[key] = config[key]
		decoder_options = config.get("decoder") or config.get("decoder_options")
		if isinstance(decoder_options, dict):
			decoder_kwargs.update(decoder_options)
		return decoder_kwargs

	def _serialize_output(self, context: PipelineExecutionContext, records: list[dict[str, Any]]) -> Path:
		"""Serialize transformed records into a file that can be transmitted."""
		output_format = str(context.pipeline.output_format).upper()
		staging_directory = Path(context.destination.config.get("staging_directory") or tempfile.gettempdir())
		FileUtils.ensure_directory(staging_directory)
		output_path = staging_directory / f"{context.acquired_file.path.stem}.{output_format.lower()}"

		if output_format == "CSV":
			fieldnames = self._resolve_csv_fieldnames(records, context)
			with open(output_path, "w", newline="", encoding="utf-8") as stream:
				writer = csv.DictWriter(stream, fieldnames=fieldnames)
				writer.writeheader()
				for record in records:
					writer.writerow(record)
		elif output_format == "JSON":
			with open(output_path, "w", encoding="utf-8") as stream:
				json.dump(records, stream, ensure_ascii=False, indent=2, default=str)
		elif output_format == "XML":
			raise NotImplementedError("XML output is not implemented yet.")
		else:
			raise ValueError(f"Unsupported output format '{output_format}'.")

		return output_path

	@staticmethod
	def _resolve_csv_fieldnames(records: list[dict[str, Any]], context: PipelineExecutionContext) -> list[str]:
		"""Resolve CSV headers from the transformed records or configured mappings."""
		if records:
			fieldnames: list[str] = []
			for record in records:
				for key in record.keys():
					if key not in fieldnames:
						fieldnames.append(key)
			return fieldnames

		configured_fields = [
			mapping.target_field
			for mapping in context.pipeline.mapping_rules
			if getattr(mapping, "is_active", True)
		]
		if configured_fields:
			return configured_fields
		return ["value"]
