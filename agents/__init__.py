"""
このパッケージはopenai-agents SDKのagentsモジュールを拡張します。
ローカルのagentsディレクトリとインストール済みSDKの名前衝突を解決するため、
SDKをインポートしてローカルサブモジュール（flight_agent等）を検索パスに追加します。
"""
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)

# プロジェクトルートを除外したsys.pathでSDKを読み込む
_orig_path = sys.path[:]
sys.path = [p for p in sys.path if os.path.abspath(p or ".") != _root]

# ローカルのagentsパッケージ（自分自身）をsys.modulesから除外し、SDKを読み込む
sys.modules.pop("agents", None)
import agents as _sdk  # noqa: E402

# sys.pathを元に戻す
sys.path = _orig_path

# SDKの__path__にローカルのagentsディレクトリを先頭追加
# → from agents.flight_agent import X などが動作するようになる
if _here not in _sdk.__path__:
    _sdk.__path__.insert(0, _here)

# sys.modules["agents"]はSDKモジュールを指し続ける（意図的）

