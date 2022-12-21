from enum import IntEnum, Enum


class SongType(IntEnum):
    INSERT = 3
    ENDING = 2
    OPENING = 1


class Season(Enum):
    WINTER = "Winter"
    SPRING = "Spring"
    SUMMER = "Summer"
    FALL = "Fall"


class Status(IntEnum):
    WATCHING = 1
    COMPLETED = 2
    ON_HOLD = 3
    DROPPED = 4
    PLAN_TO_WATCH = 5
    LOOTED = 6


class GameState(IntEnum):
    NOTPLAYING = 1
    LOADING = 2
    GUESSING = 3
    REVEALING = 4
