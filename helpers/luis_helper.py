# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from booking_details import BookingDetails



from word2number.w2n import word_to_num
def int_extraction(text):
    number =[]
    for s in text.split():
        if s=="me":
            number.append(1)
        else:
            try:
                number.append(word_to_num(s))
            except Exception:
                pass
            
    return sum(number)

from datetime import date
today = date.today()
from datetime import timedelta
from dateutil.parser import parse
def date_extraction(text):
    if text:
        try:
            date = parse(text, fuzzy=True)
            travel_date = today if str(text).lower() =="asap" else date
        except:
            travel_date = None
    else:
        travel_date = None

    return travel_date


class Intent(Enum):
    BOOK_FLIGHT = "book"
    CANCEL = "None"
    GET_WEATHER = "None"
    NONE_INTENT = "None"

class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)
            intent = (
                LuisRecognizer.top_intent(recognizer_result)
                if recognizer_result.intents
                else None
            )

            if intent == Intent.BOOK_FLIGHT.value:
                result = BookingDetails()

                # We need to get the result from the LUIS JSON which at every level returns an array.
                #destination city
                to_entities = recognizer_result.entities.get("$instance", {}).get(
                    "dst_city", []
                )
                if to_entities: result.destination = to_entities[0]["text"].capitalize()
                
                #departure city
                from_entities = recognizer_result.entities.get("$instance", {}).get(
                    "or_city", []
                )
                if from_entities: result.origin = from_entities[0]["text"].capitalize()

                # Date extractions will be convert to a timex format. 
                start_entities = recognizer_result.entities.get("$instance", {}).get(
                    "str_date", []
                )
                if start_entities: 
                    travel_start_date = date_extraction(start_entities[0]["text"])
                    result.travel_start_date = travel_start_date.strftime("%Y-%m-%d")

                #get directly the return date or calculate from the duration
                duration_entities = recognizer_result.entities.get("$instance", {}).get(
                    "max_duration", []
                )
                duration = int_extraction(duration_entities[0]["text"]) if duration_entities else None

                end_entities = recognizer_result.entities.get("$instance", {}).get(
                    "end_date", []
                )
                if end_entities: 
                    result.travel_end_date = date_extraction(end_entities[0]["text"]).strftime("%Y-%m-%d")
                elif from_entities and duration:
                    travel_end_date = travel_start_date + timedelta(days=int(duration))
                    result.travel_end_date = travel_end_date.strftime("%Y-%m-%d")

                #passengers = n_adults + n_children
                adult_entities = recognizer_result.entities.get("$instance", {}).get(
                    "n_adults", []
                )
                n_adults = (int_extraction(adult_entities[0]["text"]) if adult_entities else 0)
                child_entities = recognizer_result.entities.get("$instance", {}).get(
                    "n_children", []
                )
                n_children = (int_extraction(child_entities[0]["text"]) if child_entities else 0)
                if adult_entities or child_entities : result.n_passengers = n_adults + n_children

                budget_entities = recognizer_result.entities.get("$instance", {}).get(
                    "budget", []
                )
                if budget_entities: result.budget = budget_entities[0]["text"]

        except Exception as exception:
            print(exception)

        return intent, result

