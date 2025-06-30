import discord
import asyncio
from datetime import datetime


class LicenseVerifier:
    def __init__(self, bot_token: str, channel_id: int):
        self.bot_token = bot_token
        self.channel_id = channel_id
        self.client = discord.Client(intents=discord.Intents.default())
        self.loop = asyncio.get_event_loop()

    def verify_license(self, license_key: str) -> bool:
        return self.loop.run_until_complete(self._verify(license_key))

    async def _verify(self, license_key: str) -> bool:
        try:
            await self.client.login(self.bot_token)
            channel = await self.client.fetch_channel(self.channel_id)

            async for message in channel.history(limit=100):
                for embed in message.embeds:
                    embed_fields = {
                        field.name.strip().lower(): field.value.strip()
                        for field in embed.fields
                    }

                    embed_license_key = embed_fields.get("license key")
                    embed_expiry = embed_fields.get("expiration")

                    if embed_license_key == license_key:
                        if not embed_expiry:
                            print("[❌] 'Expiration' field is missing or empty.")
                            await self.client.close()
                            return False
                        try:
                            expiry_date = datetime.strptime(embed_expiry, "%Y-%m-%d")
                            if datetime.now() <= expiry_date:
                                print(f"[✅] License valid. Expires on {expiry_date.date()}")
                                await self.client.close()
                                return True
                            else:
                                print(f"[❌] License expired on {expiry_date.date()}")
                                await self.client.close()
                                return False
                        except Exception as e:
                            print(f"[❌] Error parsing date '{embed_expiry}': {e}")
                            await self.client.close()
                            return False

            print("[❌] License not found.")
            await self.client.close()
            return False

        except Exception as e:
            print(f"[❌] License verification error: {e}")
            return False

    def get_license_expiry(self, license_key: str) -> float | None:
        return self.loop.run_until_complete(self._get_expiry(license_key))

    async def _get_expiry(self, license_key: str) -> float | None:
        try:
            await self.client.login(self.bot_token)
            channel = await self.client.fetch_channel(self.channel_id)

            async for message in channel.history(limit=100):
                for embed in message.embeds:
                    embed_fields = {
                        field.name.strip().lower(): field.value.strip()
                        for field in embed.fields
                    }
                    embed_license_key = embed_fields.get("license key")
                    embed_expiry = embed_fields.get("expiration")

                    if embed_license_key == license_key:
                        if not embed_expiry:
                            print("[❌] 'Expiration' field is missing or empty.")
                            await self.client.close()
                            return None
                        try:
                            expiry_date = datetime.strptime(embed_expiry, "%Y-%m-%d")
                            await self.client.close()
                            return expiry_date.timestamp()
                        except Exception as e:
                            print(f"[❌] Error parsing date '{embed_expiry}': {e}")
                            await self.client.close()
                            return None

            await self.client.close()
            return None

        except Exception as e:
            print(f"[❌] Error retrieving license expiration: {e}")
            return None