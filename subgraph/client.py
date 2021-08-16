import asyncio
from helpers.discord import send_message_to_discord
from subgraph.subgraph_utils import make_gql_client
from rich.console import Console
from gql import gql
from decimal import *
import math
from functools import lru_cache
import backoff

getcontext().prec = 20
console = Console()

tokens_client = make_gql_client("tokens")
harvests_client = make_gql_client("harvests")

@lru_cache(maxsize=None)
@backoff.on_exception(backoff.expo, asyncio.exceptions.TimeoutError, max_time=35)
@backoff.on_exception(backoff.expo, asyncio.exceptions.CancelledError, max_time=35)
def fetch_token_balances(client, sharesPerFragment, blockNumber):
    increment = 1000
    query = gql(
        """
        query fetchWalletBalance($firstAmount: Int, $lastID: ID,$blockNumber:Block_height) {
            tokenBalances(first: $firstAmount, where: { id_gt: $lastID  },block: $blockNumber) {
                id
                balance
                token {
                    symbol
                }
            }
        }
    """
    )

    ## Paginate this for more than 1000 balances
    continueFetching = True
    lastID = "0x0000000000000000000000000000000000000000"

    badger_balances = {}
    digg_balances = {}
    while continueFetching:
        try:
            variables = {
                "firstAmount": increment,
                "lastID": lastID,
                "blockNumber": {"number": blockNumber - 50},
            }
            nextPage = client.execute(query, variable_values=variables)
            if len(nextPage["tokenBalances"]) == 0:
                continueFetching = False
            else:
                lastID = nextPage["tokenBalances"][-1]["id"]
                console.log(
                    "Fetching {} token balances".format(len(nextPage["tokenBalances"]))
                )
                for entry in nextPage["tokenBalances"]:
                    address = entry["id"].split("-")[0]
                    amount = float(entry["balance"])
                    if amount > 0:
                        if entry["token"]["symbol"] == "BADGER":
                            badger_balances[address] = amount / 1e18
                        if entry["token"]["symbol"] == "DIGG":
                            # Speed this up
                            if entry["balance"] == 0:
                                fragmentBalance = 0
                            else:
                                fragmentBalance = sharesPerFragment / amount
                            digg_balances[address] = float(fragmentBalance) / 1e9
        except (asyncio.exceptions.TimeoutError, asyncio.exceptions.CancelledError):
            pass
        except Exception as e:
            send_message_to_discord(
                "**BADGER BOOST ERROR**",
                f":x: Error in Fetching Token Balance",
                [
                    {
                        "name": "Error Type",
                        "value": type(e),
                        "inline": True,
                        "name": "Error Description",
                        "value": e.args,
                        "inline": True,
                    }
                ],
                "Boost Bot",
            )
            console.log(type(e))
            raise e

    return badger_balances, digg_balances

@backoff.on_exception(backoff.expo, asyncio.exceptions.TimeoutError, max_time=35)
@backoff.on_exception(backoff.expo, asyncio.exceptions.CancelledError, max_time=35)
def fetch_chain_balances(chain, block):
    client = make_gql_client(chain)
    query = gql(
        """
        query balances($blockHeight: Block_height,$lastId:UserSettBalance_filter) {
            userSettBalances(first: 1000, block: $blockHeight, where:$lastId) {
                id
                user {
                    id
                }
                sett {
                    id
                    token{
                        decimals
                    }
                }
                netShareDeposit
            }
        }
        """
    )
    lastId = ""
    variables = {"blockHeight": {"number": block}}
    balances = {}

    while True:
        try:
            variables["lastId"] = {"id_gt": lastId}
            results = client.execute(query, variable_values=variables)
            balanceData = results["userSettBalances"]
            for result in balanceData:
                account = result["user"]["id"].lower()
                decimals = int(result["sett"]["token"]["decimals"])
                sett = result["sett"]["id"]
                if sett == "0x7e7E112A68d8D2E221E11047a72fFC1065c38e1a".lower():
                    decimals = 18
                deposit = float(result["netShareDeposit"]) / math.pow(10, decimals)
                if deposit > 0:
                    if sett not in balances:
                        balances[sett] = {}

                    if account not in balances[sett]:
                        balances[sett][account] = deposit
                    else:
                        balances[sett][account] += deposit

            if len(balanceData) == 0:
                break
            else:
                console.log("Fetching {} sett balances".format(len(balanceData)))
                lastId = balanceData[-1]["id"]
            console.log("Fetched {} total sett balances".format(len(balances)))
            return balances
        except (asyncio.exceptions.TimeoutError, asyncio.exceptions.CancelledError):
            pass
        except Exception as e:
            send_message_to_discord(
                "**BADGER BOOST ERROR**",
                f":x: Error in Fetching Chain Balance",
                [
                    {
                        "name": "Error Type",
                        "value": type(e),
                        "inline": True,
                        "name": "Error Description",
                        "value": e.args,
                        "inline": True,
                    }
                ],
                "Boost Bot",
            )
            raise e
