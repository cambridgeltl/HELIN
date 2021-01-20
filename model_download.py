from google_drive_downloader import GoogleDriveDownloader as gdd
import os

DEFAULT_PATH = 'static/models/best-model.pt'
os.makedirs('static/models', exist_ok=True)
gdd.download_file_from_google_drive(file_id='1pZ9oMPuUnZp6IiBv-TBh-LlYdHZg-3Oa',dest_path=DEFAULT_PATH)

