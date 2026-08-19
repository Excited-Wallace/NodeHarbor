import aiohttp
import os
import aiofiles

async def get_release_info(repo: str) -> dict:
    """
    调用 GitHub API 获取最新发布信息
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=15) as response:
            if response.status == 200:
                return await response.json()
            return {}

def parse_release_assets(assets: list, platform: str) -> str:
    """
    解析提取符合各个平台的下载链接
    """
    platform = platform.lower()
    for asset in assets:
        name = asset.get("name", "").lower()
        if platform == "windows":
            if "windows" in name or "win" in name:
                if "64" in name and "zip" in name:
                    return asset.get("browser_download_url")
        elif platform == "linux":
            if "linux" in name and "amd64" in name and "tar.gz" in name:
                return asset.get("browser_download_url")
        elif platform == "macos":
            if "darwin" in name or "mac" in name:
                if "arm64" in name or "amd64" in name:
                    return asset.get("browser_download_url")
        elif platform == "android":
            if "android" in name and "apk" in name:
                return asset.get("browser_download_url")
                
    # 宽松匹配
    for asset in assets:
        name = asset.get("name", "").lower()
        if platform == "windows" and "win" in name and ("zip" in name or "exe" in name):
            return asset.get("browser_download_url")
        elif platform == "linux" and "linux" in name and ("tar.gz" in name or "zip" in name):
            return asset.get("browser_download_url")
        elif platform == "macos" and "mac" in name:
            return asset.get("browser_download_url")
        elif platform == "android" and "apk" in name:
            return asset.get("browser_download_url")
    return ""

async def download_file(url: str, dest_path: str) -> bool:
    """
    异步下载文件
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=300) as response:
                if response.status == 200:
                    async with aiofiles.open(dest_path, 'wb') as f:
                        while chunk := await response.content.read(1024 * 1024):
                            await f.write(chunk)
                    return True
    except Exception as e:
        print(f"Download error: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
    return False
