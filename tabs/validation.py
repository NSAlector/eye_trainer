import math

class ExerciseValidator:
    def __init__(self, threshold=2.0, window_size = 10):
        self.threshold = threshold
        self.window_size = window_size

    def sync_trajectories(self, target_data, gaze_data):
        synced_pairs = []

        if not target_data or not gaze_data:
            return []

        for t_point in target_data:
            t_time = t_point['duration']

            closest_gaze = min(gaze_data, key=lambda g: abs(g['duration'] - t_time))

            synced_pairs.append({
                'duration': round(t_time, 2),
                'target': (t_point['x_coord'], t_point['y_coord']),
                'gaze': (closest_gaze['x_coord'], closest_gaze['y_coord'])
            })

        return synced_pairs

    def calculate_metrics(self, synced_pairs):
        if not synced_pairs:
            return {"score": 0, "is_success": False, "avg_error": 999}

        total_dist = 0
        for pair in synced_pairs:
            tx, ty = pair['target']
            gx, gy = pair['gaze']

            dist = math.sqrt((tx - gx) ** 2 + (ty - gy) ** 2)
            total_dist += dist

        avg_error = total_dist / len(synced_pairs)
        score = max(0, 100 - int(avg_error * 15))

        return {
            "is_success": avg_error <= self.threshold,
            "avg_error": round(avg_error, 2),
            "score": score
        }

    def find_deviation_segments(self, synced_pairs):
        n = len(synced_pairs)

        if n < self.window_size:
            return []

        bad_windows = []

        for i in range(n - self.window_size + 1): # количество существующих позиций
            window = synced_pairs[i: i + self.window_size]

            total = 0
            for p in window:
                tx, ty = p['target']
                gx, gy = p['gaze']
                total += math.sqrt((tx - gx) ** 2 + (ty - gy) ** 2)

            average_error = total / self.window_size

            if average_error > self.threshold:
                window_start = window[0]['duration']
                window_end = window[-1]['duration']
                bad_windows.append([window_start, window_end])

        if not bad_windows:
            return []

        bad_windows.sort()
        segments = [bad_windows[0]]

        for current_window in bad_windows[1:]:
            current_start = current_window[0]
            current_end = current_window[1]

            last_segment = segments[-1]
            last_end = last_segment[1]

            if current_start <= last_end:
                last_segment[1] = max(last_end, current_end)
            else:
                segments.append(current_window)

        return segments

    def validate(self, target_data, gaze_data):
        synced = self.sync_trajectories(target_data, gaze_data)
        result = self.calculate_metrics(synced)
        result['anomalies'] = self.find_deviation_segments(synced)
        return result
