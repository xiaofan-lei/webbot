import aiounittest   # The test framework

from botbuilder.dialogs.prompts import (
    TextPrompt, 
    PromptOptions, 
)
from botbuilder.dialogs import DialogSet, DialogTurnStatus
from botbuilder.core.adapters import TestAdapter
from botbuilder.core import (
    ConversationState, 
    MemoryStorage, 
    TurnContext,
)
from botbuilder.schema import (
    Activity,
    ActivityTypes,
)


class Test_prompt(aiounittest.AsyncTestCase):

    async def test_textprompt(self):
        async def exec_test(turn_context:TurnContext):
            dialog_context = await dialogs.create_context(turn_context)

            results = await dialog_context.continue_dialog()
            if (results.status == DialogTurnStatus.Empty):
                options = PromptOptions(
                    prompt = Activity(
                        type = ActivityTypes.message, 
                        text = "how can I help you?"
                        )
                    )
                await dialog_context.prompt("text_prompt", options)

            elif results.status == DialogTurnStatus.Complete:
                reply = results.result
                await turn_context.send_activity(reply)

            await conv_state.save_changes(turn_context)

        adapter = TestAdapter(exec_test)
        conv_state = ConversationState(MemoryStorage())
        dialogs_state = conv_state.create_property("dialog-state")
        dialogs = DialogSet(dialogs_state)
        dialogs.add(TextPrompt("text_prompt"))

        step1 = await adapter.test('Hello', 'how can I help you?')
        step2 = await step1.send("I'd like to book a flight.")
        await step2.assert_reply("I'd like to book a flight.")

if aiounittest.AsyncTestCase == '__main__':
    aiounittest.main()