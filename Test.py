from Utils.NetworkUtils import NetworkUtils
import asyncio

async def main():
    net = NetworkUtils()
    status, content_type = await net.website_check("http://node-11.zeno.fm/8u6kahy9b9quv?listening-from-radio-garden=1590104920814&rj-tok=AAABcjmsu5IAqDzV96J6-FeGHg&rj-ttl=5")
    print(status, content_type)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

loop.close()