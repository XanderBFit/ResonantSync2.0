import asyncio
import time
import concurrent.futures

def blocking_io_task():
    """Simulates a blocking CPU or I/O task like librosa.load or GCS download."""
    time.sleep(2)
    return "Done"

async def heartbeat():
    """Measures event loop responsiveness."""
    lags = []
    for _ in range(25):
        start = time.perf_counter()
        await asyncio.sleep(0.1)
        end = time.perf_counter()
        lag = end - start - 0.1
        lags.append(max(0, lag))
    return lags

async def run_async_blocking():
    """Simulates an 'async def' endpoint that calls a blocking function directly."""
    print("\n--- Running ASYNC BLOCKING (Simulating 'async def' with blocking calls) ---")
    heartbeat_task = asyncio.create_task(heartbeat())
    await asyncio.sleep(0.2)

    print("Starting blocking task...")
    start_task = time.perf_counter()
    # This is what happens in the current 'async def' endpoints
    blocking_io_task()
    end_task = time.perf_counter()
    print(f"Blocking task took {end_task - start_task:.2f}s")

    lags = await heartbeat_task
    print(f"Max lag: {max(lags):.4f}s")
    print(f"Avg lag: {sum(lags)/len(lags):.4f}s")
    return max(lags)

async def run_threaded():
    """Simulates FastAPI's behavior for standard 'def' endpoints (running in thread pool)."""
    print("\n--- Running THREADED (Simulating standard 'def' behavior) ---")
    heartbeat_task = asyncio.create_task(heartbeat())
    await asyncio.sleep(0.2)

    loop = asyncio.get_running_loop()
    print("Starting blocking task in thread pool...")
    start_task = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, blocking_io_task)
    end_task = time.perf_counter()
    print(f"Blocking task took {end_task - start_task:.2f}s")

    lags = await heartbeat_task
    print(f"Max lag: {max(lags):.4f}s")
    print(f"Avg lag: {sum(lags)/len(lags):.4f}s")
    return max(lags)

async def main():
    max_lag_blocking = await run_async_blocking()
    await asyncio.sleep(1)
    max_lag_threaded = await run_threaded()

    print("\n" + "="*40)
    print(f"Blocking Max Lag: {max_lag_blocking:.4f}s")
    print(f"Threaded Max Lag: {max_lag_threaded:.4f}s")
    improvement = (max_lag_blocking - max_lag_threaded) / max_lag_blocking * 100
    print(f"Responsiveness Improvement: {improvement:.2f}%")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
