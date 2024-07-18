"""
Data analysis of Donor information.

Will be using Pandas for data manipulation to start, but I'd like to explore
using Polars as an alternative and doing some profiling to see if Polars is
actually faster for datasets of this size.

See more info about Polars here:
https://blog.jetbrains.com/dataspell/2023/08/polars-vs-pandas-what-s-the-difference/#:~:text=As%20you%20can%20see%2C%20Polars,out%2Dof%2Dmemory%20errors.

Notes:
    1. Loading from CSV provides an ~35x speed increase over loading from XLSX.
    2.
"""
import glob
from pathlib import Path

from donordatabase import DonorDatabase, DonorLevel

if __name__ == '__main__':
    # Create the Donor Database
    directory = Path('../data')
    db = DonorDatabase(filepath=glob.glob(str(directory / '*.csv')))

    # How much time do the payments in the database span?
    print(f"\nDonor Database Timespan: {db.timespan}")

    # What is the total contributions by all donors in the database?
    print(f"Donor Database Total Contributions: ${db.total_contributions:,.2f}")

    # Get a list of donor names
    donor_names = db.names

    # Find the largest donor
    top_donor = db.top_donor
    print(f"\nLargest Donor:\n{top_donor}")
    # Find the largest single contribution from this donor
    print(f"Largest single contribution: "
          f"${top_donor.largest_contribution:,.2f}")

    # Find the 10 largest donors
    n_donors = 15
    top_donors = db.get_top_donors(n_donors)
    print(f"\n{n_donors} Largest Donors:")
    print(*top_donors, sep='\n')

    # Get donors by contribution level
    donors_by_level = db.get_donors_by_level()
    print("\nDonors by Level:")
    for level, donors in donors_by_level.items():
        print(f"{level}: {len(donors)} Donor(s)")

    # List all donors at a particular level
    level = DonorLevel.DONORLEVEL_FIVE
    print(f"\n{level} Donors:")
    print(*donors_by_level[level], sep='\n')

    # Get some basic statistics for each donor level
    donor_stats = db.get_donor_level_stats()
    print("\nDonor Level Statistics:")
    for level, stats in donor_stats.items():
        print(f"{level.name}: \t{stats}")

    # Create a histogram of donors at a given level
    level = DonorLevel.DONORLEVEL_TWO
    print(f"\nPlotting {level.name} Histogram")
    db.plot_payment_amount_hist(level=level, include_refunds=True,
                                colorized=True)

    # Create a histogram of payment dates
    db.plot_payment_date_hist()
