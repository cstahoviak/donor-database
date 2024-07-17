"""
The donor-database package.
"""
from .database import DonorDatabase
from .donor import Donor
from .types import DonorLevel, DonorLevelStats, Payment

# Define the package name
# __name__ = "donordatabase"

# Define all publicly accessible classes and methods.
__all__ = ["DonorDatabase",
           "Donor",
           "DonorLevel",
           "DonorLevelStats",
           "Payment"]
