import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtGraphicalEffects 1.15

Rectangle {
    id: root
    color: "#f5f5f5"

    // Phát hiện màn hình nhỏ (RPi 3.5 inch: 480x320)
    property bool isSmallScreen: root.width <= 520 || root.height <= 400
    // Ẩn nút khi fullscreen trên màn nhỏ
    property bool hideWindowButtons: isSmallScreen

    // 信号定义 - 与 Python 回调对接
    signal manualButtonPressed()
    signal manualButtonReleased()
    signal autoButtonClicked()
    signal abortButtonClicked()
    signal modeButtonClicked()
    signal sendButtonClicked(string text)
    signal settingsButtonClicked()
    // 标题栏相关信号
    signal titleMinimize()
    signal titleClose()
    signal titleDragStart(real mouseX, real mouseY)
    signal titleDragMoveTo(real mouseX, real mouseY)
    signal titleDragEnd()

    // 主布局
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // 自定义标题栏：Logo căn giữa + 最小化、关闭、可拖动
        Rectangle {
            id: titleBar
            Layout.fillWidth: true
            // Giảm chiều cao title bar trên màn nhỏ
            Layout.preferredHeight: isSmallScreen ? 44 : 56
            // Gradient nhẹ cho title bar
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#ffffff" }
                GradientStop { position: 1.0; color: "#f7f8fa" }
            }
            border.width: 0

            // Đường viền dưới tinh tế
            Rectangle {
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                height: 1
                color: "#e8e8e8"
            }

            // 整条标题栏拖动
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton
                onPressed: {
                    root.titleDragStart(mouse.x, mouse.y)
                }
                onPositionChanged: {
                    if (pressed) {
                        root.titleDragMoveTo(mouse.x, mouse.y)
                    }
                }
                onReleased: {
                    root.titleDragEnd()
                }
                z: 0
            }

            // Logo và tên trường - CĂNG ĐẦY CHIỀU NGANG
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 8
                anchors.rightMargin: hideWindowButtons ? 8 : 50  // Để chỗ cho nút nếu có
                spacing: isSmallScreen ? 6 : 10
                z: 1

                // Logo trường
                Image {
                    id: schoolLogo
                    source: displayModel ? displayModel.logoPath : ""
                    Layout.preferredWidth: isSmallScreen ? 32 : 48
                    Layout.preferredHeight: isSmallScreen ? 32 : 48
                    Layout.maximumWidth: isSmallScreen ? 32 : 48
                    Layout.maximumHeight: isSmallScreen ? 32 : 48
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    antialiasing: true
                    cache: true
                    visible: status === Image.Ready
                }

                // Tên trường - CĂNG ĐẦY
                Column {
                    Layout.fillWidth: true
                    spacing: isSmallScreen ? 0 : 2
                    anchors.verticalCenter: parent.verticalCenter

                    Text {
                        id: schoolNameText
                        width: parent.width
                        text: "TRƯỜNG CAO ĐẲNG BÌNH THUẬN"
                        font.family: "PingFang SC, Microsoft YaHei UI, Segoe UI"
                        font.pixelSize: isSmallScreen ? 13 : 18
                        font.weight: Font.Bold
                        font.letterSpacing: 0.3
                        horizontalAlignment: Text.AlignLeft
                        elide: Text.ElideNone
                        wrapMode: Text.NoWrap
                        
                        // Màu sắc thay đổi
                        property var colors: ["#1565C0", "#0D47A1", "#1976D2", "#2196F3", "#0288D1", "#00838F", "#00695C", "#2E7D32", "#558B2F", "#F57C00", "#E64A19", "#C62828", "#AD1457", "#6A1B9A", "#4527A0"]
                        property int colorIndex: 0
                        color: colors[colorIndex]
                        
                        // Animation chuyển màu mượt
                        Behavior on color {
                            ColorAnimation { duration: 1000; easing.type: Easing.InOutQuad }
                        }
                        
                        // Timer đổi màu mỗi 2 giây
                        Timer {
                            interval: 2000  // 2 giây
                            running: true
                            repeat: true
                            triggeredOnStart: true  // Kích hoạt ngay khi start
                            onTriggered: {
                                schoolNameText.colorIndex = (schoolNameText.colorIndex + 1) % schoolNameText.colors.length
                            }
                        }
                    }
                    Text {
                        text: "Trợ lý AI thông minh"
                        font.family: "PingFang SC, Microsoft YaHei UI, Segoe UI"
                        font.pixelSize: isSmallScreen ? 9 : 12
                        color: "#78909C"
                        font.italic: true
                        visible: !isSmallScreen  // Ẩn trên màn nhỏ
                    }
                }
            }

            // Nút minimize/close ở góc phải - ẨN TRÊN MÀN NHỎ (fullscreen)
            Row {
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                spacing: 6
                z: 2
                visible: !hideWindowButtons  // Ẩn khi fullscreen trên màn nhỏ

                // 最小化
                Rectangle {
                    id: btnMin
                    width: 30; height: 30; radius: 6
                    color: btnMinMouse.pressed ? "#e5e6eb" : (btnMinMouse.containsMouse ? "#f2f3f5" : "transparent")
                    Text { 
                        anchors.centerIn: parent
                        text: "–"
                        font.pixelSize: 18
                        font.weight: Font.Medium
                        color: "#4e5969"
                    }
                    MouseArea {
                        id: btnMinMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.titleMinimize()
                    }
                }

                // 关闭
                Rectangle {
                    id: btnClose
                    width: 30; height: 30; radius: 6
                    color: btnCloseMouse.pressed ? "#f53f3f" : (btnCloseMouse.containsMouse ? "#ff7875" : "transparent")
                    Text { 
                        anchors.centerIn: parent
                        text: "×"
                        font.pixelSize: 18
                        font.weight: Font.Medium
                        color: btnCloseMouse.containsMouse ? "white" : "#86909c"
                    }
                    MouseArea {
                        id: btnCloseMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: root.titleClose()
                    }
                }
            }
        }

        // 状态卡片区域
        Rectangle {
            id: statusCard
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: isSmallScreen ? 6 : 12
                spacing: isSmallScreen ? 6 : 12

                // 状态标签
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: isSmallScreen ? 28 : 40
                    color: "#E3F2FD"
                    radius: isSmallScreen ? 6 : 10

                    Text {
                        anchors.centerIn: parent
                        text: displayModel ? displayModel.statusText : "Trạng thái: Chưa kết nối"
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: isSmallScreen ? 11 : 14
                        font.weight: Font.Bold
                        color: "#2196F3"
                    }
                }

                // 表情显示区域
                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.minimumHeight: isSmallScreen ? 50 : 80

                    // 动态加载表情：AnimatedImage 用于 GIF，Image 用于静态图，Text 用于 emoji
                    Loader {
                        id: emotionLoader
                        anchors.centerIn: parent
                        // Responsive size cho màn nhỏ
                        property real maxSize: isSmallScreen ? 
                            Math.max(Math.min(parent.width, parent.height) * 0.6, 40) :
                            Math.max(Math.min(parent.width, parent.height) * 0.7, 60)
                        width: maxSize
                        height: maxSize

                        sourceComponent: {
                            var path = displayModel ? displayModel.emotionPath : ""
                            if (!path || path.length === 0) {
                                return emojiComponent
                            }
                            if (path.indexOf(".gif") !== -1) {
                                return gifComponent
                            }
                            if (path.indexOf(".") !== -1) {
                                return imageComponent
                            }
                            return emojiComponent
                        }

                        // GIF 动图组件
                        Component {
                            id: gifComponent
                            AnimatedImage {
                                fillMode: Image.PreserveAspectCrop
                                source: displayModel ? displayModel.emotionPath : ""
                                playing: true
                                speed: 1.05
                                cache: true
                                clip: true
                                onStatusChanged: {
                                    if (status === Image.Error) {
                                        console.error("AnimatedImage error:", errorString, "src=", source)
                                    }
                                }
                            }
                        }

                        // 静态图片组件
                        Component {
                            id: imageComponent
                            Image {
                                fillMode: Image.PreserveAspectCrop
                                source: displayModel ? displayModel.emotionPath : ""
                                cache: true
                                clip: true
                                onStatusChanged: {
                                    if (status === Image.Error) {
                                        console.error("Image error:", errorString, "src=", source)
                                    }
                                }
                            }
                        }

                        // Emoji 文本组件
                        Component {
                            id: emojiComponent
                            Text {
                                text: displayModel ? displayModel.emotionPath : "😊"
                                font.pixelSize: isSmallScreen ? 50 : 80
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                        }
                    }
                }

                // TTS 文本显示区域
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: isSmallScreen ? 50 : 80
                    color: "transparent"

                    Text {
                        anchors.fill: parent
                        anchors.margins: isSmallScreen ? 6 : 12
                        text: displayModel ? displayModel.ttsText : "Sẵn sàng"
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: isSmallScreen ? 16 : 22
                        font.weight: Font.Medium
                        color: "#555555"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                        maximumLineCount: isSmallScreen ? 3 : 4
                        lineHeight: 1.4
                    }
                }
            }
        }

        // 按钮区域 - ẨN ĐI
        Rectangle {
            id: buttonArea
            Layout.fillWidth: true
            Layout.preferredHeight: 0
            color: "#f7f8fa"
            visible: false

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                anchors.bottomMargin: 10
                spacing: 6

                // Nút bắt đầu/dừng trò chuyện - 主色
                Button {
                    id: autoBtn
                    Layout.preferredWidth: 100
                    Layout.fillWidth: true
                    Layout.maximumWidth: 140
                    Layout.preferredHeight: 38
                    text: displayModel ? displayModel.buttonText : "Bắt đầu trò chuyện"

                    background: Rectangle {
                        color: autoBtn.pressed ? "#0e42d2" : (autoBtn.hovered ? "#4080ff" : "#165dff")
                        radius: 8
                        Behavior on color { ColorAnimation { duration: 120; easing.type: Easing.OutCubic } }
                    }

                    contentItem: Text {
                        text: autoBtn.text
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: 12
                        color: "white"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.autoButtonClicked()
                }

                // 打断对话 - 次要色
                Button {
                    id: abortBtn
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.maximumWidth: 120
                    Layout.preferredHeight: 38
                    text: "Ngắt cuộc trò chuyện"

                    background: Rectangle { color: abortBtn.pressed ? "#e5e6eb" : (abortBtn.hovered ? "#f2f3f5" : "#eceff3"); radius: 8 }
                    contentItem: Text {
                        text: abortBtn.text
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: 12
                        color: "#1d2129"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.abortButtonClicked()
                }

                // 输入 + 发送
                RowLayout {
                    Layout.fillWidth: true
                    Layout.minimumWidth: 120
                    Layout.preferredHeight: 38
                    spacing: 6

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 38
                        color: "white"
                        radius: 8
                        border.color: textInput.activeFocus ? "#165dff" : "#e5e6eb"
                        border.width: 1

                        TextInput {
                            id: textInput
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            anchors.rightMargin: 10
                            verticalAlignment: TextInput.AlignVCenter
                            font.family: "PingFang SC, Microsoft YaHei UI"
                            font.pixelSize: 12
                            color: "#333333"
                            selectByMouse: true
                            clip: true

                            // 占位符
                            Text { anchors.fill: parent; text: "Nhập văn bản..."; font: textInput.font; color: "#c9cdd4"; verticalAlignment: Text.AlignVCenter; visible: !textInput.text && !textInput.activeFocus }

                            Keys.onReturnPressed: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = "" } }
                        }
                    }

                    Button {
                        id: sendBtn
                        Layout.preferredWidth: 60
                        Layout.maximumWidth: 84
                        Layout.preferredHeight: 38
                        text: "Gửi"
                        background: Rectangle { color: sendBtn.pressed ? "#0e42d2" : (sendBtn.hovered ? "#4080ff" : "#165dff"); radius: 8 }
                        contentItem: Text {
                            text: sendBtn.text
                            font.family: "PingFang SC, Microsoft YaHei UI"
                            font.pixelSize: 12
                            color: "white"
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                        }
                        onClicked: { if (textInput.text.trim().length > 0) { root.sendButtonClicked(textInput.text); textInput.text = "" } }
                    }
                }

                // 设置（次要）
                Button {
                    id: settingsBtn
                    Layout.preferredWidth: 80
                    Layout.fillWidth: true
                    Layout.maximumWidth: 120
                    Layout.preferredHeight: 38
                    text: "Cấu hình tham số"
                    background: Rectangle { color: settingsBtn.pressed ? "#e5e6eb" : (settingsBtn.hovered ? "#f2f3f5" : "#eceff3"); radius: 8 }
                    contentItem: Text {
                        text: settingsBtn.text
                        font.family: "PingFang SC, Microsoft YaHei UI"
                        font.pixelSize: 12
                        color: "#1d2129"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        elide: Text.ElideRight
                    }
                    onClicked: root.settingsButtonClicked()
                }
            }
        }
    }
}
