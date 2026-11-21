from plb.config import ImagesConfig, MixConfig
from experiments.schedule import build_schedule, schedule_seed, write_schedule_csv

IMAGES = ImagesConfig(per_class=5, mix=MixConfig(small=0.4, medium=0.4, large=0.2))


def schedule_csv_bytes(tmp_path, name):
    path = tmp_path / name
    write_schedule_csv(build_schedule(schedule_seed(1, 2, 2.0, 1), 2, 2.0, 30.0, IMAGES), path)
    return path.read_bytes()


def test_same_seed_scenario_rate_and_round_give_a_byte_identical_csv(tmp_path):
    first = schedule_csv_bytes(tmp_path, "a.csv")
    second = schedule_csv_bytes(tmp_path, "b.csv")

    assert first == second
    assert first.startswith(b"request_id,planned_offset_s,image_id,size_class\r\n")


def test_a_rate_of_2_and_2_point_0_give_the_same_seed():
    assert schedule_seed(1, 2, 2, 1) == schedule_seed(1, 2, 2.0, 1)


def first_10000(scenario, rate):
    # At this rate 2000 s holds about 20,000 requests, so 10,000 always fit.
    schedule = build_schedule(schedule_seed(7, scenario, rate, 1), scenario, rate, 2000.0, IMAGES)
    return schedule[:10_000]


def test_mean_gap_over_10000_requests_is_within_3_percent_of_one_over_rate():
    schedule = first_10000(scenario=1, rate=10.0)

    mean_gap = schedule[-1].planned_offset_s / len(schedule)
    assert len(schedule) == 10_000
    assert abs(mean_gap - 0.1) <= 0.03 * 0.1


def test_scenario_1_uses_only_medium_images():
    schedule = first_10000(scenario=1, rate=10.0)

    assert {p.size_class for p in schedule} == {"medium"}


def test_scenario_2_class_shares_are_within_2_points_of_the_mix():
    schedule = first_10000(scenario=2, rate=10.0)

    for size_class, share in (("small", 0.4), ("medium", 0.4), ("large", 0.2)):
        count = sum(p.size_class == size_class for p in schedule)
        assert abs(count / 10_000 - share) <= 0.02, size_class
