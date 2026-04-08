import asyncio
import time
import statistics

async def heartbeat(interval, stop_event, lags):
    """Monitor event loop lag."""
    while not stop_event.is_set():
        start_time = time.perf_counter()
        await asyncio.sleep(interval)
        actual_elapsed = time.perf_counter() - start_time
        lag = actual_elapsed - interval
        lags.append(max(0, lag))

def blocking_work(duration=1.0):
    """Simulate CPU-bound/blocking I/O work."""
    time.sleep(duration)
    return "done"

async def async_blocking_task(duration):
    """Simulates current async def endpoint behavior."""
    blocking_work(duration)

async def threaded_blocking_task(duration):
    """Simulates def endpoint behavior (offloaded to thread)."""
    await asyncio.to_thread(blocking_work, duration)

async def run_benchmark(name, task_func, duration=1.0):
    lags = []
    stop_event = asyncio.Event()

    # Start heartbeat
    hb_task = asyncio.create_task(heartbeat(0.01, stop_event, lags))

    # Give heartbeat a chance to start
    await asyncio.sleep(0.05)

    print(f"Running benchmark: {name}...")
    start_time = time.perf_counter()

    # Run the task
    await task_func(duration)

    total_time = time.perf_counter() - start_time

    # Give heartbeat a chance to capture the lag if it just finished
    await asyncio.sleep(0.05)

    # Stop heartbeat
    stop_event.set()
    await hb_task

    max_lag = max(lags) if lags else 0
    avg_lag = statistics.mean(lags) if lags else 0

    print(f"  Total time: {total_time:.4f}s")
    print(f"  Max event loop lag: {max_lag:.4f}s")
    print(f"  Avg event loop lag: {avg_lag:.4f}s")
    print("-" * 30)
    return max_lag

async def main():
    print("Event Loop Lag Benchmark (Baseline vs Optimized)")
    print("=" * 45)

    # Baseline: Blocking in async def
    baseline_lag = await run_benchmark("Baseline (async def + blocking)", async_blocking_task)

    # Optimized: Blocking offloaded to thread
    optimized_lag = await run_benchmark("Optimized (def + threaded)", threaded_blocking_task)

    if baseline_lag > 0:
        improvement = (baseline_lag - optimized_lag) / baseline_lag * 100
        print(f"Improvement in Max Lag: {improvement:.2f}%")
    else:
        print("Baseline lag was 0, improvement cannot be calculated.")

if __name__ == "__main__":
    asyncio.run(main())
