# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.dialogs import WaterfallDialog, WaterfallStepContext, DialogTurnResult
from botbuilder.dialogs.prompts import ConfirmPrompt, TextPrompt, PromptOptions, NumberPrompt,PromptValidatorContext
from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from .cancel_and_help_dialog import CancelAndHelpDialog
from .date_resolver_dialog import DateResolverDialog

class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client
        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.destination_step,
                self.origin_step,
                self.travel_start_date_step,
                self.travel_end_date_step,
                self.n_passengers_step,
                self.budget_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(
            DateResolverDialog("StartDateResolverDialog","When would you like to go?", self.telemetry_client)
        )
        self.add_dialog(
            DateResolverDialog("EndDateResolverDialog","On what date would you trip back?", self.telemetry_client)
        )
        self.add_dialog(NumberPrompt("PassengerNumberPrompt", BookingDialog.passenger_prompt_validator))
        self.add_dialog(NumberPrompt("BudgetPrompt", BookingDialog.budget_prompt_validator))
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination."""
        booking_details = step_context.options

        if booking_details.destination is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("What's your destination?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.destination)

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.destination = step_context.result
        if booking_details.origin is None:
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Where will you be travelling from?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.origin)

    async def travel_start_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.origin = step_context.result

        if not booking_details.travel_start_date or self.is_ambiguous(
            booking_details.travel_start_date
        ):
            return await step_context.begin_dialog(
                "StartDateResolverDialog", booking_details.travel_start_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.travel_start_date)

    async def travel_end_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for returning date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        booking_details.travel_start_date = step_context.result
        if not booking_details.travel_end_date or self.is_ambiguous(
            booking_details.travel_end_date
        ):
            return await step_context.begin_dialog(
                "EndDateResolverDialog", booking_details.travel_end_date
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.travel_end_date)

    async def n_passengers_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for adult travelers."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt
        booking_details.travel_end_date = step_context.result

        reprompt_msg = (
            "I'm sorry, according to our booking policy, you can order up to 50 tickets each time."
        )
        if booking_details.n_passengers is None:
            return await step_context.prompt(
                "PassengerNumberPrompt",
                PromptOptions(
                    prompt=MessageFactory.text("How many tickets would you like to book? "),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.n_passengers)

    async def budget_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for budget"""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt, and only take the first numeric value
        booking_details.n_passengers = step_context.result

        reprompt_msg = (
            "Sorry, I didn't get that. Could I have your maximum budget number?"
        )
        if booking_details.budget is None:
            return await step_context.prompt(
                "BudgetPrompt",
                PromptOptions(
                    prompt=MessageFactory.text("What were you planning on spending for this trip? "),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.budget)

    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        booking_details = step_context.options

        # Capture the response to the previous step's prompt, and only take the first numeric value
        booking_details.budget = step_context.result

        n_passenger = f"{ booking_details.n_passengers} passengers, " if booking_details.n_passengers>1 else "one passenger, "
        msg = (
            "Please confirm, you'd like to book a round trip flight "
            f"from {booking_details.origin} "
            f"to { booking_details.destination } "
            f"on {booking_details.travel_start_date}, "
            f"and return on { booking_details.travel_end_date}, "
            f"there'll be {n_passenger}"
            f"with a budget of { booking_details.budget}$. "
            "Is that right?"
        )

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(msg))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""
        if step_context.result:
            booking_details = step_context.options

            return await step_context.end_dialog(booking_details)

        return await step_context.end_dialog()

    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types

    async def passenger_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        # This condition is our validation rule. You can also change the value at this point.
        return (
            prompt_context.recognized.succeeded
            and 0 < prompt_context.recognized.value <= 50
        )

    async def budget_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        # This condition is our validation rule. You can also change the value at this point.
        return(
            prompt_context.recognized.succeeded
            and 0 < prompt_context.recognized.value
        )
