"""Map a time on the new reel timeline back to a frame of the speaker footage.

edl.json (build_voice.py) says which source stretch plays at every output time;
selects.json says where each source stretch sits inside the selects clip that
was matted. Between spoken pieces the source simply keeps rolling, so the
speaker keeps moving naturally through the pauses.
"""
import bisect
import json


class Timeline:
    def __init__(self, edl_path, selects_path):
        edl = json.load(open(edl_path))
        sel = json.load(open(selects_path))
        self.speed = edl.get("speed", 1.0)
        self.duration = edl["duration"]
        self.spans = edl["spans"]
        self.starts = [sp["out"][0] for sp in self.spans]
        self.fps = sel["fps"]
        self.ranges = sel["ranges"]
        self.words = [w for sp in self.spans for w in sp["words"]]

    def span_at(self, t):
        return max(bisect.bisect_right(self.starts, t) - 1, 0)

    def src_time(self, t):
        sp = self.spans[self.span_at(t)]
        return sp["src"][0] + (t - sp["out"][0]) * self.speed

    def select_frame(self, t):
        """Index into the selects clip (and its alpha) for output time t."""
        k = self.span_at(t)
        src = self.src_time(t)
        for r in self.ranges:
            if r["src"][0] - 1e-3 <= src < r["src"][1]:
                return r["sel_frame"] + min(int(round((src - r["src"][0]) * self.fps)), r["frames"] - 1)
        # past the end of this stretch: hold its last frame
        s0 = self.spans[k]["src"][0]
        best = min(self.ranges, key=lambda r: abs(r["src"][0] - s0))
        return best["sel_frame"] + best["frames"] - 1

    def select_frame_in_span(self, k, t):
        """Selects frame for output time t as if span k were still (or already) playing:
        used to blend across a join."""
        src = self.spans[k]["src"][0] + (t - self.spans[k]["out"][0]) * self.speed
        best = min(self.ranges, key=lambda r: 0 if r["src"][0] <= src < r["src"][1] else
                   min(abs(src - r["src"][0]), abs(src - r["src"][1])))
        i = int(round((src - best["src"][0]) * self.fps))
        return best["sel_frame"] + min(max(i, 0), best["frames"] - 1)

    def piece_at(self, t):
        return self.spans[self.span_at(t)]["piece"]
