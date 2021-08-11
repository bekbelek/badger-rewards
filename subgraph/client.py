from subgraph.subgraph_utils import make_gql_client
from brownie import interface
from rich.console import Console
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from decimal import *
import math
from functools import lru_cache

getcontext().prec = 20
console = Console()

tokens_client = make_gql_client("tokens")
harvests_client = make_gql_client("harvests")

## TODO: seperate files by chain/subgraph


def fetch_tree_distributions(startBlock, endBlock):
    query = gql(
        """
        query tree_distributions(
            $blockHeight: Block_height
            $lastDistId: TreeDistribution_filter
            ) {
            treeDistributions(block: $blockHeight, where: $lastDistId) {
                id
                token {
                    address
                    symbol
                }
                amount
                blockNumber
                }
            }
        """
    )
    lastDistId = "0x0000000000000000000000000000000000000000"
    variables = {"blockHeight": {"number": endBlock}}
    treeDistributions = []
    while True:
        variables["lastDistId"] = {"id_gt": lastDistId}
        results = harvests_client.execute(query, variable_values=variables)
        distData = results["treeDistributions"]
        if len(distData) == 0:
            break
        else:
            treeDistributions = [*treeDistributions, *distData]
        if len(distData) > 0:
            lastDistId = distData[-1]["id"]
    return [td for td in treeDistributions if int(td["blockNumber"]) > int(startBlock)]



def fetch_farm_harvest_events():
    query = gql(
        """
        query fetch_harvest_events {
            farmHarvestEvents(first:1000,orderBy: blockNumber,orderDirection:asc) {
                id
                farmToRewards
                blockNumber
                totalFarmHarvested
                timestamp
            }
        }

    """
    )
    results = harvests_client.execute(query)
    for event in results["farmHarvestEvents"]:
        event["rewardAmount"] = event.pop("farmToRewards")

    return results["farmHarvestEvents"]


def fetch_sushi_harvest_events():
    query = gql(
        """
        query fetch_harvest_events {
            sushiHarvestEvents(first:1000,orderBy:blockNumber,orderDirection:asc) {
                id
                xSushiHarvested
                totalxSushi
                toStrategist
                toBadgerTree
                toGovernance
                timestamp
                blockNumber
            }
        }
    """
    )
    results = harvests_client.execute(query)
    wbtcEthEvents = []
    wbtcBadgerEvents = []
    wbtcDiggEvents = []
    iBbtcWbtcEvents = []
    for event in results["sushiHarvestEvents"]:
        event["rewardAmount"] = event.pop("toBadgerTree")
        strategy = event["id"].split("-")[0]
        if strategy == "0x7a56d65254705b4def63c68488c0182968c452ce":
            wbtcEthEvents.append(event)
        elif strategy == "0x3a494d79aa78118795daad8aeff5825c6c8df7f1":
            wbtcBadgerEvents.append(event)
        elif strategy == "0xaa8dddfe7dfa3c3269f1910d89e4413dd006d08a":
            wbtcDiggEvents.append(event)
        elif strategy == "0xf4146a176b09c664978e03d28d07db4431525dad":
            iBbtcWbtcEvents.append(event)

    return {
        "wbtcEth": wbtcEthEvents,
        "wbtcBadger": wbtcBadgerEvents,
        "wbtcDigg": wbtcDiggEvents,
        "iBbtcWbtc": iBbtcWbtcEvents,
    }


@lru_cache(maxsize=None)
def fetch_wallet_balances(sharesPerFragment, blockNumber):
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
    ibbtc_balances = {}
    console.log(sharesPerFragment)
    while continueFetching:
        variables = {
            "firstAmount": increment,
            "lastID": lastID,
            "blockNumber": {"number": blockNumber},
        }
        nextPage = tokens_client.execute(query, variable_values=variables)
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
                    if entry["token"]["symbol"] == "ibBTC":
                        if (
                            address
                            == "0x18d98D452072Ac2EB7b74ce3DB723374360539f1".lower()
                        ):
                            # Ignore sushiswap pool
                            ibbtc_balances[address] = 0
                        else:
                            ibbtc_balances[address] = amount / 1e18

    return badger_balances, digg_balances, ibbtc_balances


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
                netDeposit
            }
        }
        """
    )
    lastId = ""
    variables = {"blockHeight": {"number": block}}
    balances = {}
    while True:
        variables["lastId"] = {"id_gt": lastId}
        results = client.execute(query, variable_values=variables)
        newBalances = {}
        balanceData = results["userSettBalances"]
        for result in balanceData:
            account = result["user"]["id"]
            deposit = float(result["netDeposit"])
            decimals = int(result["sett"]["token"]["decimals"])
            sett = result["sett"]["id"]
            if deposit > 0:
                if sett not in newBalances:
                    newBalances[sett] = {}
                newBalances[sett][account.lower()] = deposit / math.pow(10, decimals)

        if len(balanceData) == 0:
            break
        else:
            console.log("Fetching {} sett balances".format(len(balanceData)))
            lastId = balanceData[-1]["id"]
            for settAddr, newBals in newBalances.items():
                if settAddr not in balances:
                    balances[settAddr] = {}
                balances[settAddr] = {**balances[settAddr], **newBals}
    console.log("Fetched {} total sett balances".format(len(balances)))
    return balances