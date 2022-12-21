from wx import Timer as Timer


class CallbackTimer(Timer):
    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback

    def Notify(self):
        self.callback()


def pick_best_url(urls):
    picks = urls[list(urls.keys())[0]]
    return picks[list(picks.keys())[-1]]


def pick_no_video_url(urls):
    return urls[list(urls.keys())[0]]["0"]


def match_anime_titles(anime_list, anime_title):
    for anime in anime_list:
        if anime_title.lower() in anime.lower():
            yield anime
