from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from researchqa.scinews_runner_v2 import main
if __name__=='__main__':main()
