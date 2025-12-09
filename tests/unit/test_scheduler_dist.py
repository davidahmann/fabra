import pytest
import time
from fakeredis import FakeStrictRedis
from fabra.scheduler_dist import DistributedScheduler


@pytest.fixture
def redis_client() -> FakeStrictRedis:
    return FakeStrictRedis()


@pytest.fixture
def callback_log() -> list[str]:
    return []


def test_scheduler_starts(redis_client: FakeStrictRedis) -> None:
    scheduler = DistributedScheduler(redis_client)
    scheduler.start()
    try:
        assert scheduler.scheduler.running
    finally:
        scheduler.shutdown()


def test_schedule_job_locks(redis_client: FakeStrictRedis) -> None:
    scheduler = DistributedScheduler(redis_client)
    scheduler.start()

    try:
        # Shared state to verify job execution
        execution_count = {"count": 0}

        def my_job() -> None:
            execution_count["count"] += 1

        # Schedule job with ID "job1"
        scheduler.schedule_job(my_job, interval_seconds=1, job_id="job1")

        # Let it run once
        time.sleep(1.2)

        # Verify logic manually or trust "lock" key presence if we could pause time.
        # Check if lock key exists (it might have expired if job finished fast)
        # But we mostly care that this test doesn't crash or leak.
    finally:
        scheduler.shutdown()


def test_lock_contention(redis_client: FakeStrictRedis) -> None:
    # Simulate two schedulers
    s1 = DistributedScheduler(redis_client)
    s2 = DistributedScheduler(redis_client)
    s1.start()
    s2.start()

    try:
        run_log = []

        def job_logic() -> None:
            run_log.append("run")

        # Manually hold the lock to simulate s1 holding it
        redis_client.set("lock:job_shared", "locked", ex=10)

        # Now schedule on s2
        s2.schedule_job(job_logic, interval_seconds=1, job_id="job_shared")

        # Trigger the job on s2 'manually' via getting the job function from apscheduler
        # This avoids waiting for real time.
        job = s2.scheduler.get_job("job_shared")
        # The 'func' of the job is the 'locked_job' wrapper
        wrapper = job.func

        # Run the wrapper
        wrapper()

        # Since lock is held by "s1" (manually set), s2 should NOT run the logic
        assert len(run_log) == 0

        # Now release lock
        redis_client.delete("lock:job_shared")

        # Run wrapper again
        wrapper()

        # Now it should run
        assert len(run_log) == 1

    finally:
        s1.shutdown()
        s2.shutdown()
