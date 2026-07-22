

all shortcut:
  mac
    1, vscode
    2, system shortcut
      com.apple.symbolichotkeys
    3, Rectangle
  ubuntu:
    1, vscode
    2, system shortcut
    3, dconf
      export setup:
        dconf dump /org/gnome/desktop/wm/keybindings/ > /home/wujie/Desktop/dconf_org_gnome_desktop_wm_keybindings.conf
        dconf dump / >  /home/wujie/Desktop/dconf_all.conf
      load the setup:
        dconf load / < my_shortcuts_backup.conf
  software:
    1, tmux


mac setup

  system setup and tools: Rectangle pro, alttab, Hammerspoon

  1，Rectangle: move application to other workspace by shortcut 
    使用破解版
    修改配置：
    # 移动窗口到下一个空间（对应系统快捷键 Shift+Option+→）
    defaults write com.knollsoft.Hookshot nextSpaceShortcut -string "{\"keyCode\":124,\"modifierFlags\":9043968}"
    # 移动窗口到上一个空间（对应系统快捷键 Shift+Option+←）
    defaults write com.knollsoft.Hookshot previousSpaceShortcut -string "{\"keyCode\":123,\"modifierFlags\":9043968}"

    可以设置窗口左侧右侧，可以设置类似super+z移动窗口的功能；

  2，alttab: only applications in current workspace;
    正常版本够用，不需要pro版本；

  3, codex in vscode:
      launchctl setenv ZENMUX_API_KEY "sk-ss-v1-b596e76183462defc385e48e7ffc9c429829dc8e9a884daa723487dcf09c8c4c"
      在每次重新登录后需要重新设置，需要彻底重启vscode，即先完全退出再启动；

    vscode远程到另一台设备，claude可以使用settings.json中的配置来使用；codex需要使用远程电脑的本体配置来使用；

  4, 在显示器间移动光标：
      安装 Hammerspoon（官网：https://www.hammerspoon.org/）
      编辑 ~/.hammerspoon/init.lua 文件,指定移动光标的快捷键
      not good: use BetterTouchTool, slow.

  4，通过 Hammerspoon 实现 altTab 的功能；

  5, Hidden Bar to manage the right-top status bar

  6, sshfs
    1, download
      brew install macfuse
      brew install gromgit/fuse/sshfs-mac
      # 重启 Mac，到 系统设置 > 隐私与安全性 允许内核扩展

    2, system support:
      Apple Silicon Mac 启用内核扩展步骤
      1. 关机
      点击  苹果菜单 > 关机，等待完全关机

      2. 进入恢复模式
      长按 触控 ID（电源按钮）不松手，直到屏幕显示 "正在载入启动选项…"

      3. 打开启动安全性实用工具
      选择 "选项" 齿轮图标，点击 "继续"
      输入你的 Mac 管理员密码
      顶部菜单栏点击 "实用工具" > "启动安全性实用工具"
      4. 修改安全策略
      选择你的启动磁盘（通常是 "Macintosh HD"）
      点击 "安全策略…"
      选择 "降低安全性"
      勾选 "允许用户管理来自被认可开发者的内核扩展"
      点击 "好"，输入密码确认
      5. 重启
      点击左上角  苹果菜单 > 重新启动

      6. 重启后允许 macFUSE
      进入系统后，去 系统设置 > 隐私与安全性，底部会有提示要求允许 macFUSE 的系统扩展，点击 "允许"，再重启一次即可。

