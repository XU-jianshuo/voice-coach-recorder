from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile


class AudioStorage:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    def save_upload(
        self, upload: UploadFile, session_id: str, started_at: datetime
    ) -> str:
        extension = Path(upload.filename or "audio.bin").suffix or ".bin"
        relative_path = Path("audio") / started_at.strftime("%Y/%m/%d")
        target_dir = self.root_dir / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{session_id}_{uuid4().hex[:8]}{extension}"
        target_path = target_dir / filename
        with target_path.open("wb") as output:
            while chunk := upload.file.read(1024 * 1024):
                output.write(chunk)

        return str(relative_path / filename).replace("\\", "/")
