"""
PromptVC — Git-like version control for LLM prompts.

Commit your prompts. Diff your thinking. Never lose what worked.

Usage:
    $ promptvc commit summarizer prompt.txt -m "initial version"
    $ promptvc log summarizer
    $ promptvc diff summarizer <hash_a> <hash_b>
    $ promptvc checkout summarizer <hash>

Homepage: https://github.com/Youssef-osama33/promptvc
License:  MIT
"""

__version__ = "0.1.0"
__author__ = "Youssef Osama"
__license__ = "MIT"
__url__ = "https://github.com/Youssef-osama33/promptvc"
__all__ = ["__version__", "__author__", "__license__", "__url__"]
