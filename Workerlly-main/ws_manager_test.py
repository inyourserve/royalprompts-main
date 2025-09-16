# Test script to check current WebSocket manager behavior
from app.utils.websocket_manager import manager


async def test_websocket_behavior():
    # Test 1: Send to non-existent user
    try:
        await manager.send_personal_message({"test": "message"}, "non_existent_user")
        print("❌ No exception thrown for missing user - FCM won't trigger!")
    except Exception as e:
        print("✅ Exception thrown for missing user - FCM will trigger")

    # Test 2: Send to existing user (if any connected)
    try:
        if manager.active_connections:
            user_id = list(manager.active_connections.keys())[0]
            await manager.send_personal_message({"test": "message"}, user_id)
            print("✅ Message sent to connected user successfully")
        else:
            print("No users connected to test with")
    except Exception as e:
        print(f"Exception during send: {e}")
