import wx


__all__ = (
    "RelativeParameter", "Object", "RelativeSizeObject",
    "RelativePositionObject", "RelativeFontObject", "RelativeObject",
    "RelativePanel", "RelativePosition", "RelativeFont", "RelativeSize"
)


class RelativeParameter:
    def __init__(self, w: float, h: float):
        self.w = w
        self.h = h

    def __mul__(self, other):
        return int(other[0]*self.w), int(other[1]*self.h)


class Object:
    BACKGROUND_COLOUR: wx.Colour = None
    FOREGROUND_COLOUR: wx.Colour = None

    def __init__(self):
        self.SetBackgroundColour(self.BACKGROUND_COLOUR if self.BACKGROUND_COLOUR else
                                 self.GetParent().GetBackgroundColour())
        self.SetForegroundColour(self.FOREGROUND_COLOUR if self.FOREGROUND_COLOUR else
                                 self.GetParent().GetForegroundColour())


def size_children(self):
    for child in self.GetChildren():
        if hasattr(child, "on_size"):
            child.on_size()


class RelativeSize:
    SIZE: RelativeParameter

    def __init__(self):
        if type(self.SIZE) != RelativeParameter:
            raise TypeError("SIZE attribute must be of type 'RelativeParameter'")

    @property
    def _size(self):
        return wx.Size(self.SIZE * self.GetParent().GetSize())

    def on_size(self, children=True):
        self.SetSize(self._size)
        if children:
            size_children(self)


class RelativeSizeObject(RelativeSize, Object):
    def __init__(self):
        super().__init__()
        Object.__init__(self)


class RelativePosition:
    POSITION: RelativeParameter

    def __init__(self):
        if type(self.POSITION) != RelativeParameter:
            raise TypeError("POSITION attribute must be of type 'RelativeParameter'")

    @property
    def _position(self):
        parent = self.GetParent()
        return parent.GetPosition() + wx.Point(self.POSITION * parent.GetSize())

    def on_size(self, children=True):
        self.SetPosition(self._position)
        if children:
            size_children(self)


class RelativePositionObject(RelativePosition, Object):
    def __init__(self):
        super().__init__()
        Object.__init__(self)


class RelativeFont:
    FONT_SIZE: float = 0

    def __init__(self):
        if self.FONT_SIZE <= 0:
            raise ValueError("FONT_SIZE attribute must be greater than 0 when CONTAINS_TEXT is true")
        super().__init__()

    def on_size(self, children=True):
        font = self.GetFont()
        font.SetPixelSize(wx.Size(0, int(self.GetSize()[1] * self.FONT_SIZE)))
        self.SetFont(font)
        if children:
            size_children(self)


class RelativeFontObject(RelativeFont, Object):
    def __init__(self):
        super().__init__()
        Object.__init__(self)


class RelativeObject(RelativeSize, RelativePosition, RelativeFont, Object):
    CONTAINS_TEXT: bool = False

    def __init__(self):
        Object.__init__(self)
        RelativeSize.__init__(self)
        RelativePosition.__init__(self)
        if self.CONTAINS_TEXT:
            RelativeFont.__init__(self)

    def on_size(self, children=True):
        RelativeSize.on_size(self, False)
        RelativePosition.on_size(self, False)
        if self.CONTAINS_TEXT:
            RelativeFont.on_size(self, False)
        if children:
            size_children(self)


class RelativePanel(wx.Panel, RelativeSizeObject):
    SIZE = RelativeParameter(1, 1)

    def __init__(self, parent):
        super().__init__(parent)
        RelativeSizeObject.__init__(self)
