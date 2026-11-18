/*
    SPDX-FileCopyrightText: 2017 Kai Uwe Broulik <kde@privat.broulik.de>

    SPDX-License-Identifier: GPL-2.0-or-later
*/

pragma ComponentBehavior: Bound

import QtQuick

import org.kde.plasma.plasmoid
import org.kde.plasma.extras as PlasmaExtras
import org.kde.kirigami as Kirigami

import org.kde.taskmanager as TaskManager

MouseArea {
    id: micStreamIconBox

    required property Task task

    // Taken from KIconLoader.
    readonly property int indicatorSize: {
        const size = Math.min(task.height, task.width) / 2;

        if (size < Kirigami.Units.iconSizes.smallMedium) {
            return Kirigami.Units.iconSizes.small;
        }
        return Kirigami.Units.iconSizes.smallMedium;
    }

    readonly property int indicatorScale: Math.max(1, Math.round(indicatorSize / Kirigami.Units.iconSizes.small))

    anchors {
        right: task.audioStreamIcon && task.audioStreamIcon.visible ? task.audioStreamIcon.right : parent.right
        rightMargin: task.audioStreamIcon && task.audioStreamIcon.visible ? 0 : task.taskFrame.margins.right
        top: task.audioStreamIcon && task.audioStreamIcon.visible ? task.audioStreamIcon.bottom : parent.top
        topMargin: task.audioStreamIcon && task.audioStreamIcon.visible
            ? Math.round(Kirigami.Units.smallSpacing / 2)
            : Math.round(task.taskFrame.margins.top * indicatorScale)
    }

    width: height
    height: Math.min(Math.min(task.width, task.height) * 0.4, indicatorSize)

    visible: task.hasMicStream && task.audioIndicatorsEnabled

    enabled: Plasmoid.configuration.interactiveMute && !task.isLauncher

    hoverEnabled: true

    onClicked: mouse => {
        if (mouse.button === Qt.LeftButton) {
            task.toggleMicMuted();
        }
    }

    Accessible.checkable: true
    Accessible.checked: micStreamIconBox.task.micMuted
    Accessible.name: micStreamIconBox.task.micMuted
        ? i18nc("@action:button", "Unmute microphone")
        : i18nc("@action:button", "Mute microphone")
    Accessible.role: Accessible.Button

    PlasmaExtras.Highlight {
        anchors.fill: parent
        hovered: micStreamIconBox.containsMouse
        pressed: micStreamIconBox.pressed
    }

    Kirigami.Icon {
        anchors.fill: parent
        source: {
            if (micStreamIconBox.task.micMuted) {
                return "microphone-sensitivity-muted-symbolic";
            }
            return "microphone-sensitivity-high-symbolic";
        }
        active: micStreamIconBox.containsMouse && micStreamIconBox.enabled
    }
}
