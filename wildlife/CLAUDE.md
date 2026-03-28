# Wildlife

Garden wildlife monitoring tools. Camera: Reolink CX810 at 192.168.1.89 (garden path).

## hedgehog_watch.py
Motion detection for the garden camera. Compares consecutive snapshots, detects large moving objects (filtering wind/noise), sends Discord alerts with annotated images.

- **Test**: `python3 wildlife/hedgehog_watch.py --test` (captures two frames 30s apart)
- **Run**: `python3 wildlife/hedgehog_watch.py --interval 60` (production watch)
- **No alerts**: Add `--no-alert` to suppress Discord notifications

Detection parameters tuned for night vision IR: 25 brightness threshold, 0.5-30% change band, 500px minimum cluster. Timestamp overlay is cropped before comparison.

Archives detections to `/mnt/file_server/wildlife/hedgehog-watch/`.
