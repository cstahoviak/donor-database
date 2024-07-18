"""
The AAC Types module.
"""
from collections import namedtuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import warnings

import numpy as np

from .utils import string_to_datetime, currency_to_str

Name = namedtuple('Name', ['first', 'last', 'full'])
Range = namedtuple('Range', ['lower', 'upper'])


@dataclass(frozen=True)
class Address:
    street1: str
    street2: str
    city: str
    state: str
    postal: int


class DonorLevel(Enum):
    # Defining __order__ is only necessary in Python <3.0
    # __order__ = ' ZERO ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT NINE TEN '
    DONORLEVEL_ZERO = Range(lower=0, upper=500)
    DONORLEVEL_ONE = Range(lower=500, upper=1_000)
    DONORLEVEL_TWO = Range(lower=1_000, upper=2_500)
    DONORLEVEL_THREE = Range(lower=2_500, upper=5_000)
    DONORLEVEL_FOUR = Range(lower=5_000, upper=7_500)
    DONORLEVEL_FIVE = Range(lower=7_500, upper=10_000)
    DONORLEVEL_SIX = Range(lower=10_000, upper=25_000)
    DONORLEVEL_SEVEN = Range(lower=25_000, upper=50_000)
    DONORLEVEL_EIGHT = Range(lower=50_000, upper=75_000)
    DONORLEVEL_NINE = Range(lower=75_000, upper=100_000)
    DONORLEVEL_TEN = Range(lower=100_000, upper=250_000)

    def __repr__(self):
        return (f"({self.name}: "
                f"lower={currency_to_str(self.value.lower)}, "
                f"upper={currency_to_str(self.value.upper)})")

    def __str__(self):
        return (f"{currency_to_str(self.value.lower)} - "
                f"{currency_to_str(self.value.upper)}")


@dataclass
class DonorLevelStats:
    """
    level: The DonorLevel for this set of statistics.
    num: The total number of contributions (payments + donations + refunds) at
        the given donor level.
    mean: The mean contribution amount at this donor level.
    """
    level: DonorLevel
    n_donors: int
    n_payments: int
    total: float
    payments: np.ndarray
    max: float
    min: float
    mean: float
    std: float
    median: float
    # mode: float

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"level: {self.level}, "
                f"donors: {self.n_donors}, "
                f"total contributions: {self.n_payments}, "
                f"total contribution value: ${self.total:,.2f}, "
                f"max: ${self.max:,.2f}, "
                f"min: ${self.min:,.2f}, "
                f"mean: ${self.mean:,.2f}, "
                f"std: ${self.std:,.2f}, "
                f"median: ${self.median:,.2f})")


@dataclass(frozen=True)
class Payment:
    transaction_id: int
    user_id: int
    contribution_type: str
    actual_date: Optional[datetime]
    posted_date: Optional[datetime]
    firstname: str
    lastname: str
    fullname: str
    email: str
    payment_type: str
    response_meta: str
    amount: float
    gl_code: int
    street1: str
    street2: str
    city: str
    state: str
    postal: int

    def __repr__(self):
        return (f"{self.__class__.__name__}("
                f"transaction ID: {self.transaction_id}, "
                f"user ID: {self.user_id}, "
                f"name: {self.fullname}, "
                f"amount: ${self.amount:,.2f}, "
                f"type: {self.contribution_type})")

    def __post_init__(self):
        """
        For more info on setting an attribute of a 'frozen' dataclass object
        via the __post_init__ method, see:
        https://stackoverflow.com/questions/53756788/how-to-set-the-value-of-dataclass-field-in-post-init-when-frozen-true

        "There is a tiny performance penalty when using frozen=True: __init__()
        cannot use simple assignment to initialize fields, and must use
        object.__setattr__(self, 'attr_name', value)."
        """
        # Convert actual_date to datetime object
        if isinstance(self.actual_date, str):
            actual_date = string_to_datetime(self.actual_date, '%Y-%m-%d')
            object.__setattr__(self, 'actual_date', actual_date)

        # Convert posted_date to datetime object
        if isinstance(self.posted_date, str):
            posted_date = string_to_datetime(self.posted_date, '%Y-%m-%d')
            object.__setattr__(self, 'posted_date', posted_date)

        if not self.actual_date and self.posted_date:
            warnings.warn(f"{self} has neither a valid 'actual_date' nor a "
                          f"valid 'posted_date'.")

        # Use the posted date as the actual date if no posted date is given, and
        #  vice versa.
        actual = self.actual_date if self.actual_date else self.posted_date
        posted = self.posted_date if self.posted_date else self.actual_date
        object.__setattr__(self, 'actual_date', actual)
        object.__setattr__(self, 'posted_date', posted)
