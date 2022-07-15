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

    def test_responded_should_be_automatically_set_to_false(self):
        context = TurnContext(SimpleAdapter(), ACTIVITY)
        assert context.responded is False

if aiounittest.AsyncTestCase == '__main__':
    aiounittest.main()