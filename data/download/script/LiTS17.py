import libtorrent as lt
import os
import time
from IPython.display import display
import ipywidgets as widgets

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Set up libtorrent session
ses = lt.session()
ses.listen_on(6881, 6891)
downloads = []

# Path to the torrent file
# Update this path as needed
TFILE = "/mnt/data/coden/Multi-Organ-Tumor-Segmentation-Application/.torrent/LITS17-27772adef6f563a1ecc0ae19a528b956e6c803ce.torrent"
SAVE_PATH = "data"

params = {
    "save_path": SAVE_PATH,
    "ti": lt.torrent_info(TFILE),
}
downloads.append(ses.add_torrent(params))

state_str = [
    "queued",
    "checking",
    "downloading metadata",
    "downloading",
    "finished",
    "seeding",
    "allocating",
    "checking fastresume",
]

layout = widgets.Layout(width="auto")
style = {"description_width": "initial"}
download_bars = [
    widgets.FloatSlider(
        step=0.01, disabled=True, layout=layout, style=style
    )
    for _ in downloads
]

display(*download_bars)

while downloads:
    next_shift = 0
    for index, download in enumerate(downloads[:]):
        bar = download_bars[index + next_shift]
        if not download.is_seed():
            s = download.status()
            bar.description = " ".join([
                download.name(),
                ":",
                "%.2f" % (s.progress * 100),
                "%",
                "down",
                "%.1f" % (s.download_rate / 1000),
                "kB/s",
                "up",
                "%.1f" % (s.upload_rate / 1000),
                "kB/s",
                "peers",
                str(s.num_peers),
                "seeds",
                str(s.num_seeds),
                state_str[s.state],
            ])
            bar.value = s.progress * 100
        else:
            next_shift -= 1
            ses.remove_torrent(download)
            downloads.remove(download)
            bar.close()  # May not work in all environments
            download_bars.remove(bar)
            print("complete")
    time.sleep(1)
