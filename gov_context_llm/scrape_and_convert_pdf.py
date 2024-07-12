import os
import re
from bs4 import BeautifulSoup
import requests

# https://video.fairfaxcounty.gov/VPodcast.php?view_id=9
# https://www.fairfaxcounty.gov/boardofsupervisors/jan-24-2023-meeting
# https://video.fairfaxcounty.gov/player/clip/2706
# https://video.fairfaxcounty.gov/videos/2706/captions.vtt
# https://video.fairfaxcounty.gov/MediaPlayer.php?view_id=9&clip_id=3414
# https://video.fairfaxcounty.gov/player/clip/3174
# https://www.fairfaxcounty.gov/boardofsupervisors/may-23-2023-meeting

CLIP_ID_REGEX = re.compile("clip\/(?P<clip_id>[0-9]*)")


def get_pdf_links_from_ffx_site(year: str) -> list[tuple[str, str]]:
    request = requests.get(
        f"https://www.fairfaxcounty.gov/boardofsupervisors/{year}-board-meetings"
    )
    soup = BeautifulSoup(request.content, "html.parser")
    summaries = []
    for link in soup.find_all("a"):
        if "Full Board of Supervisors Meeting" in link.get_text():
            meeting_link = link.get("href")
            if "https://www.fairfaxcounty.gov" not in meeting_link:
                meeting_link = f"https://www.fairfaxcounty.gov{meeting_link}"
            meeting_request = requests.get(meeting_link)
            meeting_soup = BeautifulSoup(meeting_request.content)
            meeting_date = (
                meeting_soup.find("div", {"class": "event_date value"})
                .get_text()
                .split(" - ")[0]
            )
            for link in meeting_soup.find_all("a", {"aria-label": "Official Summary"}):
                pdf_link = link.get("href")
                if ".pdf" in pdf_link:
                    if "/boardofsupervisors/.." in pdf_link:
                        # https://www.fairfaxcounty.gov/boardofsupervisors/sites/boardofsupervisors/files/assets/10-10-23_final-summary.pdf
                        fixed = pdf_link.replace("/boardofsupervisors/..", "")
                        pdf_link = f"https://www.fairfaxcounty.gov/boardofsupervisors/sites{fixed}"
                    date_parts = meeting_date.split("/")
                    summaries.append(
                        (
                            f"{date_parts[2]}/{date_parts[0]}/{date_parts[1]}",
                            pdf_link,
                        )
                    )

    return summaries


ids = get_pdf_links_from_ffx_site("2024")
for path, url in ids:
    response = requests.get(url)
    pdf_path = f"data/raw/summaries/{path}/official_summary.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    with open(pdf_path, "wb") as file:
        file.write(response.content)
