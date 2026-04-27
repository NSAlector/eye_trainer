import json
import math
import random
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tabs.validation import ExerciseValidator

LOG_FILE = "C:/Qt/EyeTrainer/eye_gymnastics/data/gymnastics.log"


def load_stimulus(filepath, movement_filter=None):
    points = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("levelname") != "INFO":
                continue
            movement = entry.get("movement", "")
            if movement_filter and movement_filter not in movement:
                continue
            points.append({
                "duration": entry["duration"],
                "x_coord":  entry["x_coord"],
                "y_coord":  entry["y_coord"]
            })
    return points


def gaze_ideal(stimulus):
    return [{"duration": p["duration"], "x_coord": p["x_coord"], "y_coord": p["y_coord"]}
            for p in stimulus]


def gaze_epsilon(stimulus, epsilon=1.0):
    result = []
    for p in stimulus:
        result.append({
            "duration": p["duration"],
            "x_coord":  p["x_coord"] + random.uniform(-epsilon, epsilon),
            "y_coord":  p["y_coord"] + random.uniform(-epsilon, epsilon)
        })
    return result


def gaze_sinus(stimulus, amplitude=3.0):
    result = []
    for i, p in enumerate(stimulus):
        offset = amplitude * math.sin(i * 0.5)
        result.append({
            "duration": p["duration"],
            "x_coord":  p["x_coord"] + offset,
            "y_coord":  p["y_coord"] + offset
        })
    return result


def gaze_drift(stimulus, start=None, end=None, offset=15.0):
    if start is None:
        start = len(stimulus) // 3
    if end is None:
        end = start + len(stimulus) // 4

    result = []
    for i, p in enumerate(stimulus):
        if start <= i <= end:
            result.append({
                "duration": p["duration"],
                "x_coord":  p["x_coord"] + offset,
                "y_coord":  p["y_coord"] + offset
            })
        else:
            result.append({
                "duration": p["duration"],
                "x_coord":  p["x_coord"],
                "y_coord":  p["y_coord"]
            })
    return result


def gaze_delay(stimulus, delay_seconds=0.5):
    result = []
    for p in stimulus:
        delayed_time = p['duration'] - delay_seconds
        if delayed_time < 0:
            source = stimulus[0]
        else:
            source = min(stimulus, key=lambda s: abs(s['duration'] - delayed_time))
        result.append({
            "duration": p['duration'],
            "x_coord":  source['x_coord'],
            "y_coord":  source['y_coord']
        })
    return result


def report(test_name, result):
    success   = "засчитано" if result['is_success'] else "не засчитано"
    anomalies = result.get('anomalies', [])

    print(f"  название:   {test_name}")
    print(f"  результат:  {success}")
    print(f"  avg_error:  {result['avg_error']}")
    print(f"  score:      {result['score']}")

    if anomalies:
        print(f"  аномалии:   {len(anomalies)} участок(ов)")
        for i, seg in enumerate(anomalies, 1):
            print(f"    {i}. [{seg[0]:.2f} — {seg[1]:.2f} сек]")
    else:
        print(f"  аномалии:   нет")
    print()


def test_metrics_perfect(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_ideal(stimulus))
    result    = validator.calculate_metrics(synced)
    assert result['is_success'] == True
    assert result['avg_error']  == 0.0
    assert result['score']      == 100
    print(f"OK  metrics: идеальный взгляд → avg_error=0.0, score=100")


def test_metrics_within_threshold(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_epsilon(stimulus, epsilon=1.0))
    result    = validator.calculate_metrics(synced)
    assert result['is_success'] == True, \
        f"avg_error={result['avg_error']} должно быть ≤ порога 2.0"
    print(f"OK  metrics: epsilon=1.0 → avg_error={result['avg_error']}, score={result['score']}")


def test_metrics_exceeds_threshold(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_epsilon(stimulus, epsilon=5.0))
    result    = validator.calculate_metrics(synced)
    assert result['is_success'] == False, \
        f"avg_error={result['avg_error']} должно превышать порог 2.0"
    assert result['score'] < 100
    print(f"OK  metrics: epsilon=5.0 → avg_error={result['avg_error']}, score={result['score']}")


def test_metrics_sinus_fail(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_sinus(stimulus, amplitude=8.0))
    result    = validator.calculate_metrics(synced)
    assert result['is_success'] == False, \
        f"avg_error={result['avg_error']} должно превышать порог 2.0"
    print(f"OK  metrics: синусоида amplitude=8.0 → avg_error={result['avg_error']}, score={result['score']}")


def test_metrics_delay(stimulus):
    validator    = ExerciseValidator(threshold=2.0, window_size=5)
    synced_small = validator.sync_trajectories(stimulus, gaze_delay(stimulus, delay_seconds=0.3))
    synced_big   = validator.sync_trajectories(stimulus, gaze_delay(stimulus, delay_seconds=2.0))
    result_small = validator.calculate_metrics(synced_small)
    result_big   = validator.calculate_metrics(synced_big)
    assert result_big['avg_error'] > result_small['avg_error'], \
        "Большая задержка должна давать большую ошибку"
    print(f"OK  metrics: задержка 0.3с → avg_error={result_small['avg_error']}, score={result_small['score']}")
    print(f"OK  metrics: задержка 2.0с → avg_error={result_big['avg_error']}, score={result_big['score']}")


def test_segments_ideal(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_ideal(stimulus))
    result    = validator.find_deviation_segments(synced)
    assert result == [], f"Ожидали [], получили {result}"
    print("OK  segments: идеальный взгляд → участков нет")


def test_segments_epsilon_within(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_epsilon(stimulus, epsilon=1.0))
    result    = validator.find_deviation_segments(synced)
    assert result == [], f"Epsilon=1.0 в пределах порога, ожидали [], получили {result}"
    print("OK  segments: epsilon=1.0 (меньше порога 2.0) → участков нет")


def test_segments_epsilon_exceeds(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_epsilon(stimulus, epsilon=5.0))
    result    = validator.find_deviation_segments(synced)
    assert len(result) >= 1, f"Epsilon=5.0 превышает порог, ожидали участки, получили []"
    print(f"OK  segments: epsilon=5.0 (больше порога 2.0) → найдено участков: {len(result)}")
    for i, seg in enumerate(result, 1):
        print(f"    {i}. [{seg[0]:.2f} — {seg[1]:.2f} сек]")


def test_segments_sinus(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    synced    = validator.sync_trajectories(stimulus, gaze_sinus(stimulus, amplitude=5.0))
    result    = validator.find_deviation_segments(synced)
    assert len(result) >= 1, "Ожидали участки при синусоидальном отклонении"
    print(f"OK  segments: синусоида amplitude=5.0 → найдено участков: {len(result)}")
    for i, seg in enumerate(result, 1):
        print(f"    {i}. [{seg[0]:.2f} — {seg[1]:.2f} сек]")


def test_segments_drift(stimulus):
    validator   = ExerciseValidator(threshold=2.0, window_size=5)
    n           = len(stimulus)
    drift_start = n // 3
    drift_end   = drift_start + n // 4
    gaze        = gaze_drift(stimulus, start=drift_start, end=drift_end, offset=15.0)
    synced      = validator.sync_trajectories(stimulus, gaze)
    result      = validator.find_deviation_segments(synced)
    assert len(result) >= 1, "Ожидали участок отклонения при дрейфе"
    seg = result[0]
    assert seg[0] <= stimulus[drift_end]['duration'],   "Участок начинается слишком поздно"
    assert seg[1] >= stimulus[drift_start]['duration'], "Участок заканчивается слишком рано"
    print(f"OK  segments: дрейф offset=15.0 → участок [{seg[0]:.2f} — {seg[1]:.2f} сек]")


def test_validate_ideal(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    result    = validator.validate(stimulus, gaze_ideal(stimulus))
    assert result['is_success'] == True
    assert result['avg_error']  == 0.0
    assert result['anomalies']  == []
    report("идеальный взгляд", result)


def test_validate_epsilon_pass(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    result    = validator.validate(stimulus, gaze_epsilon(stimulus, epsilon=1.0))
    assert result['is_success'] == True
    report("epsilon=1.0 (в пределах порога)", result)


def test_validate_sinus_fail(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    result    = validator.validate(stimulus, gaze_sinus(stimulus, amplitude=8.0))
    assert result['is_success'] == False
    assert len(result['anomalies']) >= 1
    report("синусоида amplitude=8.0", result)


def test_validate_drift_fail(stimulus):
    validator = ExerciseValidator(threshold=2.0, window_size=5)
    result    = validator.validate(stimulus, gaze_drift(stimulus, offset=20.0))
    assert result['is_success'] == False
    assert len(result['anomalies']) >= 1
    report("дрейф offset=20.0", result)


def test_validate_delay(stimulus):
    validator    = ExerciseValidator(threshold=2.0, window_size=5)
    result_small = validator.validate(stimulus, gaze_delay(stimulus, delay_seconds=0.3))
    result_big   = validator.validate(stimulus, gaze_delay(stimulus, delay_seconds=2.0))
    assert result_big['avg_error'] > result_small['avg_error'], \
        "Большая задержка должна давать большую ошибку"
    report("задержка 0.3 сек", result_small)
    report("задержка 2.0 сек", result_big)
    print("OK  большая задержка даёт большую ошибку чем маленькая")


if __name__ == "__main__":
    random.seed(42)

    print("Загружаем стимул из лога...")
    stimulus = load_stimulus(LOG_FILE, movement_filter="calc_cur_coordinates_circle_right")
    print(f"Загружено точек стимула: {len(stimulus)}\n")

    all_tests = [
        ("calculate_metrics — корректность выполнения упражнения", [
            lambda: test_metrics_perfect(stimulus),
            lambda: test_metrics_within_threshold(stimulus),
            lambda: test_metrics_exceeds_threshold(stimulus),
            lambda: test_metrics_sinus_fail(stimulus),
            lambda: test_metrics_delay(stimulus),
        ]),
        ("find_deviation_segments — поиск участков отклонения", [
            lambda: test_segments_ideal(stimulus),
            lambda: test_segments_epsilon_within(stimulus),
            lambda: test_segments_epsilon_exceeds(stimulus),
            lambda: test_segments_sinus(stimulus),
            lambda: test_segments_drift(stimulus),
        ]),
        ("validate — итоговый результат", [
            lambda: test_validate_ideal(stimulus),
            lambda: test_validate_epsilon_pass(stimulus),
            lambda: test_validate_sinus_fail(stimulus),
            lambda: test_validate_drift_fail(stimulus),
            lambda: test_validate_delay(stimulus),
        ]),
    ]

    passed = 0
    failed = 0

    for group_name, group_tests in all_tests:
        print(f"=== {group_name} ===")
        for test in group_tests:
            try:
                test()
                passed += 1
            except AssertionError as e:
                print(f"FAIL: {e}")
                failed += 1
        print()

    print(f"Итого: {passed} passed, {failed} failed")
