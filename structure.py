from typing import Dict, Union, List
from enums import SongType, Season, Status
from json import load


class SongTypeInfo:
    __slots__ = ("type", "number")

    def __init__(self, string):
        if string.lower() == "insert song":
            self.type: SongType = SongType.INSERT
            self.number: int = 0
            return
        self.type, self.number = string.split()
        self.type: SongType = SongType[self.type.upper()]
        self.number: int = int(self.number)


class Vintage:
    __slots__ = ("season", "year")

    def __init__(self, string):
        self.season, self.year = string.split()
        self.season: Season = Season[self.season.upper()]
        self.year: int = int(self.year)


class Player:
    __slots__ = (
        "name", "score", "correct_guesses", "correct", "answer", "guess_time",
        "active", "position", "position_slot"
    )

    def __init__(self, data):
        self.name: int = data["name"]
        self.score: int = data["score"]
        self.correct_guesses: Union[int, None] = data.get("correctGuesses")
        self.correct: bool = data["correct"]
        self.answer: str = data["answer"]
        self.guess_time: Union[int, None] = data.get("guessTime")
        self.active: bool = data["active"]
        self.position: int = data["position"]
        self.position_slot: int = data["positionSlot"]


class PlayerListInfo:
    __slots__ = ("name", "list_status", "score")

    def __init__(self, data):
        self.name: str = data["name"]
        self.list_status: Status = Status(data["listStatus"])
        self.score: int = data["score"]


class Round:
    __slots__ = (
        "game_mode", "name", "artist", "anime", "ann_id", "song_number", "active_players",
        "total_players", "type", "urls", "site_ids", "difficulty", "anime_type",
        "anime_score", "vintage", "tags", "genre", "alt_answers", "start_sample",
        "video_length", "players", "from_list", "correct", "self_answer"
    )

    def __init__(self, data):
        self.game_mode: str = data["gameMode"]
        self.name: str = data["name"]
        self.artist: str = data["artist"]
        self.anime: Dict[str, str] = data["anime"]
        self.ann_id: Union[int, None] = data.get("ann_id")
        self.song_number: int = data["songNumber"]
        self.active_players: int = data["activePlayers"]
        self.total_players: int = data["totalPlayers"]
        self.type: SongTypeInfo = SongTypeInfo(data["type"])
        self.urls: Dict[str, Dict[str, str]] = data["urls"]
        self.site_ids: Dict[str, int] = data["siteIds"]
        self.difficulty: Union[float, None] = None if data["difficulty"] == "Unrated" else float(data["difficulty"])
        self.anime_type: str = data["animeType"]
        self.anime_score: int = data["animeScore"]
        self.vintage: Vintage = Vintage(data["vintage"])
        self.tags: List[str] = data["tags"]
        self.genre: List[str] = data["genre"]
        self.alt_answers: List[str] = data["altAnswers"]
        self.start_sample: int = data["startSample"]
        self.video_length: float = data["videoLength"]
        self.players: List[Player] = list(map(Player, data["players"]))
        self.from_list: List[PlayerListInfo] = list(map(PlayerListInfo, data["fromList"]))
        self.correct: Union[bool, None] = data.get("correct")


class Game:
    __slots__ = ("rounds",)

    def __init__(self, data):
        self.rounds: List[Round] = list(map(Round, data))

    @classmethod
    def from_path(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls(load(f))
