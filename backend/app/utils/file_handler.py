import os
import aiofiles
from fastapi import UploadFile

async def save_upload_file(upload_file: UploadFile, dest_path: str) -> None:
    """
    异步保存上传的文件到指定路径
    """
    async with aiofiles.open(dest_path, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(content)

async def read_file_content(filepath: str) -> str:
    """
    异步读取文本文件内容
    """
    if not os.path.exists(filepath):
        return ""
    async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
        return await f.read()

async def write_file_content(filepath: str, content: str) -> None:
    """
    异步写入文本文件内容
    """
    async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
        await f.write(content)

def delete_file(filepath: str) -> bool:
    """
    安全删除本地文件
    """
    if os.path.exists(filepath):
        try:
            os.remove(filepath)
            return True
        except Exception:
            pass
    return False

def get_file_size(filepath: str) -> int:
    """
    获取指定路径的文件大小
    """
    if os.path.exists(filepath):
        return os.path.getsize(filepath)
    return 0
