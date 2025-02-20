import sentry_sdk

from ..models.schemas import Settings


def setup(app):
    if Settings.DISABLE_TELEMETRY:
        return
    sentry_sdk.init(
        dsn="https://b5c59f7e5ab86d73518222ddb40807c9@o4508851738247168.ingest.de.sentry.io/4508851740541008",
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        _experiments={
            # Set continuous_profiling_auto_start to True
            # to automatically start the profiler on when
            # possible.
            "continuous_profiling_auto_start": True,
        },
    )
