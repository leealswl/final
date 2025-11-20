# 이 파일을 통해 v11_generator 디렉토리가 Python 패키지로 인식됩니다.

# nodes 폴더 안에 있던 graph_builder.py를 v11_generator 루트로 옮겼다고 가정하고, 
# 해당 파일에 정의된 핵심 그래프 구축 함수를 패키지 레벨로 노출시킵니다.
# from .testnode2 import create_proposal_graph
from .graph_builder import create_proposal_graph