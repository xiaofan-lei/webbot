# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class BookingDetails:
    def __init__(
        self,
        destination: str = None,
        origin: str = None,
        travel_start_date: str = None,
        travel_end_date: str = None,
        n_passengers: str = None,
        budget: str = None,
        unsupported_airports=None,
    ):
        if unsupported_airports is None:
            unsupported_airports = []
        self.destination = destination
        self.origin = origin
        self.travel_start_date = travel_start_date
        self.travel_end_date = travel_end_date
        self.n_passengers = n_passengers
        self.budget = budget
        self.unsupported_airports = unsupported_airports
