import aiounittest   # The test framework
from botbuilder.core.adapters import TestAdapter, TestFlow
from botbuilder.core import (
    TurnContext,
    TelemetryLoggerMiddleware,
    NullTelemetryClient,
)

class Test_telemetry(aiounittest.AsyncTestCase):
    async def test_create_telemetry_middleware(self):
        telemetry = NullTelemetryClient()
        my_logger = TelemetryLoggerMiddleware(telemetry, True)
        assert my_logger

    async def test_none_telemetry_client(self):
        my_logger = TelemetryLoggerMiddleware(None, True)

        async def logic(context: TurnContext):
            await context.send_activity(f"echo:{context.activity.text}")

        adapter = TestAdapter(logic)
        adapter.use(my_logger)
        test_flow = TestFlow(None, adapter)
        test_flow = await test_flow.send("foo")
        test_flow = await test_flow.assert_reply("echo:foo")
        test_flow = await test_flow.send("bar")
        await test_flow.assert_reply("echo:bar")

  
if aiounittest.AsyncTestCase == '__main__':
    aiounittest.main()