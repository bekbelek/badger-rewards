from helpers.constants import DISABLED_VAULTS
from rewards.snapshot.token_snapshot import token_snapshot_usd
from rewards.explorer import convert_from_eth
from rich.console import Console
from config.env_config import env_config
from rewards.classes.UserBalance import UserBalances
from typing import Dict, List, Tuple
from collections import Counter
from rewards.snapshot.chain_snapshot import chain_snapshot
from badger_api.prices import (
    fetch_token_prices,
)

console = Console()
prices = fetch_token_prices()


def calc_union_addresses(
    nativeSetts: Dict[str, int], nonNativeSetts: Dict[str, int]
) -> List[str]:
    """
    Combine addresses from native setts and non native setts
    :param nativeSetts: native setts
    :param nonNativeSetts: non native setts
    """
    nativeAddresses = list(nativeSetts.keys())
    nonNativeAddresses = list(nonNativeSetts.keys())
    return list(set(nativeAddresses + nonNativeAddresses))


def filter_dust(balances: Dict[str, int], dustAmount: int) -> Dict[str, float]:
    """
    Filter out dust values from user balances
    :param balances: balances to filter
    :param dustAmount: dollar amount to filter by
    """
    return {addr: value for addr, value in balances.items() if value > dustAmount}


def convert_balances_to_usd(
    balances: UserBalances, sett: str
) -> Tuple[Dict[str, float], str]:
    """
    Convert sett balance to usd and multiply by correct ratio
    :param balances: balances to convert to usd
    """
    price = prices[env_config.get_web3().toChecksumAddress(sett)]
    priceRatio = balances.settRatio
    usdBalances = {}
    for user in balances:
        usdBalances[user.address] = priceRatio * price * user.balance

    return usdBalances, balances.settType


def calc_boost_data(block: int) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Calculate boost data required for boost calculation
    :param block: block to collect the boost data from
    """
    chains = [
        "polygon",
        # "bsc",
        "eth",
    ]
    blocksByChain = convert_from_eth(block)
    native = Counter()
    nonNative = Counter()
    for chain in chains:
        chainBlock = blocksByChain[chain]
        console.log("Taking chain snapshot on {} \n".format(chain))

        snapshot = chain_snapshot(chain, chainBlock)
        console.log("Taking token snapshot on {}".format(chain))

        tokens = token_snapshot_usd(chain, chainBlock)
        native = native + Counter(tokens)
        for sett, balances in snapshot.items():
            if sett in DISABLED_VAULTS:
                continue
            balances, settType = convert_balances_to_usd(balances, sett)
            if settType == "native":
                native = native + Counter(balances)
            elif settType == "nonNative":
                nonNative = nonNative + Counter(balances)

    native = filter_dust(dict(native), 1)
    nonNative = filter_dust(dict(nonNative), 1)
    return native, nonNative
