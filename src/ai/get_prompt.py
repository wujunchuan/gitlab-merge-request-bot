from pathlib import Path
from typing import Dict


class PromptManager:
    """Prompt管理器，用于加载和管理各种prompt文件"""

    def __init__(self):
        self.prompt_dir = Path(__file__).parent / "prompt"
        self._cache: Dict[str, str] = {}

    def load_prompt(self, filename: str, use_cache: bool = True) -> str:
        """
        加载prompt文件

        Args:
            filename: prompt文件名（支持.md和.txt）
            use_cache: 是否使用缓存
        """
        if use_cache and filename in self._cache:
            return self._cache[filename]

        file_path = self.prompt_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        if use_cache:
            self._cache[filename] = content

        return content

    def reload_prompt(self, filename: str) -> str:
        """重新加载prompt（清除缓存）"""
        if filename in self._cache:
            del self._cache[filename]
        return self.load_prompt(filename, use_cache=True)


# 全局prompt管理器实例
prompt_manager = PromptManager()
