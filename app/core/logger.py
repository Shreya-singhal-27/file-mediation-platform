import os
import sys

from loguru import logger

from app.config import Settings


def configure_logger(settings: Settings) -> None:
	os.makedirs(os.path.dirname(settings.log_path), exist_ok=True)

	logger.remove()
	logger.add(
		sys.stdout,
		level=settings.log_level.upper(),
		colorize=False,
		enqueue=True,
		backtrace=False,
		diagnose=False,
		format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
	)
	logger.add(
		settings.log_path,
		level=settings.log_level.upper(),
		rotation="10 MB",
		retention="10 days",
		compression="zip",
		enqueue=True,
		backtrace=False,
		diagnose=False,
		format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
	)
