import aiounittest   # The test framework
from typing import Callable, List

from botbuilder.core import (
    TurnContext,
    BotAdapter, 
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    ConversationAccount,
    ResourceResponse,
)

ACTIVITY = Activity(
    id="1234",
    type="message",
    text="test",
    from_property=ChannelAccount(id="user", name="User Name"),
    recipient=ChannelAccount(id="bot", name="Bot Name"),
    conversation=ConversationAccount(id="convo", name="Convo Name"),
    channel_id="UnitTest",
    locale="en-uS",  # Intentionally oddly-cased to check that it isn't defaulted somewhere, but tests stay in English
    service_url="https://example.org",
)


class SimpleAdapter(BotAdapter):
    async def send_activities(self, context, activities) -> List[ResourceResponse]:
        responses = []
        assert context is not None
        assert activities is not None
        assert isinstance(activities, list)
        assert activities
        for (idx, activity) in enumerate(activities):  # pylint: disable=unused-variable
            assert isinstance(activity, Activity)
            assert activity.type == "message" or activity.type == ActivityTypes.trace
            responses.append(ResourceResponse(id="5678"))
        return responses

    async def update_activity(self, context, activity):
        assert context is not None
        assert activity is not None
        return ResourceResponse(id=activity.id)

    async def delete_activity(self, context, reference):
        assert context is not None
        assert reference is not None
        assert reference.activity_id == ACTIVITY.id


class Test_context(aiounittest.AsyncTestCase):

    def test_should_create_context_with_request_and_adapter(self):
        TurnContext(SimpleAdapter(), ACTIVITY)

    async def test_should_send_a_trace_activity(self):
        context = TurnContext(SimpleAdapter(), ACTIVITY)
        called = False

        #  pylint: disable=unused-argument
        async def aux_func(
            ctx: TurnContext, activities: List[Activity], next: Callable
        ):
            nonlocal called
            called = True
            assert isinstance(activities, list), "activities not array."
            assert len(activities) == 1, "invalid count of activities."
            assert activities[0].type == ActivityTypes.trace, "type wrong."
            assert activities[0].name == "name-text", "name wrong."
            assert activities[0].value == "value-text", "value worng."
            assert activities[0].value_type == "valueType-text", "valeuType wrong."
            assert activities[0].label == "label-text", "label wrong."
            return []

        context.on_send_activities(aux_func)
        await context.send_trace_activity(
            "name-text", "value-text", "valueType-text", "label-text"
        )
        assert called

if aiounittest.AsyncTestCase == '__main__':
    aiounittest.main()