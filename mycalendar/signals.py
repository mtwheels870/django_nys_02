async def my_callback(sender, **kwargs):
    await asyncio.sleep(5)
    print(f"signals.my_callback(), Request finished, sender = {sender}")
