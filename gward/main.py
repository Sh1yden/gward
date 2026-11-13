"""Main run gward."""


def main():
    from asyncio import run

    print("Hello Gward!!!")

    run(async_main())


async def async_main():
    print("Hello Async Gward!!!")
