import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQuick.Controls.Material
import QtQuick.Effects

ApplicationWindow {
    id: windowRoot
    objectName: "windowRoot"
    width: 950
    height: 650
    minimumWidth: 600
    minimumHeight: 400
    visible: true
    title: "Eidolon"
    color: "transparent"  // ✅ This is important
    flags: Qt.FramelessWindowHint | Qt.Window
    property string assistantState: "ready"
    property bool backendReady: false


    Rectangle {
        id: backgroundFixLayer
        anchors.fill: parent
        color: "#202123"   // ✅ This is your real background now
        z: -99
    }


    // ✅ Signal to notify Python when typing animation completes
    signal typingAnimationComplete()

    // === ListModel ===
    ListModel {
        id: chatModel
        objectName: "chatModel"
    }

    // === Core Functions ===
    function clearChatModel() {
        chatModel.clear()
    }

    function appendAnimatedMessage(role, fullText, delay = 50) {
        chatModel.append({ role: role, content: "" })
        let rowIndex = chatModel.count - 1

        let timer = Qt.createQmlObject(`
            import QtQuick
            Timer {
                property int charIndex: 0
                property string currentText: ""
                property int targetRow: ${rowIndex}
                property string targetText: ""
                interval: ${delay}
                repeat: true

                onTriggered: {
                    if (charIndex < targetText.length) {
                        currentText += targetText.charAt(charIndex)
                        charIndex++
                        chatModel.setProperty(targetRow, "content", currentText)

                        Qt.callLater(() => mainChatView.positionViewAtEnd())
                    } else {
                        stop()
                        destroy()

                        // ✅ Correct single notification without undefined checks
                        windowRoot.typingAnimationComplete()
                    }
                }
            }
        `, windowRoot)

        timer.targetText = fullText
        timer.start()
    }


    function appendMessage(role, content) {
        chatModel.append({ role: role, content: content })
        Qt.callLater(() => mainChatView.positionViewAtEnd())
    }

    function setAssistantState(newState) {
        assistantState = newState
        console.log("🔄 Assistant state changed to:", newState)
    }

    function splitMessageContent(message) {
        if (!message || typeof message !== 'string') {
            return [{
                type: "text",
                content: message || ""
            }]
        }
        
        var parts = []
        var currentIndex = 0
        var codeBlockRegex = /```[\s\S]*?```/g
        var match
        
        while ((match = codeBlockRegex.exec(message)) !== null) {
            // Add text before code block if any
            if (match.index > currentIndex) {
                var textPart = message.substring(currentIndex, match.index).trim()
                if (textPart.length > 0) {
                    parts.push({
                        type: "text",
                        content: textPart
                    })
                }
            }
            
            // Add code block
            parts.push({
                type: "code",
                content: match[0]
            })
            
            currentIndex = match.index + match[0].length
        }
        
        // Add remaining text after last code block
        if (currentIndex < message.length) {
            var remainingText = message.substring(currentIndex).trim()
            if (remainingText.length > 0) {
                parts.push({
                    type: "text",
                    content: remainingText
                })
            }
        }
        
        // If no code blocks found, return the whole message as text
        if (parts.length === 0) {
            parts.push({
                type: "text",
                content: message
            })
        }
        
        return parts
    }

    function copyToClipboard(text) {
        if (!text || text.trim() === "") {
            console.log("❌ No text to copy")
            return false
        }
        
        console.log("🔄 Copying text via backend clipboard...")
        
        try {
            // Use the clipboard wrapper from your backend
            if (typeof clipboard !== 'undefined' && clipboard.setText) {
                clipboard.setText(text)
                console.log("✅ Text copied successfully")
                return true
            }
        } catch (e) {
            console.log("❌ Clipboard copy failed:", e.toString())
        }
        
        console.log("❌ Clipboard not available")
        return false
    }

    function scheduleThinkingDelay(delayMs) {
        thinkingTimer.interval = delayMs
        thinkingTimer.start()
    }

    function scheduleReadyState(delayMs) {
        readyStateTimer.interval = delayMs
        readyStateTimer.start()
    }

    // === Timers for state transitions ===
    Timer {
        id: thinkingTimer
        repeat: false
        onTriggered: {
            // Call the continue_after_thinking function from backend
            if (typeof backend !== 'undefined' && backend.continueAfterThinking) {
                backend.continueAfterThinking()
            }
        }
    }

    Timer {
        id: readyStateTimer
        repeat: false
        onTriggered: {
            // Set ready state and notify backend
            windowRoot.setAssistantState("ready")
            windowRoot.typingAnimationComplete()
        }
    }

    // === Resizable Corner Handle (bottom-right)
    Item {
        id: resizeHandle
        width: 20
        height: 20
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        z: 999

        // ✨ Visual diagonal grip lines
        Canvas {
            anchors.fill: parent
            onPaint: {
                var ctx = getContext("2d")
                ctx.clearRect(0, 0, width, height)
                ctx.strokeStyle = "#888888"
                ctx.lineWidth = 1.2

                for (let i = 0; i < 3; i++) {
                    let offset = 4 + i * 4
                    ctx.beginPath()
                    ctx.moveTo(width - offset, height)
                    ctx.lineTo(width, height - offset)
                    ctx.stroke()
                }
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.SizeFDiagCursor

            property int lastMouseX: 0
            property int lastMouseY: 0

            onPressed: {
                lastMouseX = mouse.x
                lastMouseY = mouse.y
            }

            onPositionChanged: {
                let dx = mouse.x - lastMouseX
                let dy = mouse.y - lastMouseY

                let newWidth = windowRoot.width + dx
                let newHeight = windowRoot.height + dy

                if (newWidth >= windowRoot.minimumWidth)
                    windowRoot.width = newWidth
                if (newHeight >= windowRoot.minimumHeight)
                    windowRoot.height = newHeight

                lastMouseX = mouse.x
                lastMouseY = mouse.y
            }
        }
    }


    // === Main container with proper margins for the border ===
    Rectangle {
        id: mainContainer
        anchors.fill: parent
        anchors.margins: 4  // Give space for the glowing border
        radius: 16
        color: "#202123"
        
        // Glowing border rectangle - positioned around the main container
        Rectangle {
            id: glowingBorder
            anchors.fill: parent
            anchors.margins: -4  // Extend beyond the main container
            radius: 20
            color: "transparent"
            border.color: "#00ffff"
            border.width: 2
            z: -1  // Behind the main content

            layer.enabled: true
            layer.effect: MultiEffect {
                shadowEnabled: true
                shadowColor: "#00ffff"
                shadowBlur: 1.0
                shadowVerticalOffset: 0
                shadowHorizontalOffset: 0
            }
        }

        RowLayout {
            anchors.fill: parent
            spacing: 0

            // === Fancy Sidebar Component ===
            SidebarPanel {
                id: mainSidebarPanel
                sidebarVisible: true
                Layout.preferredWidth: 280
                Layout.fillHeight: true
            }


            // === Main Chat Area ===
            Rectangle {
                id: mainChatArea
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#202123"
                radius: 12

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12

                    // Header section
                    Rectangle {
                        Layout.preferredHeight: 150
                        Layout.fillWidth: true
                        color: "transparent"

                        Image {
                            id: headerBanner
                            anchors.centerIn: parent
                            source: "banner.png"
                            width: 240
                            height: 120
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                            mipmap: true
                        }

                        Row {
                            spacing: 6
                            anchors.top: parent.top
                            anchors.right: parent.right
                            anchors.margins: 10

                            Rectangle {
                                width: 20; height: 20; radius: 4
                                color: "#444"; border.color: "#888"
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: windowRoot.showMinimized()
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: "–"
                                    color: "white"
                                    font.pixelSize: 14
                                }
                            }

                            Rectangle {
                                width: 20; height: 20; radius: 4
                                color: "#444"; border.color: "#888"
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        if (windowRoot.visibility === Window.Maximized) {
                                            windowRoot.visibility = Window.Windowed
                                        } else {
                                            windowRoot.visibility = Window.Maximized
                                        }
                                    }
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: "▢"
                                    color: "white"
                                    font.pixelSize: 12
                                }
                            }

                            Rectangle {
                                width: 20; height: 20; radius: 4
                                color: "#aa0000"; border.color: "#ff4444"
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: Qt.quit()
                                }
                                Text {
                                    anchors.centerIn: parent
                                    text: "×"
                                    color: "white"
                                    font.pixelSize: 14
                                }
                            }
                        }

                        MouseArea {
                            id: headerDragArea
                            anchors {
                                left: parent.left
                                right: parent.right
                                top: parent.top
                                bottom: headerBanner.top
                            }
                            z: -1
                            property int startX: 0
                            property int startY: 0

                            onPressed: (mouse) => {
                                startX = mouse.x
                                startY = mouse.y
                            }

                            onPositionChanged: (mouse) => {
                                windowRoot.x += mouse.x - startX
                                windowRoot.y += mouse.y - startY
                            }
                        }
                    }

                    // Chat messages list
                    ListView {
                        id: mainChatView
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        spacing: 20
                        clip: true
                        interactive: true
                        focus: true
                        model: chatModel

                        onCountChanged: Qt.callLater(() => mainChatView.positionViewAtEnd())

                        ScrollBar.vertical: ScrollBar {
                            policy: ScrollBar.AlwaysOn
                        }

                        delegate: Item {
                            id: messageItem
                            width: mainChatView.width
                            height: Math.max(messageBubble.implicitHeight + 20, 60)

                            // Cache the model data to avoid binding issues
                            readonly property string msgRole: model.role || "assistant"
                            readonly property string msgContent: model.content || ""

                            Rectangle {
                                id: messageBubble
                                width: mainChatView.width * 0.75
                                implicitHeight: messageContentColumn.implicitHeight + 24
                                radius: 12
                                color: msgRole === "user" ? "#004c40" : "#1a1a1a"

                                anchors.right: msgRole === "user" ? parent.right : undefined
                                anchors.left: msgRole !== "user" ? parent.left : undefined
                                anchors.rightMargin: msgRole === "user" ? 12 : 0
                                anchors.leftMargin: msgRole !== "user" ? 12 : 0
                                anchors.verticalCenter: parent.verticalCenter

                                Column {
                                    id: messageContentColumn
                                    anchors.left: parent.left
                                    anchors.right: parent.right
                                    anchors.top: parent.top
                                    anchors.margins: 12
                                    spacing: 8

                                    Text {
                                        text: msgRole === "user" ? "🧠 You:" : "🤖 Eidolon:"
                                        font.pixelSize: 13
                                        font.bold: true
                                        color: "#00ffff"
                                        wrapMode: Text.Wrap
                                        width: parent.width
                                        horizontalAlignment: msgRole === "user" ? Text.AlignRight : Text.AlignLeft
                                    }

                                    Column {
                                        width: parent.width
                                        spacing: 4

                                        Repeater {
                                            id: messageContentRepeater
                                            model: splitMessageContent(msgContent)

                                            delegate: Loader {
                                                width: parent.width

                                                readonly property var partData: modelData || { type: "text", content: "" }
                                                readonly property string partType: partData.type || "text"
                                                readonly property string partContent: partData.content || ""
                                                readonly property string messageRole: msgRole

                                                sourceComponent: partType === "code" ? codeDelegate : textDelegate
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // Status and input area
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6

                        Label {
                            id: statusLabel
                            text: {
                                if (windowRoot.assistantState === "thinking") return "🧠 Thinking...";
                                else if (windowRoot.assistantState === "typing") return "✍ Typing...";
                                else return "🔔 Ready";
                            }
                            color: "#888"
                            font.italic: true
                            font.pixelSize: 12
                            Layout.alignment: Qt.AlignLeft
                            Layout.leftMargin: 12
                        }

                        RowLayout {
                            spacing: 6
                            Layout.margins: 12
                            Layout.fillWidth: true

                            TextField {
                                id: mainEntryField
                                Layout.fillWidth: true
                                font.pixelSize: 14
                                placeholderText: "Type your message..."
                                color: "#00eeee"
                                background: Rectangle {
                                    color: "#2f2f33"
                                    radius: 8
                                }
                                onAccepted: {
                                    if (mainEntryField.text.trim() !== "") {
                                        if (typeof backend !== 'undefined' && backend.sendMessage) {
                                            backend.sendMessage(mainEntryField.text)
                                        }
                                        mainEntryField.text = ""
                                    }
                                }

                                Keys.onPressed: (event) => {
                                    if (event.key === Qt.Key_Return && !(event.modifiers & Qt.ShiftModifier)) {
                                        accepted()
                                        event.accepted = true
                                    }
                                }
                            }


                            Button {
                                text: "Send"
                                enabled: mainEntryField.text.trim() !== ""
                                background: Rectangle { 
                                    color: parent.enabled ? "#00ffff" : "#666666"
                                    radius: 8 
                                }
                                onClicked: {
                                    if (mainEntryField.text.trim() !== "") {
                                        if (typeof backend !== 'undefined' && backend.sendMessage) {
                                            backend.sendMessage(mainEntryField.text)
                                        }
                                        mainEntryField.text = ""
                                    }
                                }
                            }

                            Button {
                                text: "🎙"
                                background: Rectangle { color: "#00aaaa"; radius: 8 }
                                onClicked: {
                                    if (typeof backend !== 'undefined' && backend.sendVoiceInput) {
                                        backend.sendVoiceInput()
                                    }
                                }
                            }

                            Button {
                                text: "🧠"
                                background: Rectangle { color: "#00aaaa"; radius: 8 }
                                onClicked: {
                                    if (typeof backend !== 'undefined' && backend.openMemory) {
                                        backend.openMemory()
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // === Text delegate component ===
        Component {
            id: textDelegate

            Item {
                width: parent.width
                height: textContent.implicitHeight

                Text {
                    id: textContent
                    text: partContent
                    font.pixelSize: 15
                    color: "white"
                    wrapMode: Text.Wrap
                    width: parent.width
                    horizontalAlignment: messageRole === "user" ? Text.AlignRight : Text.AlignLeft
                }

                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton

                    onClicked: function(mouse) {
                        if (mouse.button === Qt.RightButton) {
                            textContextMenu.popup()
                        }
                    }

                    Menu {
                        id: textContextMenu

                        MenuItem {
                            text: "Copy Text"
                            onTriggered: {
                                var success = windowRoot.copyToClipboard(partContent)
                                if (success) {
                                    textContent.color = "#00ffff"
                                    textFeedbackTimer.start()
                                }
                            }
                        }
                    }

                    Timer {
                        id: textFeedbackTimer
                        interval: 500
                        running: false
                        onTriggered: textContent.color = "white"
                    }
                }
            }
        }

        // === Code delegate component ===
        Component {
            id: codeDelegate
            Rectangle {
                readonly property string cleanedCode: partContent.replace(/^```[a-zA-Z]*\n?/g, "").replace(/```$/g, "")

                width: parent.width
                implicitHeight: codeContentColumn.implicitHeight + 16
                color: "#111"
                radius: 6
                border.color: "#00ffff"
                border.width: 1

                // Right-click context menu for code blocks
                MouseArea {
                    anchors.fill: parent
                    acceptedButtons: Qt.RightButton
                    propagateComposedEvents: true
                    
                    onClicked: (mouse) => {
                        if (mouse.button === Qt.RightButton) {
                            codeContextMenu.popup()
                        }
                    }

                    Menu {
                        id: codeContextMenu

                        MenuItem {
                            text: "Copy Code"
                            onTriggered: {
                                var success = windowRoot.copyToClipboard(cleanedCode)
                                if (success) {
                                    codeCopyButton.color = "#00ff00"
                                    contextMenuFeedbackTimer.start()
                                }
                            }
                        }
                        
                        MenuItem {
                            text: "Copy Raw Text"
                            onTriggered: {
                                var success = windowRoot.copyToClipboard(partContent)
                                if (success) {
                                    codeCopyButton.color = "#00ff00"
                                    contextMenuFeedbackTimer.start()
                                }
                            }
                        }
                    }
                    
                    Timer {
                        id: contextMenuFeedbackTimer
                        interval: 1000
                        onTriggered: {
                            codeCopyButton.color = "#00aaaa"
                        }
                    }
                }

                Column {
                    id: codeContentColumn
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 8
                    spacing: 8

                    ScrollView {
                        width: parent.width
                        height: Math.min(codeDisplayText.implicitHeight, 300)
                        clip: true

                        Text {
                            id: codeDisplayText
                            text: cleanedCode
                            font.pixelSize: 14
                            font.family: "Courier New, Monaco, 'Lucida Console', monospace"
                            color: "#00ffff"
                            wrapMode: Text.Wrap
                            width: parent.width
                        }
                    }

                    Rectangle {
                        id: codeCopyButton
                        width: 60
                        height: 24
                        radius: 4
                        color: "#00aaaa"
                        anchors.horizontalCenter: parent.horizontalCenter

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            
                            onClicked: {
                                console.log("🔄 Copy button clicked")
                                var success = windowRoot.copyToClipboard(cleanedCode)
                                if (success) {
                                    codeCopyFeedback.start()
                                } else {
                                    // Show error feedback
                                    codeCopyButton.color = "#ff4444"
                                    codeErrorTimer.start()
                                }
                            }
                            
                            onPressed: {
                                codeCopyButton.color = "#008888"
                            }
                            
                            onReleased: {
                                if (codeCopyButton.color === "#008888") {
                                    codeCopyButton.color = "#00aaaa"
                                }
                            }
                        }

                        Text {
                            anchors.centerIn: parent
                            text: "Copy"
                            color: "white"
                            font.pixelSize: 12
                        }

                        Timer {
                            id: codeCopyFeedback
                            interval: 200
                            onTriggered: {
                                codeCopyButton.color = "#00ff00"
                                codeResetTimer.start()
                            }
                        }
                        
                        Timer {
                            id: codeResetTimer
                            interval: 800
                            onTriggered: {
                                codeCopyButton.color = "#00aaaa"
                            }
                        }
                        
                        Timer {
                            id: codeErrorTimer
                            interval: 1000
                            onTriggered: {
                                codeCopyButton.color = "#00aaaa"
                            }
                        }
                    }
                }
            }
        }
    }

    Connections {
    target: backend

    function onMessageReceived(role, content) {
        console.log("📥 Message received from backend:", role, content)
        appendMessage(role, content)
    }

    function onResponseReceived(content) {
        console.log("✅ Response received from backend:", content)
        appendMessage("assistant", content)
    }

    function onMessageSent(text) {
        console.log("📤 Message sent from QML:", text)
    }
}


    // === Connect to backend when component is ready ===
    Component.onCompleted: {
        console.log("🚀 QML Window initialized")
        
        // Connect the typing animation complete signal to backend if it exists
        if (typeof backend !== 'undefined' && backend.onTypingComplete) {
            typingAnimationComplete.connect(backend.onTypingComplete)
            console.log("✅ Connected typingAnimationComplete signal to backend")
        }
    }
}