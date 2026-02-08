"""
Agent - 계층적 에이전트 클래스

조직 구조:
  CEO (대표이사)          depth=0
  ├─ 부장 (Department Head)  depth=1
  │  ├─ 직원 (Staff)         depth=2
  │  └─ 직원 (Staff)         depth=2
  └─ 부장 (Department Head)  depth=1
     └─ 직원 (Staff)         depth=2
"""

from .model import SharedModel

MAX_DEPTH = 2  # 0=CEO, 1=부장, 2=직원

STATUS_ICONS = {
    "idle": "⏸",
    "working": "⏳",
    "done": "✅",
    "error": "❌",
}


class Agent:
    """
    계층적 에이전트. CEO, 부장, 직원 모두 같은 클래스를 사용하며
    system_prompt와 계층 위치로 역할이 구분됩니다.
    """

    def __init__(self, agent_id, name, role, system_prompt,
                 parent=None, icon="", max_history=3):
        self.id = agent_id
        self.name = name
        self.role = role
        self.icon = icon
        self.system_prompt = system_prompt
        self.parent = parent
        self.children = []
        self.depth = 0 if parent is None else parent.depth + 1
        self.max_history = max_history
        self.history = []
        self.status = "idle"
        self.task_description = ""
        self.result = None
        self._model = SharedModel.get()

    @property
    def display_name(self):
        return f"{self.icon} {self.name}" if self.icon else self.name

    @property
    def title(self):
        """직급 포함 표시명"""
        ranks = {0: "대표이사", 1: "부장", 2: "직원"}
        rank = ranks.get(self.depth, "")
        return f"{self.display_name} ({rank})" if rank else self.display_name

    def respond(self, query):
        """이 에이전트의 관점에서 응답을 생성합니다."""
        self.status = "working"
        try:
            response, self.history = self._model.chat(
                query,
                history=self.history,
                system=self.system_prompt,
            )
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            self.status = "done"
            self.result = response
            return response
        except Exception as e:
            self.status = "error"
            self.result = f"오류: {str(e)}"
            return self.result

    def spawn_child(self, name, role, system_prompt, icon=""):
        """하위 에이전트(부하직원)를 생성합니다."""
        child_id = f"{self.id}.{len(self.children)}"
        child = Agent(
            agent_id=child_id,
            name=name,
            role=role,
            system_prompt=system_prompt,
            parent=self,
            icon=icon,
            max_history=max(1, self.max_history - 1),
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
