"""
The AAC Database module.
"""
import datetime
from collections import OrderedDict
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, List, Optional, Union
import warnings

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from .donor import Donor
from .types import DonorLevel, DonorLevelStats, Name


class DonorDatabase:
    """
    Stores a database of Donors and useful metadata, e.g. largest individual
    payment/donation, highest contributing donor, etc.
    """
    def __init__(self, filepath: Union[str, Path, List[str], List[Path]]):
        """
        Args:
            filepath: A single file path or list of file paths from which to
                create the database.
        """
        # Convert to list if only a single path is provided
        if not isinstance(filepath, list):
            filepath = [filepath]

        print("DataFrame profiling:")
        self._dataframes = []
        for path in filepath:
            if isinstance(path, str):
                path = Path(path)

            if path.suffix == '.csv':
                self._dataframes.append(self._load_from_csv(path))
            elif path.suffix == '.xlsx':
                self._dataframes.append(self._load_from_excel(path))
            else:
                raise ValueError(
                    f"Filetype '{path.suffix}' is not supported. Valid file "
                    f"types are [.csv, .xlsx].")

        # Concatenate all dataframes into a single dataframe
        start = perf_counter_ns()
        self._df = pd.concat(self._dataframes, ignore_index=True)
        stop = perf_counter_ns()
        print(f"\tconcatenate {len(self._dataframes)} DFs:\t\t\t\t"
              f"{int((stop - start) * 1e-6)} ms")

        # Store all payments for all donors in the database
        self._payments = {}

        # Create the donor dict by iterating over the entire DataFrame
        start = perf_counter_ns()
        self._donors = {}
        for row in self._df.itertuples():
            if row.user_id not in self._donors:
                # Add the donor to the donor list
                self._donors[row.user_id] = Donor(
                    user_id=row.user_id,
                    firstname=row.firstname,
                    lastname=row.lastname,
                    fullname=row.full_name,
                    email=row.email,
                    street1=row.street_1,
                    street2=row.street_2,
                    city=row.city,
                    state=row.state,
                    postal=row.postal,
                    membership_exp=row.membership_expiration_date
                )

            # Add a new payment for this donor
            payment = self._donors[row.user_id].add_payment(
                transaction_id=row.transaction_id,
                user_id=row.user_id,
                contribution_type=row.type,
                actual_date=row.actual_date,
                posted_date=row.posted_date,
                payment_type=row.payment_type,
                response_meta=row.response_meta,
                amount=row.amount,
                gl_code=row.gl_code
            )
            if payment:
                if payment.transaction_id in self._payments:
                    warnings.warn(
                        f"A payment with Transaction ID "
                        f"'{payment.transaction_id}' (User ID: "
                        f"'{self._payments[payment.transaction_id].user_id}', "
                        f"amount: $"
                        f"{self._payments[payment.transaction_id].amount:.2f}) "
                        f"has already been added to the "
                        f"the {self.__class__.__name__}. The current payment "
                        f"of ${payment.amount:.2f} is associated with User ID "
                        f"'{payment.user_id}'.")
                self._payments[payment.transaction_id] = payment
        stop = perf_counter_ns()
        print(f"\tcreate DonorDatabase ({len(self._donors)}):\t"
              f"{int((stop - start) * 1e-6)} ms")

        self._top_donor = None
        self._total_contributions = None

        # Store donors ordered in various ways, e.g. by total contribution, by
        #  level, rtc.
        self._donors_by_contribution = None
        self._donors_by_level = None
        self._payments_by_date = None
        self._payments_by_date_list = None
        self._donor_level_stats = None

    @property
    def donors(self) -> Dict[int, Donor]:
        return self._donors

    @property
    def names(self) -> List[Name]:
        return [donor.name for donor in self._donors.values()]

    @property
    def top_donor(self) -> Donor:
        if self._top_donor is None:
            max_contribution = 0.0
            for donor in self._donors.values():
                if donor.total_contributions > max_contribution:
                    max_contribution = donor.total_contributions
                    self._top_donor = donor
        return self._top_donor

    @property
    def total_contributions(self) -> float:
        if self._total_contributions is None:
            self._total_contributions = 0.0
            for donor in self._donors.values():
                self._total_contributions += donor.total_contributions
        return self._total_contributions

    @property
    def earliest_payment(self) -> datetime.datetime:
        if self._payments_by_date_list is None:
            self._create_payments_by_date()

        return self._payments_by_date_list[0].posted_date

    @property
    def latest_payment(self) -> datetime.datetime:
        if self._payments_by_date_list is None:
            self._create_payments_by_date()

        return self._payments_by_date_list[-1].posted_date

    @property
    def timespan(self) -> datetime.timedelta:
        return self.latest_payment - self.earliest_payment

    def get_top_donors(self, n: int) -> List[Donor]:
        """
        Returns the n largest donors.

        TODO: Add support for specific time periods.
        Args:
            n: The number of donors to return.
        Returns:
            A list of the n largest Donors by total contributions.
        """
        if self._donors_by_contribution is None:
            self._create_donors_by_contribution()

        top_donors = []
        for idx, donor in enumerate(self._donors_by_contribution.values()):
            if idx > n:
                break
            top_donors.append(donor)
        return top_donors

    def get_donors_by_level(self, level: Optional[DonorLevel] = None) -> \
            Union[Dict[DonorLevel, List[Donor]], List[Donor]]:
        """
        Returns a dictionary of donors sorted by giving level. Each dictionary
        value is a list of donors at that level.

        Args:
            level: If provided, a list of Donors at the specified level is
                returned.
        """
        if self._donors_by_level is None:
            if self._donors_by_contribution is None:
                # We require donors to be ordered by contribution before
                #  grouping them by contribution level
                self._create_donors_by_contribution()

            self._donors_by_level = {}
            for donor in self._donors_by_contribution.values():
                if donor.level not in self._donors_by_level:
                    self._donors_by_level[donor.level] = [donor]
                else:
                    self._donors_by_level[donor.level].append(donor)

        if level in self._donors_by_level:
            return self._donors_by_level[level]
        else:
            return self._donors_by_level

    def get_donor_level_stats(self, level: Optional[DonorLevel] = None) -> \
            Union[Dict[DonorLevel, DonorLevelStats], DonorLevelStats]:
        """
        Returns a dictionary of donors sorted by giving level. Each dictionary
        value is a list of donors at that level.

        Args:
            level: If provided, a list of Donors at the specified level is
                returned.
        """
        if self._donor_level_stats is None:
            donor_level_stats = {}
            for lvl, donors in self.get_donors_by_level().items():
                n_contributions = 0
                total_contributions = 0
                payments = []
                for donor in donors:
                    n_contributions += donor.num_payments
                    total_contributions += donor.total_contributions
                    payments.extend([p.amount for p in donor.payments.values()])

                payments = np.array(payments)
                donor_level_stats[lvl] = DonorLevelStats(
                    level=lvl,
                    n_donors=len(donors),
                    n_payments=n_contributions,
                    total=total_contributions,
                    payments=payments,
                    max=payments.max(),
                    min=payments.min(),
                    mean=payments.mean(),
                    std=payments.std(),
                    median=np.median(payments)
                )
            self._donor_level_stats = donor_level_stats

        if level in self._donor_level_stats:
            return self._donor_level_stats[level]
        else:
            return self._donor_level_stats

    def plot_payment_amount_hist(self, level: Optional[DonorLevel] = None,
                                 include_refunds: bool = False,
                                 colorized: bool = False) -> None:
        """
        Creates a histogram of payments for a given donor level. See the
        following Stack Exchange link for a discussion of optimal bin width:

        https://stats.stackexchange.com/questions/798/calculating-optimal-number-of-bins-in-a-histogram

        Args:
            level:
        """
        if self._donor_level_stats is None:
            # We need the donor level stats to plot a histogram of payments
            _ = self.get_donor_level_stats()

        # Get the payment data
        if level:
            payments = self._donor_level_stats[level].payments
            title_str = f"{level.name} ({level}) Payment Distribution"
        else:
            payments = []
            for lvl, stats in self._donor_level_stats.items():
                payments.extend(stats.payments)
            payments = np.array(payments)
            title_str = f"{self.__class__.__name__} Payment Distribution"

        # Optionally remove all negative payments (refunds) from the data
        data = payments if include_refunds else payments[payments >= 0]

        # Define the bin with and optimal number of bins
        iqr = np.subtract(*np.percentile(data, [75, 25]))
        bin_width = 2 * iqr * (len(data) ** (-1/3))
        n_bins = int((data.max() - data.min()) / bin_width)
        print(f"Histogram: bin_width={bin_width:.2f}, n_bins={n_bins}")

        # TODO: The "optimal" number of bins above seemed to produce a value
        #  that was was much lower than I would've expected. Will need to
        #  revisit the bin_width/n_bins computation later
        n_bins = 100

        if colorized:
            n, bins, patches = plt.hist(data,
                                        bins=n_bins,
                                        facecolor='#2ab0ff',
                                        edgecolor='#e0e0e0',
                                        linewidth=0.5,
                                        alpha=0.7)

            # n MUST be an integer
            n = n.astype('int')
            for i in range(len(patches)):
                # Choose colormap of your taste
                patches[i].set_facecolor(plt.cm.viridis(n[i] / max(n)))

            # # Make one bin stand out (set color and opacity)
            # patches[47].set_fc('red')
            # patches[47].set_alpha(1)
            #
            # # Add annotation
            # plt.annotate('Important Bar!',
            #              xy=(0.57, 175),
            #              xytext=(2, 130),
            #              fontsize=15,
            #              arrowprops={'width': 0.4, 'headwidth': 7,
            #                          'color': '#333333'})
        else:
            # Plot a simple histogram
            plt.hist(x=data,
                     bins=n_bins,
                     facecolor='tab:blue',
                     edgecolor='gray',
                     linewidth=0.5)

        plt.title(title_str.replace('$', '\$'), fontsize=12)
        plt.xlabel('Payment Value [$]', fontsize=10)
        plt.ylabel('Frequency', fontsize=10)
        plt.grid()
        plt.show()

    def plot_payment_date_hist(self):
        """Creates a histogram of all payments by date."""
        # Create the dataset
        dates = [p.posted_date for p in self._payments.values()]
        unique_dates = set(dates)

        n_bins = len(unique_dates)
        n, bins, patches = plt.hist(x=dates,
                                    bins=n_bins,
                                    facecolor='#2ab0ff',
                                    edgecolor='#e0e0e0',
                                    linewidth=0.5,
                                    alpha=0.7)

        date_range = pd.date_range(
            start=self.earliest_payment,
            end=self.latest_payment,
            periods=int(self.timespan.days / 30)
        )
        for i in range(len(patches)):
            # Choose colormap of your taste
            patches[i].set_facecolor(
                plt.cm.viridis(n[i] / max(n.astype('int'))))

        plt.title("Payment Date Distribution", fontsize=12)
        plt.xticks(ticks=date_range, rotation=-45)
        plt.xlabel('Payment Value [$]', fontsize=10)
        plt.ylabel('Frequency', fontsize=10)
        plt.grid()
        plt.show()

    def _create_donors_by_contribution(self) -> None:
        """
        Creates a dictionary of donors ordered by total contributions.

        TODO: This method of sorting a dictionary by an attribute of its values
          seems pretty inefficient. There must be a better way to do this, but
          I'm not having much luck googling "sort dictionary by attribute value"
        """
        # Use an OrderedDict to store donors ordered by total contribution.
        # NOTE: 'total_contribution' is not unique to each donor and thus this
        #   method will not work.
        # Takes ~11ms
        # start = perf_counter_ns()
        # donors = {d.total_contributions: d for d in self._donors.values()}
        # self._donors_by_contribution = \
        #     OrderedDict(sorted(donors.items(), reverse=True))
        # stop = perf_counter_ns()
        # print(f"OrderedDict:\t{(stop - start) * 1e-6} ms")

        # Sort the _donors dict via a lambda (takes ~15ms)
        start = perf_counter_ns()
        # First get a list of sorted keys
        sorted_keys = sorted(
            self._donors,
            key=lambda user_id: self._donors[user_id].total_contributions,
            reverse=True)

        # Then create the ordered dict by iterating through the sorted keys
        self._donors_by_contribution = OrderedDict()
        for key in sorted_keys:
            self._donors_by_contribution[key] = self._donors[key]
        stop = perf_counter_ns()
        print(f"sort Donors by total contributions:\t"
              f"{(stop - start) * 1e-6:.2f} ms")

    def _create_payments_by_date(self) -> None:
        """
        Create a dict of payments ordered by date, oldest to most recent.
        """
        # Note that the method below will not work because the 'posted_date' is
        #  not a unique feature of a payment. Ordering the payments in this way
        #  will result in a dictionary that does not contain all the original
        #  payments since only one payment per posted_date can exist.
        # payments = {p.posted_date: p for p in self._payments.values()}
        # self._payments_by_date = \
        #     OrderedDict(sorted(payments.items(), reverse=True))
        # self._payments_by_date_list = list(self._payments_by_date.values())

        start = perf_counter_ns()
        sorted_keys = sorted(
            self._payments,
            key=lambda trans_id: self._payments[trans_id].posted_date
        )
        self._payments_by_date = OrderedDict()
        for key in sorted_keys:
            self._payments_by_date[key] = self._payments[key]
        self._payments_by_date_list = list(self._payments_by_date.values())
        stop = perf_counter_ns()
        print(f"sort payments by date:\t{(stop - start) * 1e-6:.2f} ms")

    def _load_from_csv(self, filepath: Path) -> pd.DataFrame:
        """
        Creates a Pandas DataFrame from a CSV file.
        Args:
            filepath:

        Returns:
            A Pandas Dataframe.
        """
        start = perf_counter_ns()
        df = pd.read_csv(filepath, header=1, keep_default_na=False)
        stop = perf_counter_ns()
        print(f"\tload from .csv:\t\t\t\t\t{int((stop - start) * 1e-6)} ms")
        return df

    def _load_from_excel(self, filepath: Path) -> pd.DataFrame:
        """
        Creates a Pandas DataFrame from an Excel XLSX file.
        Args:
            filepath:

        Returns:
            A Pandas Dataframe.
        """
        warnings.warn(
            f"Reading from MS Excel file (.xlsx) can be as much as 35x slower "
            f"than reading from a CSV file. Consider creating the "
            f"{self.__class__.__name__} from a .csv file(s)."
        )

        start = perf_counter_ns()
        df = pd.read_excel(filepath, header=1, keep_default_na=False)
        stop = perf_counter_ns()
        print(f"\tload from .xlsx:\t\t\t\t{int((stop - start) * 1e-6)} ms")
        return df
