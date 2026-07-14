import hashlib
import shutil
from pathlib import Path


class FileUtils:
	"""
	Utility methods for common file operations used
	across acquisition and transmission modules.
	"""

	@staticmethod
	def ensure_directory(
		path: str | Path,
	) -> Path:
		"""
		Create the directory if it does not exist.
		"""

		directory = Path(path)

		directory.mkdir(
			parents=True,
			exist_ok=True,
		)

		return directory

	@staticmethod
	def move_file(
		source: str | Path,
		destination: str | Path,
	) -> Path:
		"""
		Move a file to the destination directory.
		"""

		source_path = Path(source)

		destination_path = Path(destination)

		FileUtils.ensure_directory(
			destination_path.parent,
		)

		shutil.move(
			str(source_path),
			str(destination_path),
		)

		return destination_path

	@staticmethod
	def copy_file(
		source: str | Path,
		destination: str | Path,
	) -> Path:
		"""
		Copy a file to another location.
		"""

		source_path = Path(source)

		destination_path = Path(destination)

		FileUtils.ensure_directory(
			destination_path.parent,
		)

		shutil.copy2(
			source_path,
			destination_path,
		)

		return destination_path

	@staticmethod
	def delete_file(
		path: str | Path,
	) -> None:
		"""
		Delete a file if it exists.
		"""

		file = Path(path)

		if file.exists():
			file.unlink()

	@staticmethod
	def calculate_checksum(
		path: str | Path,
		algorithm: str = "md5",
	) -> str:
		"""
		Calculate the checksum of a file.

		Supported algorithms:
		- md5
		- sha1
		- sha256
		"""

		file = Path(path)

		try:
			hasher = hashlib.new(
				algorithm.lower(),
			)
		except ValueError as exc:
			raise ValueError(
				f"Unsupported hash algorithm: {algorithm}"
			) from exc

		with open(
			file,
			"rb",
		) as stream:

			for chunk in iter(
				lambda: stream.read(4096),
				b"",
			):
				hasher.update(chunk)

		return hasher.hexdigest()

	@staticmethod
	def get_file_size(
		path: str | Path,
	) -> int:
		"""
		Return file size in bytes.
		"""

		return Path(path).stat().st_size

	@staticmethod
	def is_empty_file(
		path: str | Path,
	) -> bool:
		"""
		Check whether the file is empty.
		"""

		return FileUtils.get_file_size(
			path,
		) == 0

	@staticmethod
	def file_exists(
		path: str | Path,
	) -> bool:
		"""
		Check whether a file exists.
		"""

		return Path(path).exists()

	@staticmethod
	def get_extension(
		path: str | Path,
	) -> str:
		"""
		Return file extension in lowercase.
		"""

		return Path(path).suffix.lower()

	@staticmethod
	def list_files(
		directory: str | Path,
	) -> list[Path]:
		"""
		Return all files inside a directory.
		"""

		path = Path(directory)

		if not path.exists():
			return []

		return [
			file
			for file in path.iterdir()
			if file.is_file()
		]