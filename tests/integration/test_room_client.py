from unittest.mock import Mock

from NetUtils import NetworkItem, NetworkSlot
from test_client import connected_context, run_async

from gamma_archipelago.catalog import GAME


@run_async
async def test_foreign_self_awards_are_room_news_and_not_local_receipts():
    context = connected_context()
    context.slot_info[2] = NetworkSlot("Dave", "Terraria", 1)
    context.player_names[2] = "Dave"
    context.item_names.update_game("Terraria", {"Sword": 28051001})
    packet = {"type": "ItemSend", "receiving": 2, "item": NetworkItem(28051001, 28052003, 2)}
    context.on_package("PrintJSON", packet)
    assert not context.room.messages  # Source metadata has not arrived.
    context.location_names.update_game("Terraria", {"Slime King": 28052003})
    context.on_package("DataPackage", {})
    assert context.room.messages[0].text == 'Dave gave "Sword" to Dave by completing "Slime King".'
    context.on_package("PrintJSON", packet)
    assert len(context.room.messages) == 1
    assert not context.session.item_ids and not context.session.notices


@run_async
async def test_foreign_cross_player_and_gamma_unlock_labels_use_correct_games():
    context = connected_context()
    context.slot_info[2] = NetworkSlot("Dave", GAME, 1)
    context.slot_info[3] = NetworkSlot("Mini", GAME, 1)
    context.player_names.update({2: "Dave", 3: "Mini"})
    context.on_package(
        "PrintJSON",
        {
            "type": "ItemSend",
            "receiving": 3,
            "item": NetworkItem(28051102, 28052003, 2),
        },
    )
    assert "Dave" in context.room.messages[0].text and "Mini" in context.room.messages[0].text
    assert context.room.messages[0].text.endswith("by entering Rostok.")


@run_async
async def test_room_feed_does_not_duplicate_own_transfers_and_handles_chat_replies():
    context = connected_context()
    for finder, receiver in ((1, 1), (2, 1), (1, 2)):
        context.on_package(
            "PrintJSON",
            {
                "type": "ItemSend",
                "receiving": receiver,
                "item": NetworkItem(28051001, 28052003, finder),
            },
        )
    assert not context.room.messages
    for packet in ({}, {"type": "Unknown", "data": []}, {"type": "Chat", "data": "bad"}):
        context.on_package("PrintJSON", packet)
    context.on_package("Print", {"text": 12})
    context.on_package("Print", {"text": "Hint points: 4"})
    context.jsontotextparser = lambda data: data[0]["text"]
    context.on_package("PrintJSON", {"type": "Chat", "data": [{"text": "Dave: Hello"}]})
    assert [message.text for message in context.room.messages] == ["Hint points: 4", "Dave: Hello"]
    for _ in range(70):
        context.room.append(" ")
        context.room.append("message")
    assert len(context.room.messages) == 64
    context.bridge.write_room_feed = Mock()
    await context.poll_game_once()
    assert context.bridge.write_room_feed.call_args.args[2] == context.room.epoch


@run_async
async def test_unknown_recipient_and_unknown_item_wait_for_metadata():
    context = connected_context()
    packet = {"type": "ItemSend", "receiving": 3, "item": NetworkItem(99, 28052003, 2)}
    context.on_package("PrintJSON", packet)
    context.slot_info[3] = NetworkSlot("Mini", GAME, 1)
    context.on_package("DataPackage", {})
    assert not context.room.messages
    context.slot_info[2] = NetworkSlot("Dave", GAME, 1)
    context.item_names.update_game(GAME, {"Future reward": 99})
    context.on_package("DataPackage", {})
    assert len(context.room.messages) == 1
