from pydantic import BaseModel, Field

class SourceConfiguration(BaseModel):

	type: str = "LOCAL"

	source_path: str

	archive_path: str

	rejected_path: str

	allowed_extensions: list[str] = Field(
		default_factory=list,
	)

class FTPConfiguration(BaseModel):

	host: str

	port: int = 21

	username: str

	password: str

	remote_directory: str

	local_download_directory: str

	archive_directory: str

	rejected_directory: str

	allowed_extensions: list[str] = Field(
		default_factory=list,
	)
	
class SFTPConfiguration(BaseModel):

	host: str

	port: int = 22

	username: str

	password: str

	remote_directory: str

	local_download_directory: str

	archive_directory: str

	rejected_directory: str

	allowed_extensions: list[str] = Field(
		default_factory=list,
	)