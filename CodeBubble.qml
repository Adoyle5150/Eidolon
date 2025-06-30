import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: codeBubble
    width: parent ? parent.width * 0.95 : 800
    color: "#1e1e1e"
    radius: 8
    border.color: "#444"
    border.width: 1
    property string codeText: ""
    property string language: "plain"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10
        spacing: 6

        TextArea {
            id: codeDisplay
            text: codeBubble.codeText
            wrapMode: TextArea.NoWrap
            font.family: "Consolas"
            font.pixelSize: 13
            readOnly: true
            color: "#ccc"
            background: null
            selectByMouse: true
            horizontalScrollBarPolicy: Qt.ScrollBarAsNeeded
            verticalScrollBarPolicy: Qt.ScrollBarAsNeeded
        }

        Button {
            text: "Copy"
            Layout.alignment: Qt.AlignRight
            onClicked: {
                Qt.callLater(() => Qt.application.clipboard.setText(codeBubble.codeText))
            }
        }
    }
}

