from . import uiautomation as uia
from .languages import *
from .utils import *
from .color import *
from .errors import *
import datetime
import time
import os
import re
import win32api
import win32con



class WxParam:
    SYS_TEXT_HEIGHT = 33
    TIME_TEXT_HEIGHT = 34
    RECALL_TEXT_HEIGHT = 45
    CHAT_TEXT_HEIGHT = 52
    CHAT_IMG_HEIGHT = 117
    DEFALUT_SAVEPATH = os.path.join(os.getcwd(), 'wxauto文件')

class WeChatBase:
    def _lang(self, text, langtype='MAIN'):
        if langtype == 'MAIN':
            return MAIN_LANGUAGE[text][self.language]
        elif langtype == 'WARNING':
            return WARNING[text][self.language]

    def _split(self, MsgItem):
        """解析消息项，提取消息类型和内容

        Args:
            MsgItem: 消息项控件

        Returns:
            Message: 解析后的消息对象
        """
        # 防止递归调用导致栈溢出
        try:
            uia.SetGlobalSearchTimeout(0)
            MsgItemName = MsgItem.Name
            msg_id = ''.join([str(i) for i in MsgItem.GetRuntimeId()])

            # 系统消息
            if MsgItem.BoundingRectangle.height() == WxParam.SYS_TEXT_HEIGHT:
                Msg = ['SYS', MsgItemName, msg_id]
            # 时间消息
            elif MsgItem.BoundingRectangle.height() == WxParam.TIME_TEXT_HEIGHT:
                Msg = ['Time', MsgItemName, msg_id]
            # 撤回消息
            elif MsgItem.BoundingRectangle.height() == WxParam.RECALL_TEXT_HEIGHT:
                if '撤回' in MsgItemName:
                    Msg = ['Recall', MsgItemName, msg_id]
                else:
                    Msg = ['SYS', MsgItemName, msg_id]
            # 普通消息
            else:
                Index = 1
                try:
                    User = MsgItem.ButtonControl(foundIndex=Index)
                    # 查找非空名称的按钮控件
                    max_attempts = 5  # 限制尝试次数，防止无限循环
                    attempts = 0
                    while User.Name == '' and attempts < max_attempts:
                        Index += 1
                        attempts += 1
                        User = MsgItem.ButtonControl(foundIndex=Index)

                    # 如果找到了有效的用户名
                    if User.Name != '':
                        winrect = MsgItem.BoundingRectangle
                        mid = (winrect.left + winrect.right)/2

                        # 判断是好友消息还是自己的消息
                        if User.BoundingRectangle.left < mid:
                            # 尝试获取文本控件
                            has_text = False
                            try:
                                text_control = MsgItem.TextControl()
                                has_text = text_control.Exists(0.1)
                            except:
                                has_text = False

                            if has_text and text_control.BoundingRectangle.top < User.BoundingRectangle.top:
                                name = (User.Name, text_control.Name)
                            else:
                                name = (User.Name, User.Name)
                        else:
                            name = 'Self'

                        Msg = [name, MsgItemName, msg_id]
                    else:
                        # 如果没有找到有效的用户名，当作系统消息处理
                        Msg = ['SYS', MsgItemName, msg_id]
                except:
                    # 出现异常时，当作系统消息处理
                    Msg = ['SYS', MsgItemName, msg_id]

            uia.SetGlobalSearchTimeout(10.0)
            # 使用消息类型映射创建消息对象
            return message_types.get(Msg[0], FriendMessage)(Msg, MsgItem, self)
        except Exception as e:
            # 出现异常时，返回一个简单的系统消息对象
            uia.SetGlobalSearchTimeout(10.0)
            import traceback
            print(f"解析消息时出错: {str(e)}")
            traceback.print_exc()
            return SysMessage(['SYS', f'解析消息出错: {str(e)}', '0'], MsgItem, self)

    def _getmsgs(self, msgitems, savepic=False, savefile=False, savevoice=False):
        """解析消息项列表，提取消息内容

        Args:
            msgitems: 消息项控件列表
            savepic: 是否保存图片
            savefile: 是否保存文件
            savevoice: 是否保存语音

        Returns:
            list: 解析后的消息列表
        """
        wxlog.debug(f"开始解析消息项，savepic={savepic}, savefile={savefile}, savevoice={savevoice}")

        # 首先关闭可能已经打开的图片查看窗口和保存对话框
        try:
            # 检查是否已经有保存对话框打开，如果有则关闭
            save_dialog = FindWindow(name='另存为...')
            if save_dialog:
                wxlog.debug("检测到另存为对话框已打开，尝试使用Esc键关闭")
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)

            # 检查是否已经有图片查看窗口打开，如果有则关闭
            img_window = FindWindow(classname='ImagePreviewWnd')
            if img_window:
                wxlog.debug("检测到图片查看窗口已打开，尝试使用Esc键关闭")
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)

                # 如果Esc键没有关闭窗口，尝试使用Alt+F4
                img_window = FindWindow(classname='ImagePreviewWnd')
                if img_window:
                    wxlog.debug("窗口仍然存在，尝试使用Alt+F4关闭")
                    # 模拟按下Alt+F4
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                    win32api.keybd_event(win32con.VK_F4, 0, 0, 0)    # F4键按下
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_F4, 0, win32con.KEYEVENTF_KEYUP, 0)  # F4键释放
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
                    time.sleep(0.5)
        except Exception as e:
            wxlog.error(f"关闭已存在的窗口时出错: {str(e)}")

        # 解析消息项
        msgs = []
        for MsgItem in msgitems:
            if MsgItem.ControlTypeName == 'ListItemControl':
                msgs.append(self._split(MsgItem))

        msgtypes = [
            f"[{self._lang('图片')}]",
            f"[{self._lang('文件')}]",
            f"[{self._lang('语音')}]",
        ]

        # 如果没有需要处理的特殊消息类型，直接返回
        if not [i for i in msgs if i.content[:4] in msgtypes]:
            return msgs

        # 处理特殊消息类型
        for msg in msgs:
            if msg.type not in ('friend', 'self'):
                continue

            try:
                # 在处理每条消息前，确保没有图片查看窗口或保存对话框打开
                self._ensure_no_windows_open()

                if msg.content.startswith(f"[{self._lang('图片')}]") and savepic:
                    wxlog.debug(f"处理图片消息: {msg.content}")
                    imgpath = self._download_pic(msg.control)
                    if imgpath:
                        wxlog.debug(f"图片已保存到: {imgpath}")
                        msg.content = imgpath
                    else:
                        wxlog.warning(f"图片保存失败，保持原始内容: {msg.content}")

                    # 在处理完图片消息后，再次确保没有窗口打开
                    self._ensure_no_windows_open()

                elif msg.content.startswith(f"[{self._lang('文件')}]") and savefile:
                    wxlog.debug(f"处理文件消息: {msg.content}")
                    filepath = self._download_file(msg.control)
                    if filepath:
                        wxlog.debug(f"文件已保存到: {filepath}")
                        msg.content = filepath
                    else:
                        wxlog.warning(f"文件保存失败，保持原始内容: {msg.content}")

                elif msg.content.startswith(f"[{self._lang('语音')}]") and savevoice:
                    wxlog.debug(f"处理语音消息: {msg.content}")
                    voice_text = self._get_voice_text(msg.control)
                    if voice_text:
                        wxlog.debug(f"语音已转换为文本: {voice_text}")
                        msg.content = voice_text
                    else:
                        wxlog.warning(f"语音转换失败，保持原始内容: {msg.content}")

                # 更新消息信息
                msg.info[1] = msg.content

            except Exception as e:
                wxlog.error(f"处理消息时出错: {str(e)}")
                import traceback
                wxlog.error(traceback.format_exc())

        return msgs

    def _download_pic(self, msgitem):
        """下载图片

        Args:
            msgitem: 消息项控件

        Returns:
            str: 图片保存路径，如果保存失败则返回None
        """
        wxlog.debug("开始下载图片")

        # 检查是否已经有保存对话框打开，如果有则关闭
        try:
            save_dialog = FindWindow(name='另存为...')
            if save_dialog:
                wxlog.debug("检测到另存为对话框已打开，尝试使用Esc键关闭")
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)
        except Exception as e:
            wxlog.error(f"关闭已存在的保存对话框时出错: {str(e)}")

        # 检查是否已经有图片查看窗口打开，如果有则关闭
        try:
            img_window = FindWindow(classname='ImagePreviewWnd')
            if img_window:
                wxlog.debug("检测到图片查看窗口已打开，尝试使用Esc键关闭")
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)

                # 如果Esc键没有关闭窗口，尝试使用Alt+F4
                img_window = FindWindow(classname='ImagePreviewWnd')
                if img_window:
                    wxlog.debug("窗口仍然存在，尝试使用Alt+F4关闭")
                    # 模拟按下Alt+F4
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                    win32api.keybd_event(win32con.VK_F4, 0, 0, 0)    # F4键按下
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_F4, 0, win32con.KEYEVENTF_KEYUP, 0)  # F4键释放
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
                    time.sleep(0.5)
        except Exception as e:
            wxlog.error(f"关闭已存在的图片查看窗口时出错: {str(e)}")

        try:
            # 确保窗口在前台
            self._show()

            # 查找图片控件
            imgcontrol = msgitem.ButtonControl(Name='')
            if not imgcontrol.Exists(0.5):
                wxlog.warning("未找到图片控件")
                return None

            # 滚动到图片控件位置
            RollIntoView(self.C_MsgList, imgcontrol)

            # 点击图片控件
            wxlog.debug("点击图片控件")
            imgcontrol.Click(simulateMove=False)

            # 等待图片查看窗口出现
            t0 = time.time()
            img_window = None
            while time.time() - t0 < 5:  # 最多等待5秒
                img_window = FindWindow(classname='ImagePreviewWnd')
                if img_window:
                    break
                time.sleep(0.1)

            if not img_window:
                wxlog.warning("图片查看窗口未出现")
                return None

            # 创建图片对象并保存
            wxlog.debug("创建WeChatImage对象")
            imgobj = WeChatImage()

            # 保存图片
            wxlog.debug(f"保存图片，默认路径: {WxParam.DEFALUT_SAVEPATH}")

            # 生成唯一的文件名（不带扩展名）
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            save_path = os.path.join(WxParam.DEFALUT_SAVEPATH, f"微信图片_{timestamp}")

            # 保存图片
            savepath = imgobj.Save(save_path)
            wxlog.debug(f"图片已保存到: {savepath}")

            # 关闭图片查看窗口
            wxlog.debug("关闭图片查看窗口")
            imgobj.Close()

            # 确保图片查看窗口已经完全关闭
            t0 = time.time()
            while time.time() - t0 < 5:  # 最多等待5秒
                if not FindWindow(classname='ImagePreviewWnd'):
                    wxlog.debug("图片查看窗口已完全关闭")
                    break
                time.sleep(0.1)

            # 确保保存对话框已经完全关闭
            t0 = time.time()
            while time.time() - t0 < 5:  # 最多等待5秒
                if not FindWindow(name='另存为...'):
                    wxlog.debug("保存对话框已完全关闭")
                    break
                time.sleep(0.1)

            # 如果窗口仍然存在，发出警告
            if FindWindow(classname='ImagePreviewWnd'):
                wxlog.warning("图片查看窗口仍然存在，可能会导致下一次操作出现问题")

            if FindWindow(name='另存为...'):
                wxlog.warning("保存对话框仍然存在，可能会导致下一次操作出现问题")

            # 验证文件是否存在
            if os.path.exists(savepath):
                wxlog.debug(f"文件存在性验证通过: {savepath}")
            else:
                # 尝试查找实际保存的文件
                dir_name = os.path.dirname(save_path)
                if os.path.exists(dir_name):
                    for filename in os.listdir(dir_name):
                        # 检查文件是否是最近创建的（10秒内）
                        file_path = os.path.join(dir_name, filename)
                        if not os.path.isfile(file_path):
                            continue

                        file_time = os.path.getmtime(file_path)
                        if time.time() - file_time > 10:  # 只考虑10秒内创建的文件
                            continue

                        # 检查文件名是否包含时间戳
                        if timestamp in filename:
                            savepath = file_path
                            wxlog.debug(f"找到匹配时间戳的文件: {savepath}")
                            break

                if not os.path.exists(savepath):
                    wxlog.warning(f"文件不存在: {savepath}")

            return savepath

        except Exception as e:
            wxlog.error(f"下载图片时出错: {str(e)}")
            import traceback
            wxlog.error(traceback.format_exc())
            return None

    def _download_file(self, msgitem):
        # msgitems = self.C_MsgList.GetChildren()
        # msgs = []
        # for MsgItem in msgitems:
        #     msgs.append(self._split(MsgItem))

        filecontrol = msgitem.ButtonControl(Name='')
        if not filecontrol.Exists(0.5):
            return None
        RollIntoView(self.C_MsgList, filecontrol)
        filecontrol.RightClick(simulateMove=False)
        # paths = list()
        menu = self.UiaAPI.MenuControl(ClassName='CMenuWnd')
        options = [i for i in menu.ListControl().GetChildren() if i.ControlTypeName == 'MenuItemControl']

        copy = [i for i in options if i.Name == '复制']
        if copy:
            copy[0].Click(simulateMove=False)
        else:
            filecontrol.RightClick(simulateMove=False)
            filecontrol.Click(simulateMove=False)
            filewin = self.UiaAPI.WindowControl(ClassName='MsgFileWnd')
            accept_button = filewin.ButtonControl(Name='接收文件')
            if accept_button.Exists(2):
                accept_button.Click(simulateMove=False)

            while True:
                try:
                    filecontrol = msgitem.ButtonControl(Name='')
                    filecontrol.RightClick(simulateMove=False)
                    menu = self.UiaAPI.MenuControl(ClassName='CMenuWnd')
                    options = [i for i in menu.ListControl().GetChildren() if i.ControlTypeName == 'MenuItemControl']
                    copy = [i for i in options if i.Name == '复制']
                    if copy:
                        copy[0].Click(simulateMove=False)
                        break
                    else:
                        filecontrol.RightClick(simulateMove=False)
                except:
                    pass
        filepath = ReadClipboardData().get('15')[0]
        savepath = os.path.join(WxParam.DEFALUT_SAVEPATH, os.path.split(filepath)[1])
        if not os.path.exists(WxParam.DEFALUT_SAVEPATH):
            os.makedirs(WxParam.DEFALUT_SAVEPATH)
        shutil.copyfile(filepath, savepath)
        return savepath

    def _ensure_no_windows_open(self):
        """确保没有图片查看窗口或保存对话框打开"""
        # 检查是否有图片查看窗口打开
        img_window = FindWindow(classname='ImagePreviewWnd')
        if img_window:
            wxlog.warning("检测到图片查看窗口已打开，尝试关闭")
            try:
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)

                # 如果Esc键没有关闭窗口，尝试使用Alt+F4
                img_window = FindWindow(classname='ImagePreviewWnd')
                if img_window:
                    wxlog.debug("窗口仍然存在，尝试使用Alt+F4关闭")
                    # 模拟按下Alt+F4
                    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                    win32api.keybd_event(win32con.VK_F4, 0, 0, 0)    # F4键按下
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_F4, 0, win32con.KEYEVENTF_KEYUP, 0)  # F4键释放
                    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放
                    time.sleep(0.5)
            except Exception as e:
                wxlog.error(f"关闭图片查看窗口时出错: {str(e)}")

        # 检查是否有保存对话框打开
        save_dialog = FindWindow(name='另存为...')
        if save_dialog:
            wxlog.warning("检测到保存对话框已打开，尝试关闭")
            try:
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.5)
            except Exception as e:
                wxlog.error(f"关闭保存对话框时出错: {str(e)}")

        # 最终确认所有窗口都已关闭
        if FindWindow(classname='ImagePreviewWnd'):
            wxlog.warning("图片查看窗口仍然存在，可能会导致下一次操作出现问题")

        if FindWindow(name='另存为...'):
            wxlog.warning("保存对话框仍然存在，可能会导致下一次操作出现问题")

    def _get_voice_text(self, msgitem):
        if msgitem.GetProgenyControl(8, 4):
            return msgitem.GetProgenyControl(8, 4).Name
        voicecontrol = msgitem.ButtonControl(Name='')
        if not voicecontrol.Exists(0.5):
            return None
        RollIntoView(self.C_MsgList, voicecontrol)
        msgitem.GetProgenyControl(7, 1).RightClick(simulateMove=False)
        menu = self.UiaAPI.MenuControl(ClassName='CMenuWnd')
        option = menu.MenuItemControl(Name="语音转文字")
        if not option.Exists(0.5):
            voicecontrol.Click(simulateMove=False)
            if not msgitem.GetProgenyControl(8, 4):
                return None
        else:
            option.Click(simulateMove=False)

        text = ''
        while True:
            if msgitem.GetProgenyControl(8, 4):
                if msgitem.GetProgenyControl(8, 4).Name == text:
                    return text
                text = msgitem.GetProgenyControl(8, 4).Name
            time.sleep(0.1)


class ChatWnd(WeChatBase):
    def __init__(self, who, language='cn'):
        self.who = who
        self.language = language
        self.usedmsgid = []
        self.UiaAPI = uia.WindowControl(searchDepth=1, ClassName='ChatWnd', Name=who)
        self.editbox = self.UiaAPI.EditControl()
        self.C_MsgList = self.UiaAPI.ListControl()
        self.GetAllMessage()

        self.savepic = False   # 该参数用于在自动监听的情况下是否自动保存聊天图片

    def __repr__(self) -> str:
        return f"<wxauto Chat Window at {hex(id(self))} for {self.who}>"

    def _show(self):
        self.HWND = FindWindow(name=self.who, classname='ChatWnd')
        win32gui.ShowWindow(self.HWND, 1)
        win32gui.SetWindowPos(self.HWND, -1, 0, 0, 0, 0, 3)
        win32gui.SetWindowPos(self.HWND, -2, 0, 0, 0, 0, 3)
        self.UiaAPI.SwitchToThisWindow()

    def AtAll(self, msg=None):
        """@所有人

        Args:
            msg (str, optional): 要发送的文本消息
        """
        wxlog.debug(f"@所有人：{self.who} --> {msg}")
        self._show()
        if not self.editbox.HasKeyboardFocus:
            self.editbox.Click(simulateMove=False)

        self.editbox.SendKeys('@')
        atwnd = self.UiaAPI.PaneControl(ClassName='ChatContactMenu')
        if atwnd.Exists(maxSearchSeconds=0.1):
            atwnd.ListItemControl(Name='所有人').Click(simulateMove=False)
            if msg:
                if not msg.startswith('\n'):
                    msg = '\n' + msg
                self.SendMsg(msg)
            else:
                self.editbox.SendKeys('{Enter}')

    def SendMsg(self, msg, at=None):
        """发送文本消息

        Args:
            msg (str): 要发送的文本消息
            at (str|list, optional): 要@的人，可以是一个人或多个人，格式为str或list，例如："张三"或["张三", "李四"]
        """
        wxlog.debug(f"发送消息：{self.who} --> {msg}")
        self._show()
        if not self.editbox.HasKeyboardFocus:
            self.editbox.Click(simulateMove=False)

        if at:
            if isinstance(at, str):
                at = [at]
            for i in at:
                self.editbox.SendKeys('@'+i)
                atwnd = self.UiaAPI.PaneControl(ClassName='ChatContactMenu')
                if atwnd.Exists(maxSearchSeconds=0.1):
                    atwnd.SendKeys('{ENTER}')
                    if msg and not msg.startswith('\n'):
                        msg = '\n' + msg

        t0 = time.time()
        while True:
            if time.time() - t0 > 10:
                raise TimeoutError(f'发送消息超时 --> {self.who} - {msg}')
            SetClipboardText(msg)
            self.editbox.SendKeys('{Ctrl}v')
            if self.editbox.GetValuePattern().Value:
                break
        self.editbox.SendKeys('{Enter}')

    def SendFiles(self, filepath):
        """向当前聊天窗口发送文件

        Args:
            filepath (str|list): 要复制文件的绝对路径

        Returns:
            bool: 是否成功发送文件
        """
        wxlog.debug(f"发送文件：{self.who} --> {filepath}")
        filelist = []
        if isinstance(filepath, str):
            if not os.path.exists(filepath):
                Warnings.lightred(f'未找到文件：{filepath}，无法成功发送', stacklevel=2)
                return False
            else:
                filelist.append(os.path.realpath(filepath))
        elif isinstance(filepath, (list, tuple, set)):
            for i in filepath:
                if os.path.exists(i):
                    filelist.append(i)
                else:
                    Warnings.lightred(f'未找到文件：{i}', stacklevel=2)
        else:
            Warnings.lightred(f'filepath参数格式错误：{type(filepath)}，应为str、list、tuple、set格式', stacklevel=2)
            return False

        if filelist:
            self._show()
            self.editbox.SendKeys('{Ctrl}a', waitTime=0)
            t0 = time.time()
            while True:
                if time.time() - t0 > 10:
                    raise TimeoutError(f'发送文件超时 --> {filelist}')
                SetClipboardFiles(filelist)
                time.sleep(0.2)
                self.editbox.SendKeys('{Ctrl}v')
                if self.editbox.GetValuePattern().Value:
                    break
            self.editbox.SendKeys('{Enter}')
            return True
        else:
            Warnings.lightred('所有文件都无法成功发送', stacklevel=2)
            return False

    def GetAllMessage(self, savepic=False, savefile=False, savevoice=False):
        '''获取当前窗口中加载的所有聊天记录

        Args:
            savepic (bool): 是否自动保存聊天图片
            savefile (bool): 是否自动保存聊天文件
            savevoice (bool): 是否自动保存语音转文字

        Returns:
            list: 聊天记录信息
        '''
        wxlog.debug(f"获取所有聊天记录：{self.who}")
        MsgItems = self.C_MsgList.GetChildren()
        msgs = self._getmsgs(MsgItems, savepic, savefile, savevoice)
        return msgs

    def GetNewMessage(self, savepic=False, savefile=False, savevoice=False):
        '''获取当前窗口中加载的新聊天记录

        Args:
            savepic (bool): 是否自动保存聊天图片
            savefile (bool): 是否自动保存聊天文件
            savevoice (bool): 是否自动保存语音转文字

        Returns:
            list: 新聊天记录信息
        '''
        wxlog.debug(f"获取新聊天记录：{self.who}")

        # 确保窗口在前台
        try:
            self._show()
            wxlog.debug(f"已激活聊天窗口到前台: {self.who}")
        except Exception as e:
            wxlog.error(f"激活聊天窗口失败: {str(e)}")
            # 抛出异常，让上层处理
            raise

        # 初始化usedmsgid（如果需要）
        if not self.usedmsgid:
            # 直接从MsgItems中提取ID，避免递归调用
            MsgItems = self.C_MsgList.GetChildren()
            self.usedmsgid = [''.join([str(i) for i in item.GetRuntimeId()]) for item in MsgItems if item.ControlTypeName == 'ListItemControl']
            return []

        # 获取当前所有消息项
        MsgItems = self.C_MsgList.GetChildren()

        # 直接从MsgItems中提取当前所有消息ID
        current_msgids = [''.join([str(i) for i in item.GetRuntimeId()]) for item in MsgItems if item.ControlTypeName == 'ListItemControl']

        # 找出新消息项
        NewMsgItems = [i for i in MsgItems if i.ControlTypeName == 'ListItemControl' and ''.join([str(i) for i in i.GetRuntimeId()]) not in self.usedmsgid]

        # 如果没有新消息，直接返回空列表
        if not NewMsgItems:
            return []

        # 处理新消息
        newmsgs = self._getmsgs(NewMsgItems, savepic, savefile, savevoice)

        # 更新已使用的消息ID列表
        self.usedmsgid = current_msgids

        return newmsgs


    def LoadMoreMessage(self):
        """加载当前聊天页面更多聊天信息

        Returns:
            bool: 是否成功加载更多聊天信息
        """
        wxlog.debug(f"加载更多聊天信息：{self.who}")
        self._show()
        loadmore = self.C_MsgList.GetFirstChildControl()
        loadmore_top = loadmore.BoundingRectangle.top
        top = self.C_MsgList.BoundingRectangle.top
        while True:
            if loadmore.BoundingRectangle.top > top or loadmore.Name == '':
                isload = True
                break
            else:
                self.C_MsgList.WheelUp(wheelTimes=10, waitTime=0.1)
                if loadmore.BoundingRectangle.top == loadmore_top:
                    isload = False
                    break
                else:
                    loadmore_top = loadmore.BoundingRectangle.top
        self.C_MsgList.WheelUp(wheelTimes=1, waitTime=0.1)
        return isload

    def GetGroupMembers(self):
        """获取当前聊天群成员

        Returns:
            list: 当前聊天群成员列表
        """
        wxlog.debug(f"获取当前聊天群成员：{self.who}")
        ele = self.UiaAPI.PaneControl(searchDepth=7, foundIndex=6).ButtonControl(Name='聊天信息')
        try:
            uia.SetGlobalSearchTimeout(1)
            rect = ele.BoundingRectangle
            Click(rect)
        except:
            return
        finally:
            uia.SetGlobalSearchTimeout(10)
        roominfoWnd = self.UiaAPI.WindowControl(ClassName='SessionChatRoomDetailWnd', searchDepth=1)
        more = roominfoWnd.ButtonControl(Name='查看更多', searchDepth=8)
        try:
            uia.SetGlobalSearchTimeout(1)
            rect = more.BoundingRectangle
            Click(rect)
        except:
            pass
        finally:
            uia.SetGlobalSearchTimeout(10)
        members = [i.Name for i in roominfoWnd.ListControl(Name='聊天成员').GetChildren()]
        while members[-1] in ['添加', '移出']:
            members = members[:-1]
        roominfoWnd.SendKeys('{Esc}')
        return members

class WeChatImage:
    def __init__(self, language='cn') -> None:
        self.language = language
        self.api = uia.WindowControl(ClassName='ImagePreviewWnd', searchDepth=1)
        MainControl1 = [i for i in self.api.GetChildren() if not i.ClassName][0]
        self.ToolsBox, self.PhotoBox = MainControl1.GetChildren()

        # tools按钮
        self.t_previous = self.ToolsBox.ButtonControl(Name=self._lang('上一张'))
        self.t_next = self.ToolsBox.ButtonControl(Name=self._lang('下一张'))
        self.t_zoom = self.ToolsBox.ButtonControl(Name=self._lang('放大'))
        self.t_translate = self.ToolsBox.ButtonControl(Name=self._lang('翻译'))
        self.t_ocr = self.ToolsBox.ButtonControl(Name=self._lang('提取文字'))
        self.t_save = self.ToolsBox.ButtonControl(Name=self._lang('另存为...'))
        self.t_qrcode = self.ToolsBox.ButtonControl(Name=self._lang('识别图中二维码'))

    def __repr__(self) -> str:
        return f"<wxauto WeChat Image at {hex(id(self))}>"

    def _lang(self, text):
        return IMAGE_LANGUAGE[text][self.language]

    def _show(self):
        HWND = FindWindow(classname='ImagePreviewWnd')
        win32gui.ShowWindow(HWND, 1)
        self.api.SwitchToThisWindow()

    def OCR(self):
        result = ''
        ctrls = self.PhotoBox.GetChildren()
        if len(ctrls) == 2:
            self.t_ocr.Click(simulateMove=False)
        ctrls = self.PhotoBox.GetChildren()
        if len(ctrls) != 3:
            Warnings.lightred('获取文字识别失败', stacklevel=2)
        else:
            TranslateControl = ctrls[-1]
            result = TranslateControl.TextControl().Name
        return result


    def Save(self, savepath='', timeout=10):
        """保存图片

        Args:
            savepath (str): 绝对路径，包括文件名和后缀，例如："D:/Images/微信图片_xxxxxx.jpg"
            （如果不填，则默认为当前脚本文件夹下，新建一个“微信图片”的文件夹，保存在该文件夹内）

        Returns:
            str: 文件保存路径，即savepath
        """

        # 记录开始时间，用于调试
        start_time = time.time()

        # 确保保存路径有效
        if not savepath:
            savepath = os.path.join(WxParam.DEFALUT_SAVEPATH, f"微信图片_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg")

        # 处理文件路径，分离目录和文件名
        save_dir = os.path.dirname(savepath)
        file_name = os.path.basename(savepath)
        file_name_without_ext = os.path.splitext(file_name)[0]  # 去掉扩展名

        # 确保目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # 记录保存路径，用于调试
        wxlog.debug(f"原始图片保存路径: {savepath}")
        wxlog.debug(f"保存目录: {save_dir}")
        wxlog.debug(f"文件名(无扩展名): {file_name_without_ext}")
        wxlog.debug(f"保存目录是否存在: {os.path.exists(save_dir)}")

        # 检查是否已经有保存对话框打开
        save_dialog = FindWindow(name='另存为...')
        if save_dialog:
            wxlog.debug("检测到另存为对话框已打开，直接使用")
        else:
            # 点击保存按钮
            if self.t_zoom.Exists(maxSearchSeconds=5):
                wxlog.debug("点击另存为按钮")
                self.t_save.Click(simulateMove=False)
            else:
                raise TimeoutError('下载超时')
        t0 = time.time()
        while True:
            if time.time() - t0 > timeout:
                raise TimeoutError('下载超时')
            handle = FindWindow(name='另存为...')
            if handle:
                break
        t0 = time.time()
        while True:
            if time.time() - t0 > timeout:
                raise TimeoutError('下载超时')
            try:
                edithandle = [i for i in GetAllWindowExs(handle) if i[1] == 'Edit' and i[-1]][0][0]
                savehandle = FindWinEx(handle, classname='Button', name='保存(&S)')[0]
                if edithandle and savehandle:
                    break
            except:
                pass
        # 准备保存路径 - 使用不带扩展名的文件名
        save_path_for_dialog = os.path.join(save_dir, file_name_without_ext)
        wxlog.debug(f"对话框使用的保存路径: {save_path_for_dialog}")

        # 清空编辑框
        win32gui.SendMessage(edithandle, win32con.WM_SETTEXT, 0, "")
        time.sleep(0.1)

        # 设置保存路径
        wxlog.debug(f"设置保存路径: {save_path_for_dialog}")
        win32gui.SendMessage(edithandle, win32con.WM_SETTEXT, 0, str(save_path_for_dialog))
        time.sleep(0.2)

        # 获取编辑框当前文本，检查是否设置成功
        try:
            buffer_size = 1024
            buffer = win32gui.PyMakeBuffer(buffer_size)
            length = win32gui.SendMessage(edithandle, win32con.WM_GETTEXT, buffer_size, buffer)

            # 正确处理memoryview对象
            address, _ = win32gui.PyGetBufferAddressAndLen(buffer)
            if length > 0:
                current_text = win32gui.PyGetString(address, length)
            else:
                current_text = ""

            wxlog.debug(f"编辑框当前文本: {current_text}")
        except Exception as e:
            wxlog.error(f"获取编辑框文本时出错: {str(e)}")
            current_text = ""

        # 如果设置失败，尝试使用剪贴板
        if not current_text or save_path_for_dialog not in current_text:
            wxlog.warning("通过SendMessage设置路径失败，尝试使用剪贴板")
            # 保存原始剪贴板内容
            import win32clipboard
            win32clipboard.OpenClipboard()
            try:
                original_clipboard = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT) if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT) else None
            except:
                original_clipboard = None
            win32clipboard.CloseClipboard()

            # 设置剪贴板为保存路径
            SetClipboardText(save_path_for_dialog)

            # 选择所有文本并粘贴
            win32gui.SendMessage(edithandle, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
            win32gui.SendMessage(edithandle, win32con.WM_KEYDOWN, ord('A'), 0)
            win32gui.SendMessage(edithandle, win32con.WM_KEYUP, ord('A'), 0)
            win32gui.SendMessage(edithandle, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
            time.sleep(0.1)

            win32gui.SendMessage(edithandle, win32con.WM_KEYDOWN, win32con.VK_CONTROL, 0)
            win32gui.SendMessage(edithandle, win32con.WM_KEYDOWN, ord('V'), 0)
            win32gui.SendMessage(edithandle, win32con.WM_KEYUP, ord('V'), 0)
            win32gui.SendMessage(edithandle, win32con.WM_KEYUP, win32con.VK_CONTROL, 0)
            time.sleep(0.2)

            # 恢复原始剪贴板内容
            if original_clipboard:
                SetClipboardText(original_clipboard)

        # 点击保存按钮
        wxlog.debug("点击保存按钮")

        # 使用SendMessage点击保存按钮
        try:
            wxlog.debug("使用SendMessage点击保存按钮")
            win32gui.SendMessage(savehandle, win32con.BM_CLICK, 0, 0)

            # 等待一段时间，确保文件有足够的时间保存
            time.sleep(1.0)

            # 检查文件是否已保存
            test_path = save_path_for_dialog + ".jpg"
            if os.path.exists(test_path):
                wxlog.debug("文件已成功保存")
            else:
                # 如果文件未保存，尝试使用模拟按键
                wxlog.debug("文件未保存，尝试使用模拟按键")
                try:
                    # 模拟按下回车键
                    win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
                    time.sleep(0.1)
                    win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)
                    time.sleep(0.5)
                except Exception as e:
                    wxlog.error(f"模拟按键失败: {str(e)}")
        except Exception as e:
            wxlog.error(f"点击保存按钮失败: {str(e)}")

        # 再等待一段时间，确保文件已保存
        time.sleep(0.5)

        # 尝试查找实际保存的文件
        actual_file = None
        possible_extensions = ['.jpg', '.png', '.gif', '.bmp']

        # 获取保存目录
        dir_name = os.path.dirname(save_path_for_dialog)

        # 检查目录中的所有文件，查找匹配的文件名（不考虑时间戳部分）
        if os.path.exists(dir_name):
            for filename in os.listdir(dir_name):
                # 检查文件是否是最近创建的（10秒内）
                file_path = os.path.join(dir_name, filename)
                if not os.path.isfile(file_path):
                    continue

                file_time = os.path.getmtime(file_path)
                if time.time() - file_time > 10:  # 只考虑10秒内创建的文件
                    continue

                # 检查文件名是否匹配基本模式（微信图片_）
                if "微信图片_" in filename:
                    # 检查文件扩展名
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in ['.jpg', '.png', '.gif', '.bmp']:
                        actual_file = file_path
                        wxlog.debug(f"找到实际保存的文件: {actual_file}")
                        break

        # 如果上面的方法没找到，尝试直接检查可能的扩展名
        if not actual_file:
            for ext in possible_extensions:
                test_path = save_path_for_dialog + ext
                if os.path.exists(test_path):
                    actual_file = test_path
                    wxlog.debug(f"找到实际保存的文件: {actual_file}")
                    break

        # 如果找到了实际文件，返回实际路径，否则返回原始路径
        if actual_file:
            wxlog.debug(f"保存图片总耗时: {time.time() - start_time:.2f}秒")

            # 关闭可能仍然打开的保存对话框
            try:
                save_dialog = FindWindow(name='另存为...')
                if save_dialog:
                    wxlog.debug("检测到另存为对话框仍然打开，尝试关闭")
                    win32gui.PostMessage(save_dialog, win32con.WM_CLOSE, 0, 0)
            except Exception as e:
                wxlog.error(f"尝试关闭另存为对话框时出错: {str(e)}")

            return actual_file
        else:
            wxlog.warning(f"未找到实际保存的文件，返回原始路径: {savepath}")
            return savepath

    def Previous(self):
        """上一张"""
        if self.t_previous.IsKeyboardFocusable:
            self._show()
            self.t_previous.Click(simulateMove=False)
            return True
        else:
            Warnings.lightred('上一张按钮不可用', stacklevel=2)
            return False

    def Next(self, warning=True):
        """下一张"""
        if self.t_next.IsKeyboardFocusable:
            self._show()
            self.t_next.Click(simulateMove=False)
            return True
        else:
            if warning:
                Warnings.lightred('已经是最新的图片了', stacklevel=2)
            return False

    def Close(self):
        """关闭图片查看窗口"""
        try:
            # 确保窗口在前台
            self._show()

            # 发送Esc键关闭窗口
            wxlog.debug("使用Esc键关闭图片查看窗口")
            self.api.SendKeys('{Esc}')

            # 等待窗口关闭，最多等待3秒
            t0 = time.time()
            while time.time() - t0 < 3:
                if not FindWindow(classname='ImagePreviewWnd'):
                    wxlog.debug("图片查看窗口已关闭")
                    break
                time.sleep(0.1)

            # 如果窗口仍然存在，尝试使用Alt+F4关闭
            if FindWindow(classname='ImagePreviewWnd'):
                wxlog.debug("窗口仍然存在，尝试使用Alt+F4关闭")
                # 模拟按下Alt+F4
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)  # Alt键按下
                win32api.keybd_event(win32con.VK_F4, 0, 0, 0)    # F4键按下
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_F4, 0, win32con.KEYEVENTF_KEYUP, 0)  # F4键释放
                win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # Alt键释放

                # 再次等待窗口关闭，最多等待3秒
                t0 = time.time()
                while time.time() - t0 < 3:
                    if not FindWindow(classname='ImagePreviewWnd'):
                        wxlog.debug("图片查看窗口已关闭")
                        break
                    time.sleep(0.1)

            # 关闭可能仍然打开的保存对话框
            save_dialog = FindWindow(name='另存为...')
            if save_dialog:
                wxlog.debug("检测到另存为对话框仍然打开，尝试使用Esc键关闭")
                # 模拟按下Esc键
                win32api.keybd_event(win32con.VK_ESCAPE, 0, 0, 0)
                time.sleep(0.1)
                win32api.keybd_event(win32con.VK_ESCAPE, 0, win32con.KEYEVENTF_KEYUP, 0)

                # 等待保存对话框关闭，最多等待3秒
                t0 = time.time()
                while time.time() - t0 < 3:
                    if not FindWindow(name='另存为...'):
                        wxlog.debug("保存对话框已关闭")
                        break
                    time.sleep(0.1)

            # 最终确认所有窗口都已关闭
            if FindWindow(classname='ImagePreviewWnd'):
                wxlog.warning("图片查看窗口仍然存在，可能需要手动关闭")

            if FindWindow(name='另存为...'):
                wxlog.warning("保存对话框仍然存在，可能需要手动关闭")

        except Exception as e:
            wxlog.error(f"关闭图片查看窗口时出错: {str(e)}")
            import traceback
            wxlog.error(traceback.format_exc())

class TextElement:
    def __init__(self, ele, wx) -> None:
        self._wx = wx
        chatname = wx.CurrentChat()
        self.ele = ele
        self.sender = ele.ButtonControl(foundIndex=1, searchDepth=2)
        _ = ele.GetFirstChildControl().GetChildren()[1].GetChildren()
        if len(_) == 1:
            self.content = _[0].TextControl().Name
            self.chattype = 'friend'
            self.chatname = chatname
        else:
            self.sender_remark = _[0].TextControl().Name
            self.content = _[1].TextControl().Name
            self.chattype = 'group'
            numtext = re.findall(' \(\d+\)', chatname)[-1]
            self.chatname = chatname[:-len(numtext)]

        self.info = {
            'sender': self.sender.Name,
            'content': self.content,
            'chatname': self.chatname,
            'chattype': self.chattype,
            'sender_remark': self.sender_remark if hasattr(self, 'sender_remark') else ''
        }

    def __repr__(self) -> str:
        return f"<wxauto Text Element at {hex(id(self))} ({self.sender.Name}: {self.content})>"

class NewFriendsElement:
    def __init__(self, ele, wx):
        self._wx = wx
        self.ele = ele
        self.name = self.ele.Name
        self.msg = self.ele.GetFirstChildControl().PaneControl(SearchDepth=1).GetChildren()[-1].TextControl().Name
        self.ele.GetChildren()[-1]
        self.Status = self.ele.GetFirstChildControl().GetChildren()[-1]
        self.acceptable = False
        if isinstance(self.Status, uia.ButtonControl):
            self.acceptable = True

    def __repr__(self) -> str:
        return f"<wxauto New Friends Element at {hex(id(self))} ({self.name}: {self.msg})>"

    def Accept(self, remark=None, tags=None):
        """接受好友请求

        Args:
            remark (str, optional): 备注名
            tags (list, optional): 标签列表
        """
        wxlog.debug(f"接受好友请求：{self.name}  备注：{remark} 标签：{tags}")
        self._wx._show()
        self.Status.Click(simulateMove=False)
        NewFriendsWnd = self._wx.UiaAPI.WindowControl(ClassName='WeUIDialog')

        if remark:
            remarkedit = NewFriendsWnd.TextControl(Name='备注名').GetParentControl().EditControl()
            remarkedit.Click(simulateMove=False)
            remarkedit.SendKeys('{Ctrl}a', waitTime=0)
            remarkedit.SendKeys(remark)

        if tags:
            tagedit = NewFriendsWnd.TextControl(Name='标签').GetParentControl().EditControl()
            for tag in tags:
                tagedit.Click(simulateMove=False)
                tagedit.SendKeys(tag)
                NewFriendsWnd.PaneControl(ClassName='DropdownWindow').TextControl().Click(simulateMove=False)

        NewFriendsWnd.ButtonControl(Name='确定').Click(simulateMove=False)


class ContactWnd:
    def __init__(self):
        self.UiaAPI = uia.WindowControl(ClassName='ContactManagerWindow', searchDepth=1)
        self.Sidebar, _, self.ContactBox = self.UiaAPI.PaneControl(ClassName='', searchDepth=3, foundIndex=3).GetChildren()

    def __repr__(self) -> str:
        return f"<wxauto Contact Window at {hex(id(self))}>"

    def _show(self):
        self.HWND = FindWindow(classname='ContactManagerWindow')
        win32gui.ShowWindow(self.HWND, 1)
        win32gui.SetWindowPos(self.HWND, -1, 0, 0, 0, 0, 3)
        win32gui.SetWindowPos(self.HWND, -2, 0, 0, 0, 0, 3)
        self.UiaAPI.SwitchToThisWindow()

    def GetFriendNum(self):
        """获取好友人数"""
        wxlog.debug('获取好友人数')
        numText = self.Sidebar.PaneControl(Name='全部').TextControl(foundIndex=2).Name
        return int(re.findall('\d+', numText)[0])

    def Search(self, keyword):
        """搜索好友

        Args:
            keyword (str): 搜索关键词
        """
        wxlog.debug(f"搜索好友：{keyword}")
        self.ContactBox.EditControl(Name="搜索").Click(simulateMove=False)
        self.ContactBox.SendKeys('{Ctrl}{A}')
        self.ContactBox.SendKeys(keyword)

    def GetAllFriends(self):
        """获取好友列表"""
        wxlog.debug("获取好友列表")
        self._show()
        contacts_list = []
        while True:
            contact_ele_list = self.ContactBox.ListControl().GetChildren()
            for ele in contact_ele_list:
                contacts_info = {
                    'nickname': ele.TextControl().Name,
                    'remark': ele.ButtonControl(foundIndex=2).Name,
                    'tags': ele.ButtonControl(foundIndex=3).Name.split('，'),
                }
                if contacts_info.get('remark') in ('添加备注', ''):
                    contacts_info['remark'] = None
                if contacts_info.get('tags') in (['添加标签'], ['']):
                    contacts_info['tags'] = None
                if contacts_info not in contacts_list:
                    contacts_list.append(contacts_info)
            bottom = self.ContactBox.ListControl().GetChildren()[-1].BoundingRectangle.top
            self.ContactBox.WheelDown(wheelTimes=5, waitTime=0.1)
            if bottom == self.ContactBox.ListControl().GetChildren()[-1].BoundingRectangle.top:
                return contacts_list

    def Close(self):
        """关闭联系人窗口"""
        wxlog.debug('关闭联系人窗口')
        self._show()
        self.UiaAPI.SendKeys('{Esc}')


class ContactElement:
    def __init__(self, ele):
        self.element = ele
        self.nickname = ele.TextControl().Name
        self.remark = ele.ButtonControl(foundIndex=2).Name
        self.tags = ele.ButtonControl(foundIndex=3).Name.split('，')

    def __repr__(self) -> str:
        return f"<wxauto Contact Element at {hex(id(self))} ({self.nickname}: {self.remark})>"

    def EditRemark(self, remark: str):
        """修改好友备注名

        Args:
            remark (str): 新备注名
        """
        wxlog.debug(f"修改好友备注名：{self.nickname} --> {remark}")
        self.element.ButtonControl(foundIndex=2).Click(simulateMove=False)
        self.element.SendKeys('{Ctrl}a')
        self.element.SendKeys(remark)
        self.element.SendKeys('{Enter}')


class SessionElement:
    def __init__(self, item):
        self.name = item.GetProgenyControl(4, control_type='TextControl').Name\
            if item.GetProgenyControl(4, control_type='TextControl') else None
        self.time = item.GetProgenyControl(4, 1, control_type='TextControl').Name\
            if item.GetProgenyControl(4, 1, control_type='TextControl') else None
        self.content = item.GetProgenyControl(4, 2, control_type='TextControl').Name\
            if item.GetProgenyControl(4, 2, control_type='TextControl') else None
        self.isnew = item.GetProgenyControl(2, 2) is not None
        wxlog.debug(f"============== 【{self.name}】 ==============")
        wxlog.debug(f"最后一条消息时间: {self.time}")
        wxlog.debug(f"最后一条消息内容: {self.content}")
        wxlog.debug(f"是否有新消息: {self.isnew}")


class Message:
    type = 'message'

    def __getitem__(self, index):
        return self.info[index]

    def __str__(self):
        return self.content

    def __repr__(self):
        return str(self.info[:2])


class SysMessage(Message):
    type = 'sys'

    def __init__(self, info, control, wx):
        self.info = info
        self.control = control
        self.wx = wx
        self.sender = info[0]
        self.content = info[1]
        self.id = info[-1]
        wxlog.debug(f"【系统消息】{self.content}")

    # def __repr__(self):
    #     return f'<wxauto SysMessage at {hex(id(self))}>'


class TimeMessage(Message):
    type = 'time'

    def __init__(self, info, control, wx):
        self.info = info
        self.control = control
        self.wx = wx
        self.time = ParseWeChatTime(info[1])
        self.sender = info[0]
        self.content = info[1]
        self.id = info[-1]
        wxlog.debug(f"【时间消息】{self.time}")

    # def __repr__(self):
    #     return f'<wxauto TimeMessage at {hex(id(self))}>'


class RecallMessage(Message):
    type = 'recall'

    def __init__(self, info, control, wx):
        self.info = info
        self.control = control
        self.wx = wx
        self.sender = info[0]
        self.content = info[1]
        self.id = info[-1]
        wxlog.debug(f"【撤回消息】{self.content}")

    # def __repr__(self):
    #     return f'<wxauto RecallMessage at {hex(id(self))}>'


class SelfMessage(Message):
    type = 'self'

    def __init__(self, info, control, obj):
        self.info = info
        self.control = control
        self._winobj = obj
        self.sender = info[0]
        self.content = info[1]
        self.id = info[-1]
        self.chatbox = obj.ChatBox if hasattr(obj, 'ChatBox') else obj.UiaAPI
        wxlog.debug(f"【自己消息】{self.content}")

    # def __repr__(self):
    #     return f'<wxauto SelfMessage at {hex(id(self))}>'

    def quote(self, msg):
        """引用该消息

        Args:
            msg (str): 引用的消息内容

        Returns:
            bool: 是否成功引用
        """
        wxlog.debug(f'发送引用消息：{msg}  --> {self.sender} | {self.content}')
        self._winobj._show()
        headcontrol = [i for i in self.control.GetFirstChildControl().GetChildren() if i.ControlTypeName == 'ButtonControl'][0]
        RollIntoView(self.chatbox.ListControl(), headcontrol, equal=True)
        xbias = int(headcontrol.BoundingRectangle.width()*1.5)
        headcontrol.RightClick(x=-xbias, simulateMove=False)
        menu = self._winobj.UiaAPI.MenuControl(ClassName='CMenuWnd')
        quote_option = menu.MenuItemControl(Name="引用")
        if not quote_option.Exists(maxSearchSeconds=0.1):
            wxlog.debug('该消息当前状态无法引用')
            return False
        quote_option.Click(simulateMove=False)
        editbox = self.chatbox.EditControl(searchDepth=15)
        t0 = time.time()
        while True:
            if time.time() - t0 > 10:
                raise TimeoutError(f'发送消息超时 --> {msg}')
            SetClipboardText(msg)
            editbox.SendKeys('{Ctrl}v')
            if editbox.GetValuePattern().Value.replace('\r￼', ''):
                break
        editbox.SendKeys('{Enter}')
        return True

    def forward(self, friend):
        """转发该消息

        Args:
            friend (str): 转发给的好友昵称、备注或微信号

        Returns:
            bool: 是否成功转发
        """
        wxlog.debug(f'转发消息：{self.sender} --> {friend} | {self.content}')
        self._winobj._show()
        headcontrol = [i for i in self.control.GetFirstChildControl().GetChildren() if i.ControlTypeName == 'ButtonControl'][0]
        RollIntoView(self.chatbox.ListControl(), headcontrol, equal=True)
        xbias = int(headcontrol.BoundingRectangle.width()*1.5)
        headcontrol.RightClick(x=-xbias, simulateMove=False)
        menu = self._winobj.UiaAPI.MenuControl(ClassName='CMenuWnd')
        forward_option = menu.MenuItemControl(Name="转发...")
        if not forward_option.Exists(maxSearchSeconds=0.1):
            wxlog.debug('该消息当前状态无法转发')
            return False
        forward_option.Click(simulateMove=False)
        SetClipboardText(friend)
        contactwnd = self._winobj.UiaAPI.WindowControl(ClassName='SelectContactWnd')
        contactwnd.SendKeys('{Ctrl}a', waitTime=0)
        contactwnd.SendKeys('{Ctrl}v')
        checkbox = contactwnd.ListControl().CheckBoxControl()
        if checkbox.Exists(1):
            checkbox.Click(simulateMove=False)
            contactwnd.ButtonControl(Name='发送').Click(simulateMove=False)
            return True
        else:
            contactwnd.SendKeys('{Esc}')
            raise FriendNotFoundError(f'未找到好友：{friend}')

    def parse(self):
        """解析合并消息内容，当且仅当消息内容为合并转发的消息时有效"""
        wxlog.debug(f'解析合并消息内容：{self.sender} | {self.content}')
        self._winobj._show()
        headcontrol = [i for i in self.control.GetFirstChildControl().GetChildren() if i.ControlTypeName == 'ButtonControl'][0]
        RollIntoView(self.chatbox.ListControl(), headcontrol, equal=True)
        xbias = int(headcontrol.BoundingRectangle.width()*1.5)
        headcontrol.Click(x=-xbias, simulateMove=False)
        chatrecordwnd = uia.WindowControl(ClassName='ChatRecordWnd', searchDepth=1)
        msgitems = chatrecordwnd.ListControl().GetChildren()
        msgs = []
        for msgitem in msgitems:
            textcontrols = [i for i in GetAllControl(msgitem) if i.ControlTypeName == 'TextControl']
            who = textcontrols[0].Name
            time = textcontrols[1].Name
            try:
                content = textcontrols[2].Name
            except IndexError:
                content = ''
            msgs.append(([who, content, ParseWeChatTime(time)]))
        chatrecordwnd.SendKeys('{Esc}')
        return msgs

class FriendMessage(Message):
    type = 'friend'

    def __init__(self, info, control, obj):
        self.info = info
        self.control = control
        self._winobj = obj
        self.sender = info[0][0]
        self.sender_remark = info[0][1]
        self.content = info[1]
        self.id = info[-1]
        self.info[0] = info[0][0]
        self.chatbox = obj.ChatBox if hasattr(obj, 'ChatBox') else obj.UiaAPI
        if self.sender == self.sender_remark:
            wxlog.debug(f"【好友消息】{self.sender}: {self.content}")
        else:
            wxlog.debug(f"【好友消息】{self.sender}({self.sender_remark}): {self.content}")

    # def __repr__(self):
    #     return f'<wxauto FriendMessage at {hex(id(self))}>'

    def quote(self, msg):
        """引用该消息

        Args:
            msg (str): 引用的消息内容

        Returns:
            bool: 是否成功引用
        """
        wxlog.debug(f'发送引用消息：{msg}  --> {self.sender} | {self.content}')
        self._winobj._show()
        headcontrol = [i for i in self.control.GetFirstChildControl().GetChildren() if i.ControlTypeName == 'ButtonControl'][0]
        RollIntoView(self.chatbox.ListControl(), headcontrol, equal=True)
        xbias = int(headcontrol.BoundingRectangle.width()*1.5)
        headcontrol.RightClick(x=xbias, simulateMove=False)
        menu = self._winobj.UiaAPI.MenuControl(ClassName='CMenuWnd')
        quote_option = menu.MenuItemControl(Name="引用")
        if not quote_option.Exists(maxSearchSeconds=0.1):
            wxlog.debug('该消息当前状态无法引用')
            return False
        quote_option.Click(simulateMove=False)
        editbox = self.chatbox.EditControl(searchDepth=15)
        t0 = time.time()
        while True:
            if time.time() - t0 > 10:
                raise TimeoutError(f'发送消息超时 --> {msg}')
            SetClipboardText(msg)
            editbox.SendKeys('{Ctrl}v')
            if editbox.GetValuePattern().Value.replace('\r￼', ''):
                break
        editbox.SendKeys('{Enter}')
        return True

    def forward(self, friend):
        """转发该消息

        Args:
            friend (str): 转发给的好友昵称、备注或微信号

        Returns:
            bool: 是否成功转发
        """
        wxlog.debug(f'转发消息：{self.sender} --> {friend} | {self.content}')
        self._winobj._show()
        headcontrol = [i for i in self.control.GetFirstChildControl().GetChildren() if i.ControlTypeName == 'ButtonControl'][0]
        RollIntoView(self.chatbox.ListControl(), headcontrol, equal=True)
        xbias = int(headcontrol.BoundingRectangle.width()*1.5)
        headcontrol.RightClick(x=xbias, simulateMove=False)
        menu = self._winobj.UiaAPI.MenuControl(ClassName='CMenuWnd')
        forward_option = menu.MenuItemControl(Name="转发...")
        if not forward_option.Exists(maxSearchSeconds=0.1):
            wxlog.debug('该消息当前状态无法转发')
            return False
        forward_option.Click(simulateMove=False)
        SetClipboardText(friend)
        contactwnd = self._winobj.UiaAPI.WindowControl(ClassName='SelectContactWnd')
        contactwnd.SendKeys('{Ctrl}a', waitTime=0)
        contactwnd.SendKeys('{Ctrl}v')
        checkbox = contactwnd.ListControl().CheckBoxControl()
        if checkbox.Exists(1):
            checkbox.Click(simulateMove=False)
            contactwnd.ButtonControl(Name='发送').Click(simulateMove=False)
            return True
        else:
            contactwnd.SendKeys('{Esc}')
            raise FriendNotFoundError(f'未找到好友：{friend}')

    def parse(self):
        """解析合并消息内容，当且仅当消息内容为合并转发的消息时有效"""
        wxlog.debug(f'解析合并消息内容：{self.sender} | {self.content}')
        self._winobj._show()
        headcontrol = [i for i in self.control.GetFirstChildControl().GetChildren() if i.ControlTypeName == 'ButtonControl'][0]
        RollIntoView(self.chatbox.ListControl(), headcontrol, equal=True)
        xbias = int(headcontrol.BoundingRectangle.width()*1.5)
        headcontrol.Click(x=xbias, simulateMove=False)
        chatrecordwnd = uia.WindowControl(ClassName='ChatRecordWnd', searchDepth=1)
        msgitems = chatrecordwnd.ListControl().GetChildren()
        msgs = []
        for msgitem in msgitems:
            textcontrols = [i for i in GetAllControl(msgitem) if i.ControlTypeName == 'TextControl']
            who = textcontrols[0].Name
            time = textcontrols[1].Name
            try:
                content = textcontrols[2].Name
            except IndexError:
                content = ''
            msgs.append(([who, content, ParseWeChatTime(time)]))
        chatrecordwnd.SendKeys('{Esc}')
        return msgs



message_types = {
    'SYS': SysMessage,
    'Time': TimeMessage,
    'Recall': RecallMessage,
    'Self': SelfMessage
}

def ParseMessage(data, control, wx):
    """根据消息类型创建相应的消息对象

    Args:
        data: 消息数据
        control: 消息控件
        wx: 微信对象

    Returns:
        Message: 消息对象
    """
    try:
        # 使用消息类型映射创建消息对象
        message_class = message_types.get(data[0], FriendMessage)
        return message_class(data, control, wx)
    except Exception as e:
        # 出现异常时，返回一个简单的系统消息对象
        import traceback
        print(f"创建消息对象时出错: {str(e)}")
        traceback.print_exc()
        return SysMessage(['SYS', f'创建消息对象出错: {str(e)}', '0'], control, wx)


class LoginWnd:
    _class_name = 'WeChatLoginWndForPC'
    UiaAPI = uia.PaneControl(ClassName=_class_name, searchDepth=1)

    def __repr__(self) -> str:
        return f"<wxauto LoginWnd Object at {hex(id(self))}>"

    def _show(self):
        self.HWND = FindWindow(classname=self._class_name)
        win32gui.ShowWindow(self.HWND, 1)
        win32gui.SetWindowPos(self.HWND, -1, 0, 0, 0, 0, 3)
        win32gui.SetWindowPos(self.HWND, -2, 0, 0, 0, 0, 3)
        self.UiaAPI.SwitchToThisWindow()

    @property
    def _app_path(self):
        HWND = FindWindow(classname=self._class_name)
        return GetPathByHwnd(HWND)

    def login(self):
        enter_button = self.UiaAPI.ButtonControl(Name='进入微信')
        if enter_button.Exists():
            enter_button.Click(simulateMove=False)

    def get_qrcode(self):
        """获取登录二维码

        Returns:
            str: 二维码图片的保存路径
        """
        switch_account_button = self.UiaAPI.ButtonControl(Name='切换账号')
        if switch_account_button.Exists():
            switch_account_button.Click(simulateMove=False)
        self._show()
        qrcode_control = self.UiaAPI.ButtonControl(Name='二维码')
        qrcode = qrcode_control.ScreenShot()
        return qrcode