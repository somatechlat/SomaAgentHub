        """Helper utilities for optional Redis caching."""

        from __future__ import annotations
        from services.common.config.base_settings import resolve_env

        try:  # pragma: no cover - environment guard
        from redis.asyncio import Redis
        from redis.asyncio import from_url as redis_from_url
        except Exception:  # pragma: no cover - redis not installed
        Redis = None  # type: ignore
        redis_from_url = None  # type: ignore


        async def create_redis_client(url: str) -> Redis | None:
            if redis_from_url is None:
                return None

                client: Redis = redis_from_url(url, decode_responses=True)
                try:
                    await client.ping()
                    except Exception:  # pragma: no cover - connection failure
                    await close_redis_client(client)
                    return None
                    return client


                    async def close_redis_client(client: Redis | None) -> None:
                        if client is not None:
                            close = getattr(client, "aclose", None)
                            if callable(close):
                                await close()
                                else:  # pragma: no cover - older redis clients
                                await client.close()
