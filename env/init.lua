-- -- 移动光标到下一个显示器
-- hs.hotkey.bind({"cmd"}, ".", function()
--     local screen = hs.mouse.getCurrentScreen()
--     local nextScreen = screen:next()
--     local rect = nextScreen:fullFrame()
--     local center = hs.geometry.rectMidPoint(rect)
--     hs.mouse.absolutePosition(center)
-- end)

-- -- 移动光标到上一个显示器
-- hs.hotkey.bind({"cmd"}, ",", function()
--     local screen = hs.mouse.getCurrentScreen()
--     local previousScreen = screen:previous()
--     local rect = previousScreen:fullFrame()
--     local center = hs.geometry.rectMidPoint(rect)
--     hs.mouse.absolutePosition(center)
-- end)


-- -- 辅助函数：获取目标屏幕上最前面的可见窗口
-- local function get_frontmost_window_on_screen(target_screen)
--     -- orderedWindows()按Z轴顺序返回，第一个是最上层窗口
--     local windows = hs.window.orderedWindows()
--     for _, win in ipairs(windows) do
--         if win:screen():id() == target_screen:id() and win:isVisible() then
--             return win
--         end
--     end
--     return nil
-- end

-- -- 移动光标并聚焦窗口的通用函数
-- local function move_and_focus(target_screen)
--     -- 先聚焦目标屏幕上的窗口
--     local win = get_frontmost_window_on_screen(target_screen)
--     if win then
--         win:focus()
--         win:application():activate(true)
--         -- 移动光标到聚焦窗口的中心
--         local frame = win:frame()
--         local center = hs.geometry.rectMidPoint(frame)
--         hs.mouse.absolutePosition(center)
--     else
--         -- 没有窗口时移动光标到屏幕中心
--         local center = hs.geometry.rectMidPoint(target_screen:fullFrame())
--         hs.mouse.absolutePosition(center)
--     end
-- end

-- -- 移动光标到下一个显示器并聚焦窗口
-- hs.hotkey.bind({"cmd"}, ".", function()
--     local current_screen = hs.mouse.getCurrentScreen()
--     local next_screen = current_screen:next()
--     move_and_focus(next_screen)
-- end)

-- -- 移动光标到上一个显示器并聚焦窗口
-- hs.hotkey.bind({"cmd"}, ",", function()
--     local current_screen = hs.mouse.getCurrentScreen()
--     local previous_screen = current_screen:previous()
--     move_and_focus(previous_screen)
-- end)


-- -- ========== 右 Cmd + . / , 切换显示器 ==========

-- local function get_frontmost_window_on_screen(target_screen)
--     local windows = hs.window.orderedWindows()
--     for _, win in ipairs(windows) do
--         if win:screen():id() == target_screen:id() and win:isVisible() then
--             return win
--         end
--     end
--     return nil
-- end

-- local function move_and_focus(target_screen)
--     local win = get_frontmost_window_on_screen(target_screen)
--     if win then
--         win:focus()
--         win:application():activate(true)
--         local frame = win:frame()
--         local center = hs.geometry.rectMidPoint(frame)
--         hs.mouse.absolutePosition(center)
--     else
--         local center = hs.geometry.rectMidPoint(target_screen:fullFrame())
--         hs.mouse.absolutePosition(center)
--     end
-- end

-- -- 使用 LeftRightHotkey Spoon 区分左右 Cmd
-- hs.loadSpoon("LeftRightHotkey")

-- spoon.LeftRightHotkey:bind({"rCmd"}, ".", function()
--     move_and_focus(hs.mouse.getCurrentScreen():next())
-- end)

-- spoon.LeftRightHotkey:bind({"rCmd"}, ",", function()
--     move_and_focus(hs.mouse.getCurrentScreen():previous())
-- end)

-- spoon.LeftRightHotkey:start()






-- ========== 右 Cmd + . / , 切换显示器 ==========
-- 不依赖 LeftRightHotkey Spoon；用 eventtap 识别右 Cmd

local function get_frontmost_window_on_screen(target_screen)
    local windows = hs.window.orderedWindows()
    for _, win in ipairs(windows) do
        if win:screen():id() == target_screen:id() and win:isVisible() then
            return win
        end
    end
    return nil
end

local function move_and_focus(target_screen)
    local win = get_frontmost_window_on_screen(target_screen)
    if win then
        win:raise():focus()
        local frame = win:frame()
        local center = hs.geometry.rectMidPoint(frame)
        hs.mouse.absolutePosition(center)
    else
        local center = hs.geometry.rectMidPoint(target_screen:fullFrame())
        hs.mouse.absolutePosition(center)
    end
end

local rawFlagMasks = hs.eventtap.event.rawFlagMasks
local keycodes = hs.keycodes.map

local function isRightCmdOnly(flags)
    local raw = flags or 0
    local rCmd = (raw & rawFlagMasks.deviceRightCommand) > 0
    local lCmd = (raw & rawFlagMasks.deviceLeftCommand) > 0
    return rCmd and not lCmd
end

local rCmdScreenTap = hs.eventtap.new({hs.eventtap.event.types.keyDown}, function(e)
    local raw = e:getRawEventData().CGEventData.flags
    if not isRightCmdOnly(raw) then
        return false
    end

    local code = e:getKeyCode()
    if code == keycodes["."] then
        move_and_focus(hs.mouse.getCurrentScreen():next())
        return true
    elseif code == keycodes[","] then
        move_and_focus(hs.mouse.getCurrentScreen():previous())
        return true
    end
    return false
end)
rCmdScreenTap:start()


-- -- ========== Alt+Tab 窗口切换（当前空间，所有显示器）==========
-- local switcher = hs.window.switcher.new(
--     hs.window.filter.new():setCurrentSpace(true):setDefaultFilter{},
--     {
--         showTitles = true,
--         showThumbnails = true,
--         showSelectedThumbnail = false,
--         thumbnailSize = 128,
--         backgroundColor = {0.2, 0.2, 0.2, 0.85},
--         highlightColor = {0.4, 0.6, 0.9, 0.8},
--         fontName = ".AppleSystemUIFont",
--         textSize = 14,
--     }
-- )

-- local switcherTap = nil

-- local function startSwitcherNav()
--     if switcherTap then return end
--     switcherTap = hs.eventtap.new(
--         {hs.eventtap.event.types.keyDown, hs.eventtap.event.types.flagsChanged},
--         function(e)
--             if e:getType() == hs.eventtap.event.types.flagsChanged then
--                 if not e:getFlags().alt then
--                     switcherTap:stop()
--                     switcherTap = nil
--                 end
--                 return false
--             end
--             local code = e:getKeyCode()
--             if code == hs.keycodes.map["right"] then
--                 switcher:next()
--                 return true
--             elseif code == hs.keycodes.map["left"] then
--                 switcher:previous()
--                 return true
--             end
--             return false
--         end
--     )
--     switcherTap:start()
-- end

-- hs.hotkey.bind("alt", "tab", function()
--     startSwitcherNav()
--     switcher:next()
-- end)
-- hs.hotkey.bind({"alt", "shift"}, "tab", function()
--     startSwitcherNav()
--     switcher:previous()
-- end)
