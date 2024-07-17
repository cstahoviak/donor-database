"""
The AAC Utilities module.
"""
from datetime import datetime
from typing import Optional


def string_to_datetime(date_str: str, format: str) -> Optional[datetime]:
    """
    Converts a string to a datetime object. Note that the datetime module
    does not seem to have a NaT representation like np.datetime64('NaT'), so if
    an empty string is provided, None is returned.

    Args:
        date_str:
        format:
    """
    return datetime.strptime(date_str, format) if date_str else None


def currency_to_str(value: int) -> str:
    return f"${value:.0f}" if value < 1000 else f"${(value / 1e3):,.0f}k"
