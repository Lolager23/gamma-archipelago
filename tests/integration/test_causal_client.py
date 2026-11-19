from NetUtils import NetworkItem, NetworkSlot
from test_client import connected_context, run_async
from worlds.gamma.notices import source_cause

from gamma_archipelago.catalog import GAME, KILL_MILESTONE_BASE
from gamma_archipelago.notice_causes import CheckCause


@run_async
async def test_received_reward_names_the_senders_check_and_keeps_receipt_identity():
    context = connected_context()
    context.slot_info[2] = NetworkSlot("Friend", GAME, 1)
    context.player_names[2] = "Friend"
    context.items_received = [NetworkItem(28051001, 28052003, 2)]
    context.on_package("ReceivedItems", {})
    message = context.session.notices["r:0"]
    assert message.text == 'Friend gave you "Basic Toolkit" by entering Rostok.'
    assert message.minimum_received == 1 and context.session.item_ids == (28051001,)
    context.received_notices()
    assert len(context.session.notices) == 1


@run_async
async def test_foreign_source_id_collision_uses_its_own_datapackage_and_waits_for_metadata():
    context = connected_context()
    context.slot_info[2] = NetworkSlot("Friend", "Foreign Game", 1)
    context.items_received = [NetworkItem(28051001, 28052003, 2)]
    context.on_package("ReceivedItems", {})
    assert context.session.item_ids == (28051001,) and not context.session.notices
    context.location_names.update_game("Foreign Game", {"Defeat the Dragon": 28052003})
    context.on_package("DataPackage", {})
    assert context.session.notices["r:0"].text == (
        'Player 2 gave you "Basic Toolkit" by completing "Defeat the Dragon".'
    )
    assert context.session.notices["r:0"].transfer.cause.kind == "check"


@run_async
async def test_outgoing_foreign_reward_uses_the_local_kill_check_and_recipient_item_namespace():
    context = connected_context()
    context.slot_info[2] = NetworkSlot("James", "Foreign Game", 1)
    context.player_names[2] = "James"
    context.item_names.update_game("Foreign Game", {"Foreign Currency": 28051602})
    context.sent_notice(NetworkItem(28051602, KILL_MILESTONE_BASE + 15, 1), 2)
    message = next(iter(context.session.notices.values()))
    assert message.text == 'You sent "Foreign Currency" to James by killing 15 hostiles.'
    assert message.transfer.local_item_id == 0
    context.sent_notice(NetworkItem(28051602, 99, 1), 2)
    assert len(context.session.notices) == 1  # Missing source metadata stays pending.


@run_async
async def test_self_award_uses_one_incoming_notice_with_its_actual_rank_check():
    context = connected_context()
    context.items_received = [NetworkItem(28051001, 28052808, 1)]
    context.on_package("ReceivedItems", {})
    context.on_package(
        "PrintJSON",
        {"type": "ItemSend", "receiving": 1, "item": NetworkItem(28051001, 28052808, 1)},
    )
    assert list(context.session.notices) == ["r:0"]
    assert context.session.notices["r:0"].text.endswith("for reaching Legend rank.")


@run_async
async def test_source_resolution_rejects_invalid_metadata_and_labels_server_items():
    context = connected_context()
    for location, slot in [(True, 1), (2**53, 1), (3, "1"), (3, 99), (99, 1)]:
        assert source_cause(context, location, slot) is None
    assert source_cause(context, 28052101, 1) == CheckCause("enter", "Rookie Village")
    assert source_cause(context, -1, 0) == CheckCause("source", "Cheat Console")
    context.slot_info[2] = NetworkSlot("Friend", GAME, 1)
    context.location_names.update_game(GAME, {"Future GAMMA check": 99})
    assert source_cause(context, 99, 2) == CheckCause("check", "Future GAMMA check")
    context.location_names.lookup_in_game = lambda *_: None
    assert source_cause(context, 99, 2) is None
    context.session = None
    context.received_notices()
    context.sent_notice(NetworkItem(1, 28052003, 1), 2)
