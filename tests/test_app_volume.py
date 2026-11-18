from pathlib import Path
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
APP_VOLUME_JS = ROOT / "features/app-volume/files/contents/ui/AppVolume.js"


@unittest.skipUnless(shutil.which("node"), "node is required to test AppVolume.js")
class AppVolumeJsTests(unittest.TestCase):
    def run_js(self, body: str) -> None:
        js_src = APP_VOLUME_JS.read_text().replace(".pragma library", "")
        script = f"""
const assert = require("assert");
{js_src}
{body}
"""
        res = subprocess.run(["node", "-e", script], capture_output=True, text=True)
        if res.returncode != 0:
            self.fail(f"Node test failed:\n{res.stderr}\n{res.stdout}")

    def test_step_sign_clamping_and_preserve_mute(self):
        self.run_js("""
const MIN = 0, MAX = 65536;
const s1 = { volume: Math.round(0.20 * MAX), model: { Volume: Math.round(0.20 * MAX), Muted: false } };
const s2 = { volume: Math.round(0.98 * MAX), model: { Volume: Math.round(0.98 * MAX), Muted: true } };

// Scroll up +1 step (+5pp): s1 -> 25%, s2 -> 100% (clamped), Muted preserved!
assert.strictEqual(applyVolumeSteps([s1, s2], 1, MIN, MAX, 5), true);
assert.strictEqual(volumeToPercent(s1.model.Volume, MIN, MAX), 25);
assert.strictEqual(volumeToPercent(s2.model.Volume, MIN, MAX), 100);
assert.strictEqual(s1.model.Muted, false);
assert.strictEqual(s2.model.Muted, true);

// Scroll down to 0%: Muted stays false!
const s3 = { volume: Math.round(0.05 * MAX), model: { Volume: Math.round(0.05 * MAX), Muted: false } };
assert.strictEqual(applyVolumeSteps([s3], -2, MIN, MAX, 5), true);
assert.strictEqual(s3.model.Volume, 0);
assert.strictEqual(s3.model.Muted, false);
""")

    def test_no_streams_returns_false(self):
        self.run_js("""
assert.strictEqual(applyVolumeSteps([], 1, 0, 65536, 5), false);
assert.strictEqual(applyVolumeSteps(null, 1, 0, 65536, 5), false);
""")

    def test_wheel_accumulation_angle_and_pixel_and_target_reset(self):
        self.run_js("""
const acc = createAccumulator();
const taskA = { id: "A" }, taskB = { id: "B" };
assert.strictEqual(consumeWheelSteps(acc, taskA, 40, 0), 0);
assert.strictEqual(consumeWheelSteps(acc, taskA, 40, 0), 0);
assert.strictEqual(consumeWheelSteps(acc, taskA, 40, 0), 1);

// Partial pixelDelta on taskA resets when switching to taskB
assert.strictEqual(consumeWheelSteps(acc, taskA, 0, 30), 0);
assert.strictEqual(consumeWheelSteps(acc, taskB, 0, 20), 0);
assert.strictEqual(consumeWheelSteps(acc, taskB, 0, 20), 1);
""")

    def test_disappeared_stream_handled_gracefully(self):
        self.run_js("""
const MIN = 0, MAX = 65536;
const gone = { get model() { throw new Error("Object destroyed"); } };
const ok = { volume: Math.round(0.50 * MAX), model: { Volume: Math.round(0.50 * MAX), Muted: false } };
assert.strictEqual(applyVolumeSteps([gone, ok], 1, MIN, MAX, 5), true);
assert.strictEqual(volumeToPercent(ok.model.Volume, MIN, MAX), 55);
""")

    def test_modifier_and_tooltip_range_formatting(self):
        self.run_js("""
const ALT = 0x08000000;
assert.strictEqual(modifierMatches(0, 0, ALT), true);
assert.strictEqual(modifierMatches(0, 1, ALT), false);
assert.strictEqual(modifierMatches(ALT, 1, ALT), true);

const MAX = 65536;
assert.strictEqual(formatStreamRange([{ volume: Math.round(0.5 * MAX) }, { volume: Math.round(0.5 * MAX) }], 0, MAX), "50%");
assert.strictEqual(formatStreamRange([{ volume: Math.round(0.4 * MAX) }, { volume: Math.round(0.75 * MAX) }], 0, MAX), "40%\\u201375%");
""")


if __name__ == "__main__":
    unittest.main()
