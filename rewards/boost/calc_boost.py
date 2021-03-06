from rich.console import Console
from helpers.constants import (
    STAKE_RATIO_RANGES,
)
from typing import Dict
from tabulate import tabulate

from rewards.boost.boost_utils import (
    calc_union_addresses,
    calc_boost_data,
)

console = Console()


def calc_stake_ratio(
    address: str, nativeSetts: Dict[str, int], nonNativeSetts: Dict[str, int]
):
    """
    Calculate the stake ratio for an address
    :param address: address to find stake ratio for
    :param nativeSetts: native balances
    :param nonNativeSetts: non native balances
    """
    nativeBalance = nativeSetts.get(address.lower(), 0)
    nonNativeBalance = nonNativeSetts.get(address.lower(), 0)
    if nonNativeBalance == 0 or nativeBalance == 0:
        stakeRatio = 0
    else:
        stakeRatio = (nativeBalance) / nonNativeBalance
    return stakeRatio


def badger_boost(currentBlock: int):
    """
    Calculate badger boost multipliers based on stake ratios
    :param badger: badger system
    :param currentBlock: block to calculate boost at
    """
    console.log("Calculating boost at block {} ...".format(currentBlock))
    nativeSetts, nonNativeSetts = calc_boost_data(currentBlock - 10)
    console.log(len(nativeSetts))
    console.log(len(nonNativeSetts))

    allAddresses = calc_union_addresses(nativeSetts, nonNativeSetts)
    console.log("{} addresses fetched".format(len(allAddresses)))
    badgerBoost = {}
    boostInfo = {}
    boostData = {}

    stakeRatiosList = [
        calc_stake_ratio(addr, nativeSetts, nonNativeSetts) for addr in allAddresses
    ]

    stakeRatios = dict(zip(allAddresses, stakeRatiosList))

    boostInfo = {}
    for addr in allAddresses:
        boostInfo[addr] = {"nativeBalance": 0, "nonNativeBalance": 0, "stakeRatio": 0}

    for user, nativeUsd in nativeSetts.items():
        boostInfo[user.lower()]["nativeBalance"] = nativeUsd

    for user, nonNativeUsd in nonNativeSetts.items():
        boostInfo[user.lower()]["nonNativeBalance"] = nonNativeUsd

    for addr, ratio in stakeRatios.items():
        boostInfo[addr.lower()]["stakeRatio"] = ratio

    stakeData = {}
    console.log(STAKE_RATIO_RANGES)
    for addr, stakeRatio in stakeRatios.items():
        if stakeRatio == 0:
            badgerBoost[addr] = 1
        else:
            userBoost = 1
            userStakeRange = 0
            for stakeRange, multiplier in STAKE_RATIO_RANGES:
                if stakeRatio > stakeRange:
                    userBoost = multiplier
                    userStakeRange = stakeRange

            stakeData[userStakeRange] = stakeData.get(userStakeRange, 0) + 1
            badgerBoost[addr] = userBoost

    for addr, boost in badgerBoost.items():
        boostMetaData = boostInfo.get(addr, {})
        boostData[addr] = {
            "boost": boost,
            "nativeBalance": boostMetaData.get("nativeBalance", 0),
            "nonNativeBalance": boostMetaData.get("nonNativeBalance", 0),
            "stakeRatio": boostMetaData.get("stakeRatio", 0),
            "multipliers": {},
        }

    print(
        tabulate(
            [[rng, amount] for rng, amount in stakeData.items()],
            headers=["range", "amount of users"],
        )
    )

    return boostData
