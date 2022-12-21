# TODO:
# - Settings menu
# - maybe better searching algorithm
# - pretty up the gui
# - cache for game info
# - fix dropdown formatting

import os
import random
import wx
from wx.media import MediaCtrl, EVT_MEDIA_LOADED, MEDIABACKEND_WMP10, EVT_MEDIA_PLAY
from wx.lib.scrolledpanel import ScrolledPanel

from enums import GameState
from structure import Game
from util import *
from base import *


class GamePanel(RelativePanel):
    class Player(MediaCtrl, RelativeObject):
        POSITION = RelativeParameter(0.1, 0.1)
        SIZE = RelativeParameter(0.5, 0.35)
        BACKGROUND_COLOUR = wx.BLACK

        def __init__(self, parent):
            super().__init__(parent, szBackend=MEDIABACKEND_WMP10)
            RelativeObject.__init__(self)

            self.section_length = 20000  # TODO: adjustable
            self.timer = None
            self.starting_point = None

            self.Bind(EVT_MEDIA_LOADED, self.on_loaded)
            self.Bind(EVT_MEDIA_PLAY, self.on_played)

        def reset(self):
            self.starting_point = None

        def load(self, url, start=None, evt=None):
            if not self.LoadURI(url):
                print("Failed to load file...")
            else:
                if start is not None:
                    self.starting_point = start

        def on_loaded(self, evt=None):
            self.SetVolume(0.5)  # TODO: volume variable and adjustable
            if self.starting_point is None:
                self.starting_point = random.randint(0, self.Length() - self.section_length)
            self.Seek(self.starting_point)
            self.Play()

        def on_played(self, evt=None):
            self.timer = CallbackTimer(self.on_finished)
            self.timer.StartOnce(20000)
            self.GetParent().on_played()

        def on_stopped(self, evt=None):
            self.GetParent().on_stopped()

        def on_finished(self):
            self.Stop()
            self.on_stopped()

    class TextBox(wx.TextCtrl, RelativeObject):
        POSITION = RelativeParameter(0.25, 0.5)
        SIZE = RelativeParameter(0.5, 0.05)
        CONTAINS_TEXT = True
        FONT_SIZE = 0.55

        def __init__(self, parent):
            super().__init__(parent, style=wx.TE_PROCESS_ENTER)
            RelativeObject.__init__(self)

            self.SetDefaultStyle(wx.TextAttr(self.FOREGROUND_COLOUR, alignment=wx.TE_CENTRE))

    class LoadingText(wx.StaticText, RelativeObject):
        POSITION = RelativeParameter(0.25, 0.35)
        SIZE = RelativeParameter(0.5, 0.3)
        CONTAINS_TEXT = True
        FONT_SIZE = 0.5

        def __init__(self, parent):
            super().__init__(parent)
            RelativeObject.__init__(self)

            self.SetLabel("Loading...")
            self.Center()

    class DropdownSelect(ScrolledPanel, RelativeObject):
        POSITION = RelativeParameter(0.25, 0.55)
        SIZE = RelativeParameter(0.5, 0.3)

        class Selection(wx.StaticText):
            DOWNSCALE = 0.1
            SELECTION_COLOR = wx.Colour(40, 40, 80)
            FOREGROUND_COLOUR = wx.WHITE
            FONT_SIZE = 0.1

            def __init__(self, parent):
                super().__init__(parent, style=wx.ALIGN_CENTER | wx.ST_NO_AUTORESIZE)

            def on_size(self, children=True):
                wsize = self.GetParent().GetSize()
                font = self.GetFont()
                font.SetPixelSize(wx.Size(0, int(wsize[1]*self.FONT_SIZE)))
                self.SetFont(font)
                self.Wrap(wsize[0])

        def __init__(self, parent):
            super().__init__(parent)
            RelativeObject.__init__(self)

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.selections = [self.Selection(self) for _ in range(20)]
            self.index = -1

            self.SetSizer(self.sizer)

        def get_current_selection(self):
            if self.index == -1:
                return
            return self.get_sizer_children()[self.index].GetWindow().GetLabel()

        def get_sizer_children(self):
            return [child for child in self.sizer.GetChildren() if child.GetWindow() is not None]

        def on_down(self):
            self.index = min(self.index+1, len(self.get_sizer_children())-1)
            self.on_selection_update()

        def on_up(self):
            self.index = max(self.index-1, -1)
            self.on_selection_update()

        def on_selection_update(self):
            background = self.GetBackgroundColour()
            for selection in self.selections:
                selection.SetBackgroundColour(background)
                selection.Refresh()
            if self.index != -1:
                selection = self.get_sizer_children()[self.index].GetWindow()
                selection.SetBackgroundColour(self.Selection.SELECTION_COLOR)
                selection.Refresh()
                self.ScrollChildIntoView(selection)

        def clear(self, full=True):
            for selection in self.selections:
                selection.Hide()
            self.sizer.Clear()
            if full:
                self.index = -1
                self.on_selection_update()

        def update_anime(self, anime):
            self.clear(False)
            for i, title in enumerate(anime):
                self.selections[i].Show()
                self.selections[i].SetLabel(title)
                self.selections[i].on_size(False)
                self.sizer.Add(self.selections[i], 1, wx.EXPAND)
            if (size := self.sizer.GetMinSize())[1] < (height := self.GetSize()[1]):
                self.sizer.AddSpacer(height-size[1])
            self.sizer.Layout()
            self.SetupScrolling(scroll_x=False)

        def on_size(self, children=True):
            super().on_size(children)
            self.sizer.SetDimension(self.sizer.GetPosition(), self.GetSize())
            self.sizer.Layout()

    def __init__(self, parent):
        super().__init__(parent)

        self.text_box = self.TextBox(self)
        self.text_box.Hide()
        self.player = self.Player(self)
        self.player.Hide()
        self.dropdown = self.DropdownSelect(self)
        self.dropdown.Hide()
        # Show loading screen while loading game data
        self.loading = self.LoadingText(self)

        # Load game data
        self.games = [Game.from_path(os.path.join("data", path)) for path in os.listdir("data")]
        self.anime_list = [[list(rnd.anime.values()) for rnd in game.rounds] for game in self.games]
        self.anime_list = sum(sum(self.anime_list, []), [])
        self.anime_list = list(set(self.anime_list))
        self.currently_playing = None
        self.state = GameState.NOTPLAYING

        # Show play screen
        self.loading.Destroy()
        self.text_box.Show()
        self.player.Show()
        self.dropdown.Show()

        self.Bind(wx.EVT_TEXT, self.on_text, self.text_box)
        self.text_box.Bind(wx.EVT_KEY_DOWN, self.on_keydown)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter)

    def on_keydown(self, evt=None):
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_UP:
            self.dropdown.on_up()
        elif keycode == wx.WXK_DOWN:
            self.dropdown.on_down()
        elif self.state == GameState.GUESSING:
            evt.Skip()

    def on_text_enter(self, evt=None):
        if (selection := self.dropdown.get_current_selection()) is not None:
            self.text_box.SetValue(selection)
            self.dropdown.clear()

    def on_text(self, evt=None):
        anime = self.text_box.GetValue()
        if anime.strip() == "":
            return self.dropdown.clear()
        self.dropdown.update_anime(list(match_anime_titles(self.anime_list, anime))[:20])

    def play_round(self):
        self.state = GameState.LOADING
        self.set_random()
        self.play_no_video()

    def set_random(self):
        self.currently_playing = random.choice(random.choice(self.games).rounds)

    def play_no_video(self):
        self.player.load(pick_no_video_url(self.currently_playing.urls))

    def play_with_video(self):
        self.player.load(pick_best_url(self.currently_playing.urls))

    def on_played(self):
        self.state = GameState.GUESSING if self.state == GameState.LOADING else GameState.REVEALING

    def on_stopped(self):
        if self.state == GameState.GUESSING:
            if self.text_box.GetValue().lower() in list(map(str.lower, self.currently_playing.anime.values())):
                print("Correct!")
            else:
                print("Wrong!")
            self.play_with_video()
        elif self.state == GameState.REVEALING:
            self.player.reset()
            self.text_box.SetValue("")
            self.play_round()

    def on_open(self):
        self.play_round()

    def on_size(self, children=True):
        self.SetSize(self.GetParent().GetSize())
        if children:
            for child in self.GetChildren():
                if hasattr(child, "on_size"):
                    child.on_size()


class StartScreenPanel(RelativePanel):
    def __init__(self, parent):
        super().__init__(parent)

        btn = wx.Button(self, label="press me")
        self.Bind(wx.EVT_BUTTON, parent.start, btn)


class AppFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="AMQ Practice", size=(800, 600), pos=(1980, 200))

        self.SetBackgroundColour(wx.Colour(60, 60, 60))
        self.SetForegroundColour(wx.WHITE)

        self.game_panel = GamePanel(self)
        self.game_panel.Hide()

        self.start_panel = StartScreenPanel(self)

        self.Bind(wx.EVT_SIZE, self.on_size)

    def start(self, evt=None):
        self.game_panel.Show()
        self.start_panel.Hide()
        self.game_panel.on_open()

    def on_size(self, evt=None):
        for child in self.GetChildren():
            child.on_size()


if __name__ == "__main__":
    app = wx.App()
    frame = AppFrame()
    frame.Show()
    app.MainLoop()
