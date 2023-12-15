#!/usr/bin/env python3

import asyncio


class TradeRunner:
    def __init__(self):
        # initialize managers
        pass

    async def run(self):
        # run strategies

        # find unassigned decisions
        # need decision -> strategy mapping
        # assign decisions to strategies

        # run strategies to find new opportunities
        pass


# Usage
async def main():
    trade_runner = TradeRunner()
    trade_task = asyncio.create_task(trade_runner.run())

    await trade_task


asyncio.run(main())
