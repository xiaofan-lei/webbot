# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.dialogs import (
    ComponentDialog,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult,
)
from botbuilder.dialogs.prompts import TextPrompt, PromptOptions,ConfirmPrompt
from botbuilder.core import (
    MessageFactory,
    TurnContext,
    BotTelemetryClient,
    NullTelemetryClient,
)
from botbuilder.schema import InputHints

from booking_details import BookingDetails
from flight_booking_recognizer import FlightBookingRecognizer
from helpers.luis_helper import LuisHelper, Intent
from .booking_dialog import BookingDialog

class MainDialog(ComponentDialog):
    def __init__(
        self,
        luis_recognizer: FlightBookingRecognizer,
        booking_dialog: BookingDialog,
        telemetry_client: BotTelemetryClient = None,
    ):
        super(MainDialog, self).__init__(MainDialog.__name__)
        self.telemetry_client = telemetry_client or NullTelemetryClient()

        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = self.telemetry_client
        

        booking_dialog.telemetry_client = self.telemetry_client

        wf_dialog = WaterfallDialog(
            "WFDialog", [self.intro_step, self.luis_step, self.act_step, self.summary_step, self.final_step]
        )
        wf_dialog.telemetry_client = self.telemetry_client

        self._luis_recognizer = luis_recognizer
        self._luis_text = None
        self._luis_top_intent = False
        self._luis_entities_recongized = False        
        self._luis_result = BookingDetails()
        self._booking_dialog_id = booking_dialog.id

        self.add_dialog(text_prompt)
        self.add_dialog(booking_dialog)
        self.add_dialog(ConfirmPrompt(ConfirmPrompt.__name__))
        self.add_dialog(wf_dialog)

        self.initial_dialog_id = "WFDialog"

    async def intro_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            await step_context.context.send_activity(
                MessageFactory.text(
                    "NOTE: LUIS is not configured. To enable all capabilities, add 'LuisAppId', 'LuisAPIKey' and "
                    "'LuisAPIHostName' to the appsettings.json file.",
                    input_hint=InputHints.ignoring_input,
                )
            )
            await step_context.next(None)
      
        message_text = (
            str(step_context.options)
            if step_context.options
            else "Happy to have you here, what can I do for you? "
        )
        prompt_message = MessageFactory.text(
                    message_text, message_text, InputHints.expecting_input
                )
        return await step_context.prompt(
                TextPrompt.__name__, PromptOptions(prompt=prompt_message)
            )
        
    async def luis_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        if not self._luis_recognizer.is_configured:
            # LUIS is not configured, we just run the BookingDialog path with an empty BookingDetailsInstance.
            return await step_context.begin_dialog(
                self._booking_dialog_id, BookingDetails()
            )
        # Call LUIS and gather any potential booking details. (Note the TurnContext has the response to the prompt.)
        intent, luis_result = await LuisHelper.execute_luis_query(
            self._luis_recognizer, step_context.context
        )
        self._luis_text = step_context.result

        if intent == Intent.BOOK_FLIGHT.value and luis_result:
            self._luis_top_intent = intent

            origin = f" from {luis_result.origin}" if luis_result.origin else ""
            destination = f" to {luis_result.destination}" if luis_result.destination else ""
            travel_start_date =f" leaving on {luis_result.travel_start_date}" if luis_result.travel_start_date else "" 
            travel_end_date = f" coming back on {luis_result.travel_end_date}" if luis_result.travel_end_date else ""  
            n_passengers = "for only one passenger" if luis_result.n_passengers==1 else f" for {luis_result.n_passengers} passengers" if luis_result.n_passengers else ""
            budget = f" with a budget of {luis_result.budget}" if luis_result.budget else ""
            luis_entities =  f"{origin}{destination}{travel_start_date}{travel_end_date}{n_passengers}{budget}"

            if len(luis_entities)>0:
                self._luis_result = luis_result
                self._luis_entities_recongized = True
                #summary message
                summary_text = ( f"Got you, a flight {luis_entities}. Do you want to proceed?" )
            else:
                summary_text = ( f"Ok, you'd like to book a flight. Do you want to proceed?")
            
            # Offer a YES/NO prompt.            
            return await step_context.prompt(
                    ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(summary_text))
                )               

        else:
            summary_text = (
                "Sorry, I didn't get that. Would you like to book a flight?"
            )
            
        # Offer a YES/NO prompt.            
        return await step_context.prompt(
                ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(summary_text))
            )               

    async def act_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        #send the luis result to application insights
        self.telemetry_client.track_trace("luis_result", 
                            {'user_message' : self._luis_text,
                            'luis_top_intent' : self._luis_top_intent,
                            'luis_entities_recongized' : self._luis_entities_recongized,
                            'user_proceeded': True if step_context.result else False,
                            'dst_city' : self._luis_result.origin,
                            'or_city' : self._luis_result.destination,
                            'start_date' : self._luis_result.travel_start_date,
                            'end_date' : self._luis_result.travel_end_date,
                            'n_passengers' : self._luis_result.n_passengers,
                            'budgdet': self._luis_result.budget,
                            })
        self.telemetry_client.flush()
        
        if step_context.result: 
            #user wants to proceed the booking process
            # Run the BookingDialog giving it whatever details we have from the LUIS call.
            return await step_context.begin_dialog(self._booking_dialog_id, self._luis_result )
        else:
             return await step_context.end_dialog()

    async def summary_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the child dialog ("BookingDialog") was cancelled or the user failed to confirm,
        # the Result here will be null.
        result = step_context.result

        if result is not None:
        # Now we have all the booking details call the booking service.
            msg_txt = (f"I have you booked to {result.destination} from {result.origin} on {result.travel_start_date} and back on {result.travel_end_date}"
                f" for { result.n_passengers} people, with a budget of { result.budget}$.")
            # If the call to the booking service was successful tell the user.
            message = MessageFactory.text(msg_txt, msg_txt, InputHints.ignoring_input)
            await step_context.context.send_activity(message)

        prompt_message = "Would you like to book another flight?"
        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__, PromptOptions(prompt=MessageFactory.text(prompt_message))
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # If the main dialog was cancelled or the user failed to confirm
        # the Result here will be null.
        if step_context.result:
            prompt_message = "Please tell me about your flight dates, departure city, destination, number of passengers and your budget. "
            return await step_context.replace_dialog(self.id, prompt_message)
        else:
            return await step_context.end_dialog()

        
    @staticmethod
    async def _show_warning_for_unsupported_cities(
        context: TurnContext, luis_result: BookingDetails
    ) -> None:
        """
        Shows a warning if the requested From or To cities are recognized as entities but they are not in the Airport entity list.
        In some cases LUIS will recognize the From and To composite entities as a valid cities but the From and To Airport values
        will be empty if those entity values can't be mapped to a canonical item in the Airport.
        """
        if luis_result.unsupported_airports:
            message_text = (
                f"Sorry but the following airports are not supported:"
                f" {', '.join(luis_result.unsupported_airports)}"
            )
            message = MessageFactory.text(
                message_text, message_text, InputHints.ignoring_input
            )
            await context.send_activity(message)
