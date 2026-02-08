"""
Agent - 계층적 에이전트 클래스

4단계 조직 구조:
  🏢 대표이사 (CEO)          depth=0
  ├─ 본부장 (Division Head)   depth=1
  │  ├─ 팀장 (Team Lead)      depth=2
  │  │  ├─ 연구원 (Researcher) depth=3
  │  │  └─ 연구원              depth=3
  │  └─ 팀장                   depth=2
  └─ 본부장                    depth=1
"""

from .model import SharedModel

MAX_DEPTH = 3  # 0=CEO, 1=본부장, 2=팀장, 3=연구원

RANKS = {0: "대표이사", 1: "본부장", 2: "팀장", 3: "연구원"}

STATUS_ICONS = {
    "idle": "⏸",
    "working": "⏳",
    "done": "✅",
    "error": "❌",
}


class Agent:
    """
    계층적 에이전트. 모든 직급이 같은 클래스를 사용하며
    system_prompt와 계층 위치(depth)로 역할이 구분됩니다.
    """

    def __init__(self, agent_id, name, role, system_prompt,
                 parent=None, icon="", max_history=5):
        self.id = agent_id
        self.name = name
        self.role = role
        self.icon = icon
        self.system_prompt = system_prompt
        self.parent = parent
        self.children = []
        self.depth = 0 if parent is None else parent.depth + 1
        self.max_history = max_history
        self.history = []  # [{"role": "user"|"assistant", "content": str}, ...]
        self.status = "idle"
        self.task_description = ""
        self.result = None
        self._model = SharedModel.get()

    @property
    def rank(self):
        return RANKS.get(self.depth, "")

    @property
    def display_name(self):
        return f"{self.icon} {self.name}" if self.icon else self.name

    @property
    def title(self):
        """직급 포함 표시명"""
        r = self.rank
        return f"{self.display_name} ({r})" if r else self.display_name

    def respond(self, query):
        """이 에이전트의 관점에서 응답을 생성합니다."""
        self.status = "working"
        try:
            response, self.history = self._model.chat(
                query,
                history=self.history,
                system=self.system_prompt,
            )
            # 히스토리 크기 제한 (메시지 쌍 기준)
            max_messages = self.max_history * 2
            if len(self.history) > max_messages:
                self.history = self.history[-max_messages:]
            self.status = "done"
            self.result = response
            return response
        except Exception as e:
            self.status = "error"
            self.result = f"오류: {str(e)}"
            return self.result

    def spawn_child(self, name, role, system_prompt, icon=""):
        """하위 에이전트를 생성합니다."""
        child_id = f"{self.id}.{len(self.children)}"
        child = Agent(
            agent_id=child_id,
            name=name,
            role=role,
            system_prompt=system_prompt,
            parent=self,
            icon=icon,
            max_history=max(2, self.max_history - 1),
        )
        self.children.append(child)
        return child

    def clear(self):
        """이 에이전트와 모든 하위 에이전트를 초기화합니다."""
        self.history = []
        self.result = None
        self.status = "idle"
        self.task_description = ""
        for child in self.children:
            child.clear()
        self.children = []

    def get_tree(self):
        """조직도를 텍스트로 렌더링합니다."""
        lines = []
        self._build_tree(lines, prefix="", is_last=True, is_root=True)
        return "\n".join(lines)

    def _build_tree(self, lines, prefix, is_last, is_root):
        status = STATUS_ICONS.get(self.status, "")
        if is_root:
            connector = ""
            child_prefix = ""
        else:
            connector = "└─ " if is_last else "├─ "
            child_prefix = prefix + ("   " if is_last else "│  ")

        line = f"{prefix}{connector}{self.display_name} {status}"
        if self.task_description:
            line += f"  {self.task_description}"
        lines.append(line)

        for i, child in enumerate(self.children):
            child._build_tree(
                lines,
                prefix=child_prefix,
                is_last=(i == len(self.children) - 1),
                is_root=False,
            )
