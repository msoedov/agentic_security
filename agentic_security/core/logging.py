from logging import config


def setup_logging():
    config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "INFO",
            },
            "loggers": {
                "uvicorn.access": {
                    "level": "ERROR",  # Set higher log level to suppress info logs globally
                    "handlers": ["console"],
                    "propagate": False,
                }
            },
        }
    )
