/*
    SPDX-FileCopyrightText: 2017 Kai Uwe Broulik <kde@privat.broulik.de>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound

import QtQuick

import org.kde.plasma.private.volume as PlasmaPa

QtObject {
    id: pulseAudio

    signal streamsChanged()
    signal micStreamsChanged()

    readonly property /*PlasmaPa.GlobalConfig*/ QtObject globalConfig: PlasmaPa.GlobalConfig { }

    // It's a JS object so we can do key lookup and don't need to take care of filtering duplicates.
    property var pidMatches: new Set()

    // TODO Evict cache at some point, preferably if all instances of an application closed.
    function registerPidMatch(appName: string) {
        if (!hasPidMatch(appName)) {
            pidMatches.add(appName);

            // In case this match is new, notify that streams might have changed.
            // This way we also catch the case when the non-playing instance
            // shows up first.
            // Only notify if we changed to avoid infinite recursion.
            streamsChanged();
            micStreamsChanged();
        }
    }

    function hasPidMatch(appName: string): bool {
        return pidMatches.has(appName);
    }

    function findStreams(key: string, value: var, inst = instantiator): /*[QtObject]*/ var {
        return findStreamsFn(stream => stream[key] === value, inst);
    }

    function findStreamsFn(fn: var, inst = instantiator): var {
        const streams = [];
        for (let i = 0, count = inst.count; i < count; ++i) {
            const stream = inst.objectAt(i);
            if (fn(stream)) {
                streams.push(stream);
            }
        }
        return streams;
    }

    function streamsForAppId(appId: string): /*[QtObject]*/ var {
        return findStreams("portalAppId", appId);
    }

    function micStreamsForAppId(appId: string): /*[QtObject]*/ var {
        return findStreams("portalAppId", appId, micInstantiator);
    }

    function streamsForAppName(appName: string): /*[QtObject]*/ var {
        return findStreams("appName", appName);
    }

    function micStreamsForAppName(appName: string): /*[QtObject]*/ var {
        return findStreams("appName", appName, micInstantiator);
    }

    function streamsForPid(pid: int, inst = instantiator): /*[QtObject]*/ var {
        // skip stream that has portalAppId
        // app using portal may have a sandbox pid
        const streams = findStreamsFn(stream => stream.pid === pid && !stream.portalAppId, inst);

        if (streams.length === 0) {
            for (let i = 0, length = inst.count; i < length; ++i) {
                const stream = inst.objectAt(i) as StreamDelegate;

                if (stream.parentPid === -1) {
                    stream.parentPid = backend.parentPid(stream.pid);
                }

                if (stream.parentPid === pid) {
                    streams.push(stream);
                }
            }
        }

        return streams;
    }

    function micStreamsForPid(pid: int): /*[QtObject]*/ var {
        return streamsForPid(pid, micInstantiator);
    }

    component StreamDelegate: QtObject {
        id: delegate
        required property var model
        readonly property int pid: model.Client?.properties["application.process.id"] ?? 0
        // Determined on demand.
        property int parentPid: -1
        readonly property string appName: model.Client?.properties["application.name"] ?? ""
        readonly property string portalAppId: model.Client?.properties["pipewire.access.portal.app_id"] ?? ""
        readonly property bool muted: model.Muted
        // whether there is nothing actually going on on that stream
        readonly property bool corked: model.Corked
        readonly property int volume: model.Volume

        function mute(): void {
            model.Muted = true;
        }
        function unmute(): void {
            model.Muted = false;
        }
    }

    // QtObject has no default property, hence adding the Instantiator to one explicitly.
    readonly property Instantiator instantiator: Instantiator {
        model: PlasmaPa.PulseObjectFilterModel {
            filters: [ { role: "VirtualStream", value: false } ]
            sourceModel: PlasmaPa.SinkInputModel {}
        }

        delegate: StreamDelegate { }

        onObjectAdded: (index, object) => pulseAudio.streamsChanged()
        onObjectRemoved: (index, object) => pulseAudio.streamsChanged()
    }

    readonly property Instantiator micInstantiator: Instantiator {
        model: PlasmaPa.PulseObjectFilterModel {
            filters: [ { role: "VirtualStream", value: false } ]
            sourceModel: PlasmaPa.SourceOutputModel {}
        }

        delegate: StreamDelegate { }

        onObjectAdded: (index, object) => pulseAudio.micStreamsChanged()
        onObjectRemoved: (index, object) => pulseAudio.micStreamsChanged()
    }

    readonly property int minimalVolume: PlasmaPa.PulseAudio.MinimalVolume
    readonly property int normalVolume: PlasmaPa.PulseAudio.NormalVolume
}
