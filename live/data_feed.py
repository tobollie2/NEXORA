# /live/data_feed.py
import asyncio
import json
import logging
from datetime import datetime

import aiohttp


class KrakenDataFeed:
    """Async Kraken WebSocket feed for trades."""

    def __init__(self, symbols, queue: asyncio.Queue):
        self.url = "wss://ws.kraken.com/"
        self.symbols = symbols
        self.queue = queue
        self.session = None
        self.running = True

    async def _subscribe(self, ws):
        subs = {
            "event": "subscribe",
            "pair": self.symbols,
            "subscription": {"name": "trade"},
        }
        await ws.send_json(subs)
        logging.info(f"Subscribed to Kraken: {self.symbols}")

    async def connect(self):
        async with aiohttp.ClientSession() as self.session:
            while self.running:
                try:
                    async with self.session.ws_connect(self.url, heartbeat=30) as ws:
                        await self._subscribe(ws)
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(msg.data)
                                if isinstance(data, list) and len(data) > 1:
                                    await self.queue.put(
                                        {
                                            "timestamp": datetime.utcnow().isoformat(),
                                            "symbol": data[-1],
                                            "price": float(data[1][0][0]),
                                            "volume": float(data[1][0][1]),
                                        }
                                    )
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                except Exception as e:
                    logging.warning(f"Feed disconnected: {e}, reconnecting in 5s")
                    await asyncio.sleep(5)

    async def stop(self):
        self.running = False
        if self.session:
            await self.session.close()
