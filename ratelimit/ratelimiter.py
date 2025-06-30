import asyncio
import time
import logging
import discord

class AsyncRateLimiter:
    def __init__(self, max_calls, per_seconds):
        self.max_calls = max_calls
        self.per_seconds = per_seconds
        self.calls = []

    async def wait(self):
        now = time.monotonic()
        self.calls = [t for t in self.calls if now - t < self.per_seconds]

        if len(self.calls) >= self.max_calls:
            sleep_for = self.per_seconds - (now - self.calls[0])
            if sleep_for > 0:
                logging.info(f"[!] ⏳ Rate limit coming, waiting {sleep_for:.2f}s")
                await asyncio.sleep(sleep_for)

        self.calls.append(time.monotonic())

rate_limiter = AsyncRateLimiter(max_calls=10, per_seconds=2)

async def safe_create(obj_func, *args, **kwargs):
    await rate_limiter.wait()
    for attempt in range(5):
        try:
            logging.debug(f"[SAFE_CREATE] Chance {attempt + 1} to create: {obj_func.__name__} with args={args}, kwargs={kwargs}")
            result = await obj_func(*args, **kwargs)
            logging.info(f"[SAFE_CREATE] ✅ Create successfull: {obj_func.__name__}")
            return result
        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = getattr(e, "retry_after", 2 ** attempt)
                logging.warning(f"[SAFE_CREATE] ⏳ Rate limit reached for {obj_func.__name__}. Coming in {retry_after:.2f} seconds (chance {attempt + 1}/5)")
                await asyncio.sleep(retry_after)
            else:
                logging.error(f"[SAFE_CREATE] ❌ Error while creating {obj_func.__name__}: {e}")
                raise
        except Exception as e:
            logging.error(f"[SAFE_CREATE] ❌ Error in {obj_func.__name__}: {e}")
            raise
    logging.error(f"[SAFE_CREATE] ❌ unsuccessfull all chance for creating: {obj_func.__name__}")