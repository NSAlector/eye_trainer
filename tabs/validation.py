import math

class ExerciseValidator:
    def __init__(self, threshold=175.0, window_size=10):
        self.threshold = threshold
        self.window_size = window_size

    def sync_trajectories(self, target_data, gaze_data):
        synced_pairs = []
        if not target_data or not gaze_data: return []
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
        if not synced_pairs: return {"score": 0, "is_success": False, "avg_error": 999}
        total_dist = sum(math.sqrt((p['target'][0]-p['gaze'][0])**2 + (p['target'][1]-p['gaze'][1])**2) for p in synced_pairs)
        avg_error = total_dist / len(synced_pairs)
        score = max(0, int(100 * (1 - avg_error / (2 * self.threshold))))
        return {
            "is_success": avg_error <= self.threshold,
            "avg_error": round(avg_error, 1),
            "score": score
        }

    def calculate_timeline_errors(self, synced_pairs):
        if not synced_pairs: return []
        timeline = []
        max_sec = int(synced_pairs[-1]['duration'])
        for sec in range(max_sec + 1):
            points = [p for p in synced_pairs if int(p['duration']) == sec]
            if points:
                avg = sum(math.sqrt((p['target'][0]-p['gaze'][0])**2 + (p['target'][1]-p['gaze'][1])**2) for p in points) / len(points)
                timeline.append({"interval": f"{sec}с", "error": round(avg, 1)})
        return timeline

    def find_deviation_segments(self, synced_pairs):
        n = len(synced_pairs)
        if n < self.window_size: return []
        bad_windows = []
        for i in range(n - self.window_size + 1):
            win = synced_pairs[i : i + self.window_size]
            err = sum(math.sqrt((p['target'][0]-p['gaze'][0])**2 + (p['target'][1]-p['gaze'][1])**2) for p in win) / self.window_size
            if err > self.threshold:
                bad_windows.append([win[0]['duration'], win[-1]['duration']])
        if not bad_windows: return []
        bad_windows.sort(); segments = [bad_windows[0]]
        for cur in bad_windows[1:]:
            if cur[0] <= segments[-1][1]: segments[-1][1] = max(segments[-1][1], cur[1])
            else: segments.append(cur)
        return segments

    def validate(self, target_data, gaze_data):
        synced = self.sync_trajectories(target_data, gaze_data)
        result = self.calculate_metrics(synced)
        result['anomalies'] = self.find_deviation_segments(synced)
        result['timeline'] = self.calculate_timeline_errors(synced)
        return result
