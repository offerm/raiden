import json

from raiden.storage.sqlite import SQLiteStorage

SOURCE_VERSION = 20
TARGET_VERSION = 21


def _transform_snapshot(raw_snapshot: str) -> str:
    snapshot = json.loads(raw_snapshot)

    for task in snapshot['payment_mapping']['secrethashes_to_task'].values():
        if 'raiden.transfer.state.InitiatorTask' in task['_type']:
            for initiator in task['manager_state']['initiator_transfers'].values():
                initiator['transfer_description']['allocated_fee'] = '0'

    ids_to_addrs = dict()
    for payment_network in snapshot['identifiers_to_paymentnetworks'].values():
        for token_network in payment_network['tokennetworks']:
            ids_to_addrs[payment_network['address']] = token_network['token_address']
    snapshot['tokennetworkaddresses_to_paymentnetworkaddresses'] = ids_to_addrs

    for payment_network in snapshot['identifiers_to_paymentnetworks'].values():
        for token_network in payment_network['tokennetworks']:
            for channel_state in token_network['channelidentifiers_to_channels'].values():
                channel_state['mediation_fee'] = '0'

    return json.dumps(snapshot)


def _update_snapshots(storage: SQLiteStorage):
    updated_snapshots_data = []
    for snapshot in storage.get_snapshots():
        new_snapshot = _transform_snapshot(snapshot.data)
        updated_snapshots_data.append((new_snapshot, snapshot.identifier))

    storage.update_snapshots(updated_snapshots_data)


def _update_statechanges(storage: SQLiteStorage):
    batch_size = 50
    batch_query = storage.batch_query_state_changes(
        batch_size=batch_size,
        filters=[
            ('_type', 'raiden.transfer.state_change.ContractReceiveChannelNew'),
        ],
    )

    for state_changes_batch in batch_query:
        updated_state_changes = list()
        for state_change in state_changes_batch:
            data = json.loads(state_change.data)
            data['channel_state']['mediation_fee'] = '0'

            updated_state_changes.append((
                json.dumps(data),
                state_change.state_change_identifier,
            ))

        storage.update_state_changes(updated_state_changes)

    batch_query = storage.batch_query_state_changes(
        batch_size=batch_size,
        filters=[
            ('_type', 'raiden.transfer.mediated_transfer.state_change.ActionInitInitiator'),
        ],
    )

    for state_changes_batch in batch_query:
        updated_state_changes = list()
        for state_change in state_changes_batch:
            data = json.loads(state_change.data)
            data['transfer']['allocated_fee'] = '0'

            updated_state_changes.append((
                json.dumps(data),
                state_change.state_change_identifier,
            ))

        storage.update_state_changes(updated_state_changes)


def upgrade_v20_to_v21(
        storage: SQLiteStorage,
        old_version: int,
        current_version: int,
        **kwargs,  # pylint: disable=unused-argument
) -> int:
    if old_version == SOURCE_VERSION:
        _update_snapshots(storage)
        _update_statechanges(storage)

    return TARGET_VERSION
