"""
Orchestrator - CEO 오케스트레이션 핵심 로직

흐름:
  1. 사용자 메시지 수신
  2. input/ 파일 스캔
  3. CEO가 업무 배정 결정 (직접답변 or 부서 배정)
  4. 부서장이 업무 수행 (직접 or 팀원 위임)
  5. 결과를 계층적으로 종합하여 최종 답변
"""

import re
from pathlib import Path

from .model import SharedModel
from .agent import Agent
from .file_reader import FileReader
from .departments import (
    CEO_SYSTEM,
    DEPARTMENTS,
    TASK_ASSIGNMENT_TEMPLATE,
    DEPT_HEAD_TASK_TEMPLATE,
    STAFF_TASK_TEMPLATE,
    SYNTHESIS_TEMPLATE,
    DIRECT_RESPONSE_TEMPLATE,
)


class Orchestrator:
    """
    대표이사(CEO) 역할의 최상위 오케스트레이터.
    사용자와 대화하며, 하위 부서/직원 에이전트를 동적으로 생성합니다.
    """

    def __init__(self, input_folder="input"):
        print("=" * 50)
        print("  멀티에이전트 연구소 초기화 중...")
        print("=" * 50)

        self.model = SharedModel.get()
        self.input_folder = Path(input_folder)
        self.input_folder.mkdir(parents=True, exist_ok=True)

        self.ceo = Agent(
            agent_id="ceo",
            name="대표이사",
            role="작업 분배 및 종합",
            system_prompt=CEO_SYSTEM,
            icon="🏢",
            max_history=3,
        )

        print("  🏢 대표이사 에이전트 준비 완료")
        for key, dept in DEPARTMENTS.items():
            print(f"  {dept['icon']} {dept['name']} 대기")
        print("=" * 50)
        print("  연구소 준비 완료!")
        print("=" * 50)

    def process(self, user_message, uploaded_files=None):
        """
        메인 처리 루프. 제너레이터로 진행 상황을 단계별 yield.

        각 yield:
          {"phase": str, "agent": str, "role": str, "content": str, "tree": str}
        """
        # 이전 부서 에이전트 정리 (CEO 히스토리는 대화 연속성 유지)
        for child in self.ceo.children:
            child.clear()
        self.ceo.children = []

        # 1. 파일 스캔
        file_infos = FileReader.scan_folder(self.input_folder)
        if uploaded_files:
            for path in uploaded_files:
                try:
                    file_infos.append(FileReader.read_file(path))
                except Exception:
                    pass

        manifest = FileReader.build_manifest(file_infos)
        yield self._update("준비", self.ceo, f"파일 {len(file_infos)}개 확인")

        # 2. CEO가 업무 배정 결정
        self.ceo.task_description = "업무 분석 중"
        assignment_prompt = TASK_ASSIGNMENT_TEMPLATE.format(
            user_message=user_message,
            file_manifest=manifest,
        )
        plan = self.ceo.respond(assignment_prompt)
        yield self._update("업무 배정", self.ceo, plan)

        # 3. 배정 결과 파싱
        assignments = self._parse_assignments(plan)

        if not assignments:
            # 직접 답변 모드
            yield from self._direct_response(user_message, file_infos)
        else:
            # 부서별 실행 + 종합
            yield from self._execute_departments(assignments, file_infos, user_message)

        self.model.clean_memory()

    # ── 파싱 ──────────────────────────────────────────────

    def _parse_assignments(self, plan_text):
        """
        CEO 응답에서 부서 배정을 파싱합니다.
        형식: [배정] 부서코드 | 업무: 설명 | 파일: 파일명
        """
        if "[직접답변]" in plan_text:
            return []

        assignments = []
        pattern = r'\[배정\]\s*(\w+)\s*\|\s*업무:\s*(.+?)(?:\|\s*파일:\s*(.+?))?$'
        for line in plan_text.split("\n"):
            m = re.match(pattern, line.strip())
            if m:
                dept_code = m.group(1).strip()
                task_desc = m.group(2).strip()
                files = [f.strip() for f in m.group(3).split(",")] if m.group(3) else []

                if dept_code in DEPARTMENTS:
                    assignments.append({
                        "dept": dept_code,
                        "task": task_desc,
                        "files": files,
                    })

        # 파싱 실패시 직접답변 폴백
        if not assignments:
            return []

        return assignments

    # ── 직접 답변 ────────────────────────────────────────

    def _direct_response(self, user_message, file_infos):
        """CEO가 직접 답변합니다."""
        self.ceo.task_description = "직접 답변 작성 중"
        file_context = FileReader.get_content(file_infos) if file_infos else ""
        prompt = DIRECT_RESPONSE_TEMPLATE.format(
            user_message=user_message,
            file_context=file_context,
        )
        response = self.ceo.respond(prompt)
        yield self._update("답변", self.ceo, response)

    # ── 부서 실행 ────────────────────────────────────────

    def _execute_departments(self, assignments, file_infos, original_question):
        """부서장 에이전트를 생성하고 업무를 수행합니다."""
        dept_results = []

        for assignment in assignments:
            dept_code = assignment["dept"]
            dept_info = DEPARTMENTS[dept_code]

            # 부서장 에이전트 생성
            head = self.ceo.spawn_child(
                name=f"{dept_info['name']} 부장",
                role=dept_info["name"],
                system_prompt=dept_info["head_system"],
                icon=dept_info["icon"],
            )
            head.task_description = assignment["task"]
            yield self._update("부서 배정", head, f"업무: {assignment['task']}")

            # 부서장이 업무 수행
            result = yield from self._run_department(
                head, assignment, dept_info, file_infos
            )
            dept_results.append((head.display_name, result))

            self.model.clean_memory()

        # CEO가 종합
        self.ceo.task_description = "최종 보고 종합 중"
        results_text = "\n\n".join(
            f"[{name}]\n{result}" for name, result in dept_results
        )
        synthesis_prompt = SYNTHESIS_TEMPLATE.format(
            question=original_question,
            dept_results=results_text,
        )
        final = self.ceo.respond(synthesis_prompt)
        yield self._update("최종 보고", self.ceo, final)

    def _run_department(self, head, assignment, dept_info, file_infos):
        """
        부서장이 업무를 수행합니다.
        복잡하면 팀원에게 위임, 아니면 직접 처리.
        """
        file_content = FileReader.get_content(
            file_infos,
            filenames=assignment["files"] if assignment["files"] else None,
        )
        member_codes = ", ".join(dept_info["members"].keys())

        prompt = DEPT_HEAD_TASK_TEMPLATE.format(
            task_description=assignment["task"],
            file_content=file_content,
            member_codes=member_codes,
        )
        head_response = head.respond(prompt)
        yield self._update("분석 중", head, head_response)

        # 위임 여부 확인
        delegations = self._parse_delegations(head_response, dept_info)

        if delegations:
            # 팀원에게 위임
            staff_results = []
            for delegation in delegations:
                member_key = delegation["member"]
                member_info = dept_info["members"][member_key]

                staff = head.spawn_child(
                    name=member_info["name"],
                    role=member_info["name"],
                    system_prompt=member_info["system"],
                    icon=member_info["icon"],
                )
                staff.task_description = delegation["task"]
                yield self._update("직원 배정", staff, f"업무: {delegation['task']}")

                staff_prompt = STAFF_TASK_TEMPLATE.format(
                    task_description=delegation["task"],
                    file_content=file_content,
                )
                staff_result = staff.respond(staff_prompt)
                staff_results.append((staff.display_name, staff_result))
                yield self._update("보고", staff, staff_result)

                self.model.clean_memory()

            # 부서장이 팀원 결과 종합
            head.task_description = "팀 결과 종합 중"
            team_text = "\n\n".join(
                f"[{name}] {result}" for name, result in staff_results
            )
            synthesis = head.respond(
                f"팀원들의 보고를 종합하여 부서 최종 결과를 작성하세요:\n\n{team_text}"
            )
            yield self._update("부서 종합", head, synthesis)
            return synthesis
        else:
            # 부서장이 직접 처리한 결과 반환
            return head_response

    def _parse_delegations(self, head_response, dept_info):
        """부서장 응답에서 팀원 위임을 파싱합니다."""
        delegations = []
        pattern = r'\[위임\]\s*(\w+)\s*\|\s*업무:\s*(.+?)$'
        for line in head_response.split("\n"):
            m = re.match(pattern, line.strip())
            if m:
                member_key = m.group(1).strip()
                task = m.group(2).strip()
                if member_key in dept_info["members"]:
                    delegations.append({"member": member_key, "task": task})
        return delegations

    # ── 유틸리티 ────────────────────────────────────────

    def _update(self, phase, agent, content):
        """UI에 전달할 진행 상황 딕셔너리를 생성합니다."""
        return {
            "phase": phase,
            "agent_name": agent.display_name,
            "agent_role": agent.role,
            "agent_title": agent.title,
            "content": content,
            "tree": self.ceo.get_tree(),
        }

    def clear(self):
        """모든 상태를 초기화합니다."""
        self.ceo.clear()
        self.model.clean_memory()
