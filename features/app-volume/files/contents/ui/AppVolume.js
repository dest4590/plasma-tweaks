/*
    SPDX-FileCopyrightText: 2026 plasma-tweaks contributors

    SPDX-License-Identifier: GPL-2.0-or-later
*/

.pragma library

var DEFAULT_STEP_PERCENT = 5;
var ANGLE_STEP = 120;
var PIXEL_STEP = 40;

function createAccumulator() {
    return {
        angle: 0,
        pixel: 0,
        target: null
    };
}

function consumeWheelSteps(acc, target, angleDeltaY, pixelDeltaY) {
    if (acc.target !== target) {
        acc.angle = 0;
        acc.pixel = 0;
        acc.target = target;
    }

    if (angleDeltaY) {
        acc.angle += angleDeltaY;
        var angleSteps = Math.trunc(acc.angle / ANGLE_STEP);
        if (angleSteps !== 0) {
            acc.angle -= angleSteps * ANGLE_STEP;
        }
        return angleSteps;
    }

    if (pixelDeltaY) {
        acc.pixel += pixelDeltaY;
        var pixelSteps = Math.trunc(acc.pixel / PIXEL_STEP);
        if (pixelSteps !== 0) {
            acc.pixel -= pixelSteps * PIXEL_STEP;
        }
        return pixelSteps;
    }

    return 0;
}

function volumeToPercent(volume, minimalVolume, normalVolume) {
    var span = normalVolume - minimalVolume;
    if (span <= 0) {
        return 0;
    }
    var pct = Math.round(((volume - minimalVolume) / span) * 100);
    return Math.max(0, Math.min(100, pct));
}

function percentToVolume(percent, minimalVolume, normalVolume) {
    var span = normalVolume - minimalVolume;
    if (span <= 0) {
        return minimalVolume;
    }
    var clamped = Math.max(0, Math.min(100, percent));
    return Math.round(minimalVolume + (clamped / 100) * span);
}

function applyVolumeSteps(streams, steps, minimalVolume, normalVolume, stepPercent) {
    if (!streams || streams.length === 0 || steps === 0) {
        return false;
    }
    var step = stepPercent || DEFAULT_STEP_PERCENT;
    var deltaPct = steps * step;
    var changed = false;

    for (var i = 0; i < streams.length; ++i) {
        var stream = streams[i];
        if (!stream) {
            continue;
        }
        try {
            if (!stream.model) {
                continue;
            }
            var currentVol = stream.model.Volume;
            if (typeof currentVol !== "number") {
                currentVol = stream.volume;
            }
            if (typeof currentVol !== "number") {
                continue;
            }
            var currentPct = volumeToPercent(currentVol, minimalVolume, normalVolume);
            var nextPct = Math.max(0, Math.min(100, currentPct + deltaPct));
            var nextVol = percentToVolume(nextPct, minimalVolume, normalVolume);
            stream.model.Volume = nextVol;
            changed = true;
        } catch (e) {
            // Stream may disappear mid-event.
        }
    }
    return changed;
}

function formatStreamRange(streams, minimalVolume, normalVolume) {
    if (!streams || streams.length === 0) {
        return "0%";
    }
    var minPct = 100;
    var maxPct = 0;
    var count = 0;
    for (var i = 0; i < streams.length; ++i) {
        var stream = streams[i];
        if (!stream) {
            continue;
        }
        var vol = typeof stream.volume === "number" ? stream.volume : (stream.model ? stream.model.Volume : undefined);
        if (typeof vol !== "number") {
            continue;
        }
        var pct = volumeToPercent(vol, minimalVolume, normalVolume);
        if (pct < minPct) {
            minPct = pct;
        }
        if (pct > maxPct) {
            maxPct = pct;
        }
        count++;
    }
    if (count === 0) {
        return "0%";
    }
    if (minPct === maxPct) {
        return minPct + "%";
    }
    return minPct + "%\u2013" + maxPct + "%";
}
