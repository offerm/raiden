import pytest
from eth_utils import to_canonical_address, to_checksum_address

from raiden.network.proxies import SecretRegistry, Token, TokenNetwork, TokenNetworkRegistry
from raiden.tests.utils import factories
from raiden.tests.utils.smartcontracts import deploy_token
from raiden_contracts.constants import (
    CONTRACT_SECRET_REGISTRY,
    CONTRACT_TOKEN_NETWORK,
    CONTRACT_TOKEN_NETWORK_REGISTRY,
    TEST_SETTLE_TIMEOUT_MAX,
    TEST_SETTLE_TIMEOUT_MIN,
)


@pytest.fixture(name='secret_registry_contract_address')
def deploy_secret_register_and_return_jsonrpc_proxy(deploy_client, contract_manager):
    """This uses the JSONRPCClient to deploy the secret registry smart
    contract, and returns a JSONRPCClient proxy to interact with the smart
    contract.
    """
    compiled = {
        CONTRACT_SECRET_REGISTRY: contract_manager.get_contract(CONTRACT_SECRET_REGISTRY),
    }
    secret_registry_proxy_ = deploy_client.deploy_solidity_contract(
        CONTRACT_SECRET_REGISTRY,
        compiled,
    )
    return secret_registry_proxy_.contract.address


@pytest.fixture
def secret_registry_proxy(deploy_client, secret_registry_contract_address, contract_manager):
    """This uses the available SecretRegistry JSONRPCClient proxy to
    instantiate a Raiden proxy.

    The JSONRPCClient proxy just exposes the functions from the smart contract
    as methods in a generate python object, the Raiden proxy uses it to
    provider alternative interfaces *and* most importantly to do additional
    error checking (reason for transaction failure, gas usage, etc.).
    """
    return SecretRegistry(
        jsonrpc_client=deploy_client,
        secret_registry_address=to_canonical_address(secret_registry_contract_address),
        contract_manager=contract_manager,
    )


@pytest.fixture(name='token_network_registry_contract')
def deploy_token_network_registry_and_return_jsonrpc_proxy(
        chain_id,
        deploy_client,
        contract_manager,
        secret_registry_contract_address,
):
    compiled = {
        CONTRACT_TOKEN_NETWORK_REGISTRY: contract_manager.get_contract(
            CONTRACT_TOKEN_NETWORK_REGISTRY,
        ),
    }
    return deploy_client.deploy_solidity_contract(
        CONTRACT_TOKEN_NETWORK_REGISTRY,
        compiled,
        constructor_parameters=[
            secret_registry_contract_address,
            chain_id,
            TEST_SETTLE_TIMEOUT_MIN,
            TEST_SETTLE_TIMEOUT_MAX,
        ],
    )


@pytest.fixture
def token_network_registry_proxy(deploy_client, token_network_registry_contract, contract_manager):
    return TokenNetworkRegistry(
        jsonrpc_client=deploy_client,
        registry_address=to_canonical_address(token_network_registry_contract.contract.address),
        contract_manager=contract_manager,
    )


@pytest.fixture(name='token_network_contract')
def deploy_token_network_and_return_jsonrpc_proxy(
        chain_id,
        deploy_client,
        secret_registry_contract_address,
        token_contract,
        contract_manager,
):
    compiled = {
        CONTRACT_TOKEN_NETWORK: contract_manager.get_contract(
            CONTRACT_TOKEN_NETWORK,
        ),
    }
    return deploy_client.deploy_solidity_contract(
        CONTRACT_TOKEN_NETWORK,
        compiled,
        constructor_parameters=[
            token_contract.contract.address,
            secret_registry_contract_address,
            chain_id,
            TEST_SETTLE_TIMEOUT_MIN,
            TEST_SETTLE_TIMEOUT_MAX,
            to_checksum_address(factories.make_address()),
        ],
    )


@pytest.fixture
def token_network_proxy(deploy_client, token_network_contract, contract_manager):
    return TokenNetwork(
        jsonrpc_client=deploy_client,
        token_network_address=to_canonical_address(token_network_contract.contract.address),
        contract_manager=contract_manager,
    )


@pytest.fixture(name='token_contract')
def deploy_network_and_return_jsonrpc_proxy(deploy_client, contract_manager):
    return deploy_token(
        deploy_client=deploy_client,
        contract_manager=contract_manager,
        initial_amount=10000,
        decimals=0,
        token_name='TKN',
        token_symbol='TKN',
    )


@pytest.fixture
def token_proxy(deploy_client, token_contract, contract_manager):
    return Token(
        jsonrpc_client=deploy_client,
        token_address=to_canonical_address(token_contract.contract.address),
        contract_manager=contract_manager,
    )
