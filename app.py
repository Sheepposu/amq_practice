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
from wx.lib.buttons import GenButton as _Button

from enums import GameState
from structure import Game
from util import *
from base import *


class Text(wx.StaticText, RelativeObject):
    CONTAINS_TEXT = True

    def __init__(self, parent, position, size, font_size, *args, **kwargs):
        self.POSITION = RelativeParameter(*position)
        self.SIZE = RelativeParameter(*size)
        self.FONT_SIZE = font_size
        wx.StaticText.__init__(self, parent, *args, **kwargs)
        RelativeObject.__init__(self)


class TextButton(_Button, RelativeObject):
    CONTAINS_TEXT = True

    def __init__(self, parent, position, size, font_size, hover_color=None, *args, **kwargs):
        self.POSITION = RelativeParameter(*position)
        self.SIZE = RelativeParameter(*size)
        self.FONT_SIZE = font_size
        _Button.__init__(self, parent, *args, **kwargs)
        RelativeObject.__init__(self)

        self.bg_color = self.GetBackgroundColour()
        self.hover_color = hover_color if hover_color is not None else self.bg_color

        self.Bind(wx.EVT_ENTER_WINDOW, self.on_hover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_unhover)

    def on_hover(self, evt):
        self.SetBackgroundColour(self.hover_color)
        self.Refresh()

    def on_unhover(self, evt):
        self.SetOwnBackgroundColour(self.bg_color)
        self.Refresh()


class SliderSetting(wx.Slider, RelativeObject):
    def __init__(self, parent, min_value, max_value, default_value, position, size, setting=None):
        self.POSITION = RelativeParameter(*position)
        self.SIZE = RelativeParameter(*size)
        self.setting = setting
        wx.Slider.__init__(self, parent, value=default_value, minValue=min_value, maxValue=max_value)
        RelativeObject.__init__(self)


class Image(wx.StaticBitmap, RelativeSize, RelativePosition):
    def __init__(self, parent, position, size, file):
        self.POSITION = RelativeParameter(*position)
        self.SIZE = RelativeParameter(*size)
        wx.StaticBitmap.__init__(self, parent, bitmap=wx.Bitmap(file, wx.BITMAP_TYPE_ANY))
        self.image_size = self.GetSize()
        RelativeSize.__init__(self)
        RelativePosition.__init__(self)

    @property
    def _size(self):
        if self.SIZE.h == 0:
            w = self.SIZE.w * self.GetParent().GetSize()[0]
            return wx.Size(w, int(self.image_size[1]/self.image_size[0]*w))
        else:
            h = self.SIZE.h * self.GetParent().GetSize()[1]
            return wx.Size(int(self.image_size[0]/self.image_size[1]*h), h)


class GamePanel(RelativePanel):
    class Player(MediaCtrl, RelativeObject):
        POSITION = RelativeParameter(0.1, 0.1)
        SIZE = RelativeParameter(0.5, 0.35)
        BACKGROUND_COLOUR = wx.BLACK

        def __init__(self, parent):
            super().__init__(parent, szBackend=MEDIABACKEND_WMP10)
            RelativeObject.__init__(self)

            self.section_length = 20000
            self.volume = 0.5
            self.timer = None
            self.starting_point = None

            self.SetVolume(self.volume)

            self.Bind(EVT_MEDIA_LOADED, self.on_loaded)
            self.Bind(EVT_MEDIA_PLAY, self.on_played)

        def adjust_volume(self, volume):
            self.volume = volume
            self.SetVolume(self.volume)

        def load_settings(self, settings):
            self.section_length = settings["guess_time"] * 1000

        def reset(self):
            self.starting_point = None

        def load(self, url, start=None, evt=None):
            if not self.LoadURI(url):
                print("Failed to load file...")
            else:
                if start is not None:
                    self.starting_point = start

        def on_loaded(self, evt=None):
            if self.starting_point is None:
                self.starting_point = random.randint(0, self.Length() - self.section_length)
            self.Seek(self.starting_point)
            self.Play()

        def on_played(self, evt=None):
            self.timer = CallbackTimer(self.on_finished)
            self.timer.StartOnce(self.section_length)
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
        self.volume = SliderSetting(self, 0, 100, int(self.player.volume*100), (0.78, 0.0), (0.2, 0.05))
        # volume_image = Image(self, (0.75, 0.0), (0.05, 0), "assets/images/volume.png")
        # volume_image.Hide()
        # Show loading screen while loading game data
        self.loading = self.LoadingText(self)

        # Load game data
        self.games = [Game.from_path(os.path.join("data", path)) for path in os.listdir("data")]
        self.anime_list = [[list(rnd.anime.values()) for rnd in game.rounds] for game in self.games]
        self.anime_list = sum(sum(self.anime_list, []), [])
        self.anime_list = list(set(self.anime_list))
        self.currently_playing = None
        self.state = GameState.NOTPLAYING
        self.settings = {}
        self.results = []

        # Show play screen
        self.loading.Destroy()
        self.text_box.Show()
        self.player.Show()
        self.dropdown.Show()
        # volume_image.Show()

        self.Bind(wx.EVT_TEXT, self.on_text, self.text_box)
        self.text_box.Bind(wx.EVT_KEY_DOWN, self.on_keydown)
        self.text_box.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter)
        self.Bind(wx.EVT_SCROLL, self.on_volume_adjust, self.volume)

    def on_volume_adjust(self, evt):
        self.player.adjust_volume(self.volume.GetValue()/100)

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
            self.on_guessing_end()
        elif self.state == GameState.REVEALING:
            self.on_reveal_end()

    def on_guessing_end(self):
        if self.text_box.GetValue().lower() in list(map(str.lower, self.currently_playing.anime.values())):
            print("Correct!")
            self.results.append(True)
        else:
            print("Wrong!")
            self.results.append(False)
        self.play_with_video()

    def on_reveal_end(self):
        self.player.reset()
        self.text_box.SetValue("")
        if len(self.results) < self.settings["songs"]:
            self.play_round()
        else:
            self.GetParent().end()

    def on_open(self, settings):
        self.settings = settings
        self.player.load_settings(settings)
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

        self.settings = {
            "songs": 20,
            "guess_time": 20
        }

        hover_color = wx.Colour(*map(lambda num: num-20, self.GetBackgroundColour()))
        self.song_slider = SliderSetting(self, 1, 100, 20, (0.25, 0.1), (0.5, 0.1), "songs")
        self.song_text = Text(self, (0, 0.2), (1, 0.1), 0.6,
                              label=f"Number of songs: {self.song_slider.GetValue()}",
                              style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE)
        self.guess_slider = SliderSetting(self, 5, 60, 20, (0.25, 0.35), (0.5, 0.1), "guess_time")
        self.guess_text = Text(self, (0, 0.45), (1, 0.1), 0.6,
                               label=f"Guess time: {self.guess_slider.GetValue()}",
                               style=wx.ALIGN_CENTRE_HORIZONTAL | wx.ST_NO_AUTORESIZE)

        self.start_button = TextButton(self, (0.4, 0.6), (0.2, 0.1), 0.6, hover_color, label="Start")

        self.Bind(wx.EVT_SCROLL, lambda evt: self.on_slider_adjust(evt, self.song_text), self.song_slider)
        self.Bind(wx.EVT_SCROLL, lambda evt: self.on_slider_adjust(evt, self.guess_text), self.guess_slider)
        self.Bind(wx.EVT_BUTTON, self.on_start, self.start_button)

    def on_slider_adjust(self, evt, text):
        slider = evt.GetEventObject()
        self.settings[slider.setting] = slider.GetValue()
        label_text = " ".join(text.GetLabelText().split()[:-1])
        text.SetLabelText(f"{label_text} {self.settings[slider.setting]}")

    def on_start(self, evt):
        self.GetParent().start()


class AppFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="AMQ Practice", size=(800, 600), pos=(1980, 200))

        self.SetBackgroundColour(wx.Colour(60, 60, 60))
        self.SetForegroundColour(wx.WHITE)

        self.game_panel = GamePanel(self)
        self.game_panel.Hide()

        self.start_panel = StartScreenPanel(self)

        self.Bind(wx.EVT_SIZE, self.on_size)

    def start(self):
        self.game_panel.Show()
        self.start_panel.Hide()
        self.game_panel.on_open(self.start_panel.settings)

    def end(self):
        self.start_panel.Show()
        self.game_panel.Hide()

    def on_size(self, evt=None):
        for child in self.GetChildren():
            child.on_size()


if __name__ == "__main__":
    app = wx.App()
    frame = AppFrame()
    frame.Show()
    app.MainLoop()
