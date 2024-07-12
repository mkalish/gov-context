import os
import re
from bs4 import BeautifulSoup
import requests
from vtt_to_srt.vtt_to_srt import ConvertFile  # type: ignore

# https://video.fairfaxcounty.gov/VPodcast.php?view_id=9
# https://www.fairfaxcounty.gov/boardofsupervisors/jan-24-2023-meeting
# https://video.fairfaxcounty.gov/player/clip/2706
# https://video.fairfaxcounty.gov/videos/2706/captions.vtt
# https://video.fairfaxcounty.gov/MediaPlayer.php?view_id=9&clip_id=3414
# https://video.fairfaxcounty.gov/player/clip/3174
# https://www.fairfaxcounty.gov/boardofsupervisors/may-23-2023-meeting

CLIP_ID_REGEX = re.compile("clip\/(?P<clip_id>[0-9]*)")


def get_video_ids_from_ffx_site(year: str) -> list[tuple[str, str]]:
    request = requests.get(
        f"https://www.fairfaxcounty.gov/boardofsupervisors/{year}-board-meetings"
    )
    soup = BeautifulSoup(request.content, "html.parser")
    videos = []
    for link in soup.find_all("a"):
        if "Full Board of Supervisors Meeting" in link.get_text():
            meeting_link = link.get("href")
            if "https://www.fairfaxcounty.gov" not in meeting_link:
                meeting_link = f"https://www.fairfaxcounty.gov{meeting_link}"
            meeting_request = requests.get(meeting_link)
            meeting_soup = BeautifulSoup(meeting_request.content)
            meeting_date = (
                meeting_soup.find("div", {"class": "event_date value"})
                .get_text()  # type: ignore
                .split(" - ")[0]
            )
            for link in meeting_soup.find_all("a", {"class": "nav-link"}):
                if link.get_text() == "Watch Agenda-Linked Video (English Captions)":
                    search = CLIP_ID_REGEX.search(link.get("href"))
                    if search is not None:
                        date_parts = meeting_date.split("/")
                        videos.append(
                            (
                                f"{date_parts[2]}/{date_parts[0]}/{date_parts[1]}",
                                search.group("clip_id"),
                            )
                        )

    return videos


def download_caption(clip_id: str):
    url = f"https://video.fairfaxcounty.gov/videos/{clip_id}/captions.vtt"
    request = requests.get(url)
    return request.content.decode("utf-8")


def convert_to_srt(raw_path: str):
    convert_file = ConvertFile(raw_path, "utf-8")
    convert_file.convert()


ids = get_video_ids_from_ffx_site("2023")
for path, id in ids:
    captions = download_caption(id)
    vtt_path = f"data/raw/transcripts/{path}/board_meeting.vtt"
    os.makedirs(os.path.dirname(vtt_path), exist_ok=True)
    with open(vtt_path, "w") as file:
        file.write(captions)

    convert_to_srt(vtt_path)
