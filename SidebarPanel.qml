// SidebarPanel.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root
    property string currentChatName: ""
    property int sidebarWidth: 44
    property bool sidebarVisible: false
    
    width: sidebarWidth
    height: parent ? parent.height : 600

    // Safe backend reference
    function getBackend() {
        return (typeof sidebarBackend !== "undefined") ? sidebarBackend : null
    }

    // Fixed: Use Loader to safely handle Connections when backend is available
    Loader {
        active: getBackend() !== null
        sourceComponent: Connections {
            target: getBackend()

            function onSidebarVisibilityChanged(visible) {
                sidebarVisible = visible
                sidebarWidth = visible ? 280 : 44
            }

            function onChatMessageAdded(chatName, message) {
                console.log("💾 Chat message added, triggering save:", chatName)
                var backend = getBackend()
                if (backend) {
                    backend.saveCurrentChat()
                }
            }

            function onChatHistoryChanged() {
                console.log("📝 Chat history updated, refreshing list")
                var backend = getBackend()
                if (chatList && chatList.model && backend) {
                    console.log("🔄 Updating ListView model, current count:", chatList.count)
                    chatList.model = backend.chatHistory
                    console.log("🔄 ListView model updated, new count:", chatList.count)
                } else {
                    console.log("⚠️ Cannot update ListView - missing components")
                }
            }

            function onCurrentChatChanged(newChatName) {
                console.log("🔄 Current chat changed to:", newChatName)
                currentChatName = newChatName
                var backend = getBackend()
                if (backend) {
                    backend.saveCurrentChat()
                }
            }
        }
    }
    
    Timer {
        id: saveTimer
        interval: 2000
        repeat: false
        onTriggered: {
            var backend = getBackend()
            if (backend) {
                console.log("⏰ Auto-save timer triggered")
                backend.saveCurrentChat()
                backend.refreshChatHistory()
            }
        }
    }
    
    Timer {
        id: periodicSaveTimer
        interval: 30000
        repeat: true
        running: true
        onTriggered: {
            var backend = getBackend()
            if (backend && backend.hasUnsavedChanges) {
                console.log("🔄 Periodic save triggered")
                backend.saveCurrentChat()
            }
        }
    }

    Rectangle {
        id: sidebar
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: sidebarVisible ? 280 : 0
        color: "transparent"
        clip: true
        
        Behavior on width {
            NumberAnimation {
                duration: 300
                easing.type: Easing.OutCubic
            }
        }
        
        Rectangle {
            anchors.fill: parent
            color: "#1a1a1a"
            opacity: 0.85
            
            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "#25ffffff" }
                    GradientStop { position: 0.3; color: "#15ffffff" }
                    GradientStop { position: 1.0; color: "#05ffffff" }
                }
            }
            
            Rectangle {
                anchors.fill: parent
                color: "transparent"
                border.color: "#30ffffff"
                border.width: 1
            }
        }
        
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 16
            anchors.topMargin: 56
            spacing: 16
            visible: sidebar.width > 50
            
            // Header
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 60
                color: "#20ffffff"
                radius: 12
                border.color: "#30ffffff"
                border.width: 1
                
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    
                    Label {
                        text: "🧠 Eidolon"
                        font.pixelSize: 22
                        font.bold: true
                        color: "#00d4ff"
                        Layout.fillWidth: true
                    }
                }
            }
            
            // New Chat Button
            Button {
                id: newChatBtn
                text: "➕ New Chat"
                Layout.fillWidth: true
                Layout.preferredHeight: 50
                
                background: Rectangle {
                    color: newChatBtn.pressed ? "#4000d4ff" : (newChatBtn.hovered ? "#3000d4ff" : "#2000a0b8")
                    radius: 12
                    border.color: newChatBtn.pressed ? "#80ffffff" : "#40ffffff"
                    border.width: 1
                    
                    Behavior on color { ColorAnimation { duration: 200 } }
                    Behavior on border.color { ColorAnimation { duration: 200 } }
                }
                
                contentItem: Text {
                    text: newChatBtn.text
                    font.pixelSize: 15
                    font.weight: Font.Medium
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                
                scale: newChatBtn.pressed ? 0.96 : (newChatBtn.hovered ? 1.02 : 1.0)
                Behavior on scale { NumberAnimation { duration: 150 } }
                
                onClicked: {
                    console.log("New chat clicked - saving current chat first")
                    var backend = getBackend()
                    if (backend) {
                        backend.saveCurrentChat()
                        backend.newChatRequested()
                    }
                }
            }
            
            // Search Field
            TextField {
                id: chatSearch
                Layout.fillWidth: true
                Layout.preferredHeight: 42
                placeholderText: "🔍 Search chats…"
                
                background: Rectangle {
                    color: "#15ffffff"
                    radius: 12
                    border.color: chatSearch.activeFocus ? "#8000d4ff" : "#30ffffff"
                    border.width: 1
                    
                    Behavior on border.color { ColorAnimation { duration: 200 } }
                }
                
                color: "#ffffff"
                font.pixelSize: 14
                leftPadding: 16
                rightPadding: 16
                placeholderTextColor: "#888888"
                
                onTextChanged: {
                    console.log("🔍 Filter text changed:", chatSearch.text)
                    var backend = getBackend()
                    if (backend) {
                        console.log("🔍 Calling filterChats with:", chatSearch.text)
                        backend.filterChats(chatSearch.text)
                        console.log("🔍 filterChats called")
                    } else {
                        console.log("⚠️ Backend not available for filtering")
                    }
                }
            }
            
            // Chat List Container
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                color: "#10ffffff"
                radius: 12
                border.color: "#20ffffff"
                border.width: 1
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    
                    RowLayout {
                        Layout.fillWidth: true
                        
                        Label {
                            text: "Recent Chats"
                            font.pixelSize: 13
                            font.weight: Font.Medium
                            color: "#cccccc"
                            Layout.fillWidth: true
                            leftPadding: 8
                        }
                        
                        Button {
                            id: refreshBtn
                            text: "🔄"
                            Layout.preferredWidth: 28
                            Layout.preferredHeight: 28
                            
                            background: Rectangle {
                                color: refreshBtn.pressed ? "#30ffffff" : (refreshBtn.hovered ? "#20ffffff" : "#10ffffff")
                                radius: 6
                                border.color: refreshBtn.hovered ? "#40ffffff" : "#25ffffff"
                                border.width: 1
                                
                                Behavior on color { ColorAnimation { duration: 150 } }
                            }
                            
                            contentItem: Text {
                                text: refreshBtn.text
                                font.pixelSize: 10
                                color: "#ffffff"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            onClicked: {
                                console.log("🔄 Manual refresh requested")
                                var backend = getBackend()
                                if (backend) {
                                    console.log("🔄 Calling refreshChatHistory()")
                                    backend.refreshChatHistory()
                                    console.log("🔄 refreshChatHistory() called")
                                } else {
                                    console.log("⚠️ Backend not available for refresh")
                                }
                            }
                        }
                    }
                    
                    ListView {
                        id: chatList
                        Layout.fillHeight: true
                        Layout.fillWidth: true
                        model: sidebarBackend.chatHistory

                        // ✅ Prevent auto-scroll on selection
                        highlightRangeMode: ListView.NoHighlightRange
                        preferredHighlightBegin: 0
                        preferredHighlightEnd: 0
                        highlightMoveDuration: 0
                        snapMode: ListView.NoSnap

                        // ✅ Allow smooth manual scrolling
                        interactive: true
                        cacheBuffer: 500

                        onCountChanged: {
                            console.log("📋 Chat list updated, count:", count)
                        }

                        Component.onCompleted: {
                            console.log("🔍 ListView completed, model count:", count)
                            console.log("🔍 Backend available:", typeof sidebarBackend !== "undefined")
                            if (typeof sidebarBackend !== "undefined") {
                                console.log("🔍 Backend chatHistory length:", sidebarBackend.chatHistory ? sidebarBackend.chatHistory.length : "undefined")
                            }
                        }

                        delegate: Rectangle {
                            width: ListView.view.width
                            height: 60
                            color: mouseArea.pressed ? "#40ffffff" : (mouseArea.containsMouse ? "#25ffffff" : "#10ffffff")
                            radius: 10
                            border.color: mouseArea.containsMouse ? "#30ffffff" : "#15ffffff"
                            border.width: 1

                            scale: mouseArea.pressed ? 0.98 : (mouseArea.containsMouse ? 1.02 : 1.0)

                            Behavior on color { ColorAnimation { duration: 150 } }
                            Behavior on scale { NumberAnimation { duration: 150 } }
                            Behavior on border.color { ColorAnimation { duration: 150 } }

                            ColumnLayout {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.margins: 14
                                spacing: 4

                                Text {
                                    text: (modelData && modelData.name) ? modelData.name : "Untitled Chat"
                                    color: "#ffffff"
                                    font.pixelSize: 14
                                    font.weight: Font.Medium
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                }

                                Text {
                                    text: (modelData && modelData.timestamp) ? modelData.timestamp : "Unknown time"
                                    color: "#999999"
                                    font.pixelSize: 11
                                    Layout.fillWidth: true
                                }
                            }

                            MouseArea {
                                id: mouseArea
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    const backend = getBackend()
                                    if (!backend) {
                                        console.log("⚠️ Backend not available.")
                                        return
                                    }

                                    const chatName = (modelData && modelData.name) ? modelData.name : "Untitled Chat"
                                    console.log("🖱️ Chat clicked:", chatName)
                                    console.log("🖱️ Current chat:", backend.currentChatName)
                                    
                                    if (backend.currentChatName !== chatName) {
                                        console.log("💾 Saving current chat before switching to:", chatName)
                                        backend.saveCurrentChat()
                                        console.log("📁 Loading chat:", chatName)
                                        backend.loadChat(chatName)
                                        console.log("✅ loadChat called")
                                    } else {
                                        console.log("🟡 Ignored duplicate chat load:", chatName)
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // User Profile Section
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 180
                color: "#20ffffff"
                radius: 16
                border.color: "#40ffffff"
                border.width: 1
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 12
                    
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 60
                        color: "#15ffffff"
                        radius: 12
                        border.color: "#25ffffff"
                        border.width: 1
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 12
                            
                            Rectangle {
                                width: 40
                                height: 40
                                radius: 20
                                color: "#00d4ff"
                                border.color: "#80ffffff"
                                border.width: 2
                                
                                Text {
                                    anchors.centerIn: parent
                                    text: "JD"
                                    color: "#1e1e1e"
                                    font.pixelSize: 16
                                    font.bold: true
                                }
                            }
                            
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                
                                Text {
                                    text: "John Doe"
                                    color: "#ffffff"
                                    font.pixelSize: 15
                                    font.weight: Font.Medium
                                }
                                
                                Text {
                                    text: "john.doe@example.com"
                                    color: "#aaaaaa"
                                    font.pixelSize: 11
                                }
                            }
                        }
                    }
                    
                    Button {
                        id: feedbackBtn
                        text: "💬 Feedback"
                        Layout.fillWidth: true
                        Layout.preferredHeight: 36
                        
                        background: Rectangle {
                            color: feedbackBtn.pressed ? "#30ffffff" : (feedbackBtn.hovered ? "#20ffffff" : "#10ffffff")
                            radius: 10
                            border.color: feedbackBtn.hovered ? "#40ffffff" : "#25ffffff"
                            border.width: 1
                            
                            Behavior on color { ColorAnimation { duration: 150 } }
                            Behavior on border.color { ColorAnimation { duration: 150 } }
                        }
                        
                        contentItem: Text {
                            text: feedbackBtn.text
                            font.pixelSize: 12
                            font.weight: Font.Medium
                            color: "#ffffff"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        
                        scale: feedbackBtn.pressed ? 0.96 : (feedbackBtn.hovered ? 1.02 : 1.0)
                        Behavior on scale { NumberAnimation { duration: 150 } }
                        
                        onClicked: {
                            console.log("Open feedback panel")
                            var backend = getBackend()
                            if (backend) {
                                backend.openFeedback()
                            }
                        }
                    }
                    
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        
                        Button {
                            id: settingsBtn
                            text: "⚙️ Settings"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36
                            
                            background: Rectangle {
                                color: settingsBtn.pressed ? "#30ffffff" : (settingsBtn.hovered ? "#20ffffff" : "#10ffffff")
                                radius: 10
                                border.color: settingsBtn.hovered ? "#40ffffff" : "#25ffffff"
                                border.width: 1
                                
                                Behavior on color { ColorAnimation { duration: 150 } }
                                Behavior on border.color { ColorAnimation { duration: 150 } }
                            }
                            
                            contentItem: Text {
                                text: settingsBtn.text
                                font.pixelSize: 11
                                font.weight: Font.Medium
                                color: "#ffffff"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            scale: settingsBtn.pressed ? 0.96 : (settingsBtn.hovered ? 1.02 : 1.0)
                            Behavior on scale { NumberAnimation { duration: 150 } }
                            
                            onClicked: {
                                settingsPanel.visible = !settingsPanel.visible
                                console.log("Settings toggled:", settingsPanel.visible)
                            }
                        }
                        
                        Button {
                            id: logoutBtn
                            text: "🚪 Logout"
                            Layout.fillWidth: true
                            Layout.preferredHeight: 36

                            background: Rectangle {
                                color: logoutBtn.pressed ? "#40ff6666" : (logoutBtn.hovered ? "#30ff4444" : "#10ffffff")
                                radius: 10
                                border.color: logoutBtn.hovered ? "#60ff6666" : "#25ffffff"
                                border.width: 1

                                Behavior on color { ColorAnimation { duration: 150 } }
                                Behavior on border.color { ColorAnimation { duration: 150 } }
                            }

                            contentItem: Text {
                                text: logoutBtn.text
                                font.pixelSize: 11
                                font.weight: Font.Medium
                                color: "#ffffff"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            
                            scale: logoutBtn.pressed ? 0.96 : (logoutBtn.hovered ? 1.02 : 1.0)
                            Behavior on scale { NumberAnimation { duration: 150 } }

                            onClicked: {
                                console.log("Logout clicked - saving current chat first")
                                var backend = getBackend()
                                if (backend) {
                                    backend.saveCurrentChat()
                                    backend.logout()
                                }
                            }
                        }
                    }
                }
            }
            
            // Settings Panel
            Rectangle {
                id: settingsPanel
                visible: false
                Layout.fillWidth: true
                Layout.preferredHeight: visible ? 80 : 0
                color: "#15ffffff"
                radius: 12
                border.color: "#30ffffff"
                border.width: 1
                clip: true
                
                Behavior on Layout.preferredHeight {
                    NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
                }
                
                opacity: visible ? 1.0 : 0.0
                Behavior on opacity { NumberAnimation { duration: 200 } }
                
                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 8
                    
                    Label {
                        text: "⚙️ Settings"
                        font.pixelSize: 13
                        font.weight: Font.Medium
                        color: "#cccccc"
                    }
                    
                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 40
                        color: "#10ffffff"
                        radius: 8
                        border.color: "#20ffffff"
                        border.width: 1
                        
                        RowLayout {
                            anchors.fill: parent
                            anchors.margins: 10
                            spacing: 10
                            
                            Label {
                                text: "Animated Typing"
                                font.pixelSize: 12
                                color: "#ffffff"
                                Layout.fillWidth: true
                            }
                            
                            Rectangle {
                                id: customSwitch
                                width: 44
                                height: 22
                                radius: 11
                                color: switchActive ? "#00d4ff" : "#333333"
                                border.color: "#555555"
                                border.width: 1
                                
                                // Fixed: Initialize switchActive as false, set it in Component.onCompleted
                                property bool switchActive: false
                                
                                Component.onCompleted: {
                                    var backend = getBackend()
                                    if (backend && backend.animatedTypingEnabled !== undefined) {
                                        customSwitch.switchActive = backend.animatedTypingEnabled
                                    }
                                }
                                
                                Behavior on color { ColorAnimation { duration: 200 } }
                                
                                Rectangle {
                                    id: switchIndicator
                                    x: customSwitch.switchActive ? parent.width - width - 2 : 2
                                    y: 2
                                    width: 18
                                    height: 18
                                    radius: 9
                                    color: "#ffffff"
                                    border.color: "#dddddd"
                                    border.width: 1
                                    
                                    Behavior on x { NumberAnimation { duration: 200 } }
                                }
                                
                                MouseArea {
                                    anchors.fill: parent
                                    onClicked: {
                                        var backend = getBackend()
                                        if (backend) {
                                            backend.animatedTypingEnabled = !backend.animatedTypingEnabled
                                            customSwitch.switchActive = backend.animatedTypingEnabled
                                            console.log("Animated typing:", backend.animatedTypingEnabled)
                                        }
                                    }
                                }
                                
                                // Fixed: Use Loader for safe Connections
                                Loader {
                                    active: getBackend() !== null
                                    sourceComponent: Connections {
                                        target: getBackend()
                                        function onAnimatedTypingEnabledChanged() {
                                            var backend = getBackend()
                                            if (backend) {
                                                customSwitch.switchActive = backend.animatedTypingEnabled
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    // Toggle Button
    Button {
        id: collapseBtn
        width: 40
        height: 40
        anchors.top: parent.top
        anchors.topMargin: 12
        x: sidebarVisible ? sidebar.width - 52 : 12
        z: 100
        
        Behavior on x {
            NumberAnimation {
                duration: 300
                easing.type: Easing.OutCubic
            }
        }
        
        background: Rectangle {
            color: collapseBtn.pressed ? "#40ffffff" : (collapseBtn.hovered ? "#30ffffff" : "#20ffffff")
            radius: 10
            border.color: collapseBtn.hovered ? "#60ffffff" : "#40ffffff"
            border.width: 1
            
            Behavior on color { ColorAnimation { duration: 150 } }
            Behavior on border.color { ColorAnimation { duration: 150 } }
        }
        
        contentItem: Text {
            text: sidebarVisible ? "←" : "→"
            font.pixelSize: 16
            color: "#ffffff"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        
        scale: collapseBtn.pressed ? 0.9 : (collapseBtn.hovered ? 1.1 : 1.0)
        Behavior on scale { NumberAnimation { duration: 150 } }
        
        onClicked: {
            console.log("Toggle sidebar clicked")
            var backend = getBackend()
            if (backend) {
                backend.toggleSidebar()
            }
        }
    }
    
    Component.onDestruction: {
        var backend = getBackend()
        if (backend) {
            console.log("🧹 Component destroying, final save")
            backend.saveCurrentChat()
        }
    }
}