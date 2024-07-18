"""
The AAC Donor module.
"""
from datetime import datetime
from typing import Dict, List, Optional, Union
import warnings

import numpy as np

from .types import Name, Address, DonorLevel, Payment


class Donor:
    """
    This class represents a single Donor to the AAC.
    """
    def __init__(self, user_id: int, firstname: str, lastname: str,
                 fullname: Optional[str] = None, email: Optional[str] = None,
                 street1: Optional[str] = None, street2: Optional[str] = None,
                 city: Optional[str] = None, state: Optional[str] = None,
                 postal: Optional[int] = None,
                 membership_exp: Union[str, datetime] = None):
        """
        Args:
            user_id:
            firstname:
            lastname:
            fullname:
            email:
            street1:
            street2:
            city:
            state:
            postal:
        """
        self._id = user_id
        # Remove unwanted additional spaces between first/last names when
        #   creating the fullname
        full = " ".join(fullname.split()) if fullname else \
            " ".join([firstname.strip(), lastname.strip()])
        self._name = Name(
            # Strip leading/trailing white space from all string fields
            first=firstname.strip(),
            last=lastname.strip(),
            full=full
        )
        self._email = email.strip()
        # TODO: May want to store a current address and a list of address'
        #   instead of just a single address.
        self._address = Address(
            street1=street1.strip(),
            street2=street2.strip(),
            city=city.strip(),
            state=state.strip(),
            postal=postal
        )
        self._membership_exp = None
        if membership_exp:
            if isinstance(membership_exp, str):
                membership_exp = datetime.strptime(
                    membership_exp, '%Y-%m-%d')
            self._membership_exp = membership_exp

        # Store the payments and donations by their transaction ID
        self._payments = {}

        # Store some other metadata
        self._donor_level = None
        self._contributions = {'Payment': 0.0,
                               'Donation': 0.0,
                               'Refund': 0.0}

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}("
                f"ID: {self._id}, "
                f"name: '{self._name.full}', "
                f"email: {self._email}, "
                f"total contributions: {self.num_payments}, "
                f"total contribution value: ${self.total_contributions:,.2f}, "
                f"level: {self.level.name})")

    @property
    def name(self) -> Name:
        return self._name

    @property
    def payments(self) -> Dict[int, Payment]:
        return self._payments

    @property
    def num_payments(self) -> int:
        return len(self._payments)

    @property
    def total_contributions(self) -> float:
        """Returns the total contributions as a single value."""
        return sum(self._contributions.values())

    @property
    def largest_payment(self) -> Optional[Payment]:
        """Returns this donor's largest payment."""
        max_amount = 0.0
        max_payment = None
        for payment in self._payments.values():
            if payment.contribution_type == 'Payment':
                if payment.amount > max_amount:
                    max_amount = payment.amount
                    max_payment = payment
        return max_payment

    @property
    def largest_donation(self) -> Optional[Payment]:
        """Returns this donor's largest donation."""
        max_amount = 0.0
        max_donation = None
        for payment in self._payments.values():
            if payment.contribution_type == 'Donation':
                if payment.amount > max_amount:
                    max_amount = payment.amount
                    max_donation = payment
        return max_donation

    @property
    def largest_contribution(self) -> float:
        # TODO: Deal with None value appropriately.
        return max(self.largest_payment.amount,
                   self.largest_donation.amount)

    @property
    def level(self) -> DonorLevel:
        if self._donor_level is None:
            for level in DonorLevel:
                if np.abs(self.total_contributions) < level.value.upper:
                    self._donor_level = level
                    break
        return self._donor_level

    def add_payment(self, transaction_id: int, user_id: int,
                    contribution_type: str,
                    actual_date: Union[str, datetime],
                    posted_date: Union[str, datetime],
                    payment_type: str, response_meta: str, amount: float,
                    gl_code: int) -> Optional[Payment]:
        """
        Add a Payment (Payment, Donation or Refund) for the donor.

        Args:
            transaction_id:
            user_id:
            contribution_type:
            actual_date:
            posted_date:
            payment_type:
            response_meta:
            amount:
            gl_code:

        Returns:
            The Payment that was created for the provided payment data.
        """
        payment = None
        if self._id == user_id:
            # Create the payment
            payment = Payment(
                transaction_id=transaction_id,
                user_id=user_id,
                contribution_type=contribution_type,
                actual_date=actual_date,
                posted_date=posted_date,
                firstname=self._name.first,
                lastname=self._name.last,
                fullname=self._name.full,
                email=self._email,
                payment_type=payment_type,
                response_meta=response_meta,
                amount=amount,
                gl_code=gl_code,
                street1=self._address.street1,
                street2=self._address.street2,
                city=self._address.city,
                state=self._address.state,
                postal=self._address.postal
            )

            # Add payment to list of payments
            self._payments[transaction_id] = payment

            # Update the contribution values.
            # Note: expect 'Refund' payments to have a negative 'amount'.
            self._contributions[payment.contribution_type] += payment.amount
        else:
            warnings.warn(
                f"Unable to add transaction '{transaction_id}' for user "
                f"'{user_id}' to Donor '{self._id}'.")

        return payment

    def get_payments(self, start: Union[str, datetime],
                     end: Union[str, datetime]) -> List[Payment]:
        """
        Returns all payments between the start and stop dates. Payments will be
        ordered from most recent to earliest.
        """
        pass
