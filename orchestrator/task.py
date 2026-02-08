"""
Orchestrator - CEO 오케스트레이션 핵심 로직 (재귀적 위임)

흐름:
  1. 사용자 메시지 수신 + input/ 파일 스캔
  2. CEO가 업무 배정 결정 (직접답변 or 본부 배정)
  3. 본부장이 업무 수행 (직접 or 팀 배정)
  4. 팀장이 업무 수행 (직접 or 연구원 배정)
  5. 연구원이 직접 실행
  6. 결과가 계층을 따라 역순으로 종합
"""

import re
from pathlib import Path

from .model import SharedModel
from .agent import Agent, MAX_DEPTH
from .file_reader import FileReader
from .departments import (
    CEO_SYSTEM,
    ORGANIZATION,
    CEO_ASSIGNMENT_TEMPLATE,
    DELEGATION_TEMPLATE,
    TASK_TEMPLATE,
    SYNTHESIS_TEMPLATE,
    DIRECT_RESPONSE_TEMPLATE,
)


class Orchestrator:
    """
    대표이사(CEO) 역할의 최상위 오케스트레이터.
    재귀적으로 하위 조직에 업무를 위임합니다.
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
            max_history=5,
        )

        print("  🏢 대표이사 에이전트 준비 완료")
        for key, div in ORGANIZATION.items():
            self._print_org(div, indent=1)
        print("=" * 50)
        print("  연구소 준비 완료!")
        print("=" * 50)

    def _print_org(self, unit, indent):
        print(f"{'  ' * indent}{unit['icon']} {unit['name']} 대기")
        for sub in unit.get("units", {}).values():
            self._print_org(sub, indent + 1)

    def process(self, user_message, uploaded_files=None):
        """
        메인 처리 루프. 제너레이터로 진행 상황을 단계별 yield.
        """
        # 이전 하위 에이전트 정리 (CEO 히스토리는 대화 연속성 유지)
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
        available = ", ".join(ORGANIZATION.keys())
        assignment_prompt = CEO_ASSIGNMENT_TEMPLATE.format(
            user_message=user_message,
            file_manifest=manifest,
            available_units=available,
        )
        plan = self.ceo.respond(assignment_prompt)
        yield self._update("업무 배정", self.ceo, plan)

        # 3. 배정 파싱
        assignments = self._parse_ceo_assignments(plan)

        if not assignments:
            yield from self._direct_response(user_message, file_infos)
        else:
            yield from self._execute_assignments(
                assignments, file_infos, user_message
            )

    # ══════════════════════════════════════════════════════
    # 파싱
    # ══════════════════════════════════════════════════════

    def _parse_ceo_assignments(self, plan_text):
        """CEO 응답에서 본부 배정을 파싱합니다."""
        if "[직접답변]" in plan_text:
            return []

        assignments = []
        pattern = r'\[배정\]\s*(\w+)\s*\|\s*업무:\s*(.+?)(?:\|\s*파일:\s*(.+?))?$'
        for line in plan_text.split("\n"):
            m = re.match(pattern, line.strip())
            if m:
                code = m.group(1).strip()
                task = m.group(2).strip()
                files = [f.strip() for f in m.group(3).split(",")] if m.group(3) else []
                if code in ORGANIZATION:
                    assignments.append({"code": code, "task": task, "files": files})

        return assignments

    def _parse_delegations(self, response_text, available_units):
        """중간 관리자 응답에서 하위 배정을 파싱합니다."""
        delegations = []
        pattern = r'\[배정\]\s*(\w+)\s*\|\s*업무:\s*(.+?)$'
        for line in response_text.split("\n"):
            m = re.match(pattern, line.strip())
            if m:
                code = m.group(1).strip()
                task = m.group(2).strip()
                if code in available_units:
                    delegations.append({"code": code, "task": task})
        return delegations

    # ══════════════════════════════════════════════════════
    # 직접 답변
    # ══════════════════════════════════════════════════════

    def _direct_response(self, user_message, file_infos):
        self.ceo.task_description = "직접 답변 작성 중"
        file_context = FileReader.get_content(file_infos) if file_infos else ""
        prompt = DIRECT_RESPONSE_TEMPLATE.format(
            user_message=user_message,
            file_context=file_context,
        )
        response = self.ceo.respond(prompt)
        yield self._update("답변", self.ceo, response)

    # ══════════════════════════════════════════════════════
    # 재귀적 실행
    # ══════════════════════════════════════════════════════

    def _execute_assignments(self, assignments, file_infos, original_question):
        """CEO 배정을 실행하고 최종 종합합니다."""
        div_results = []

        for assignment in assignments:
            code = assignment["code"]
            org_unit = ORGANIZATION[code]

            # 본부장 생성
            head = self.ceo.spawn_child(
                name=org_unit["name"],
                role=org_unit["name"],
                system_prompt=org_unit["system"],
                icon=org_unit["icon"],
            )
            head.task_description = assignment["task"]
            yield self._update("본부 배정", head, f"업무: {assignment['task']}")

            # 재귀적 실행
            file_content = FileReader.get_content(
                file_infos,
                filenames=assignment["files"] if assignment["files"] else None,
            )
            result = yield from self._run_unit(
                agent=head,
                task_desc=assignment["task"],
                file_content=file_content,
                sub_units=org_unit.get("units", {}),
                original_question=original_question,
            )
            div_results.append((head.display_name, result))

        # CEO 최종 종합
        self.ceo.task_description = "최종 보고 종합 중"
        results_text = "\n\n".join(
            f"[{name}]\n{result}" for name, result in div_results
        )
        final = self.ceo.respond(SYNTHESIS_TEMPLATE.format(
            question=original_question,
            sub_results=results_text,
        ))
        yield self._update("최종 보고", self.ceo, final)

    def _run_unit(self, agent, task_desc, file_content, sub_units, original_question):
        """
        재귀적 업무 실행.

        sub_units가 있으면 → 위임 가능한 중간 관리자
        sub_units가 없으면 → 말단 실행자 (직접 수행)

        Returns: 이 에이전트의 최종 결과 문자열
        """
        if not sub_units:
            # 말단 (연구원): 직접 실행
            prompt = TASK_TEMPLATE.format(
                task_description=task_desc,
                file_content=file_content,
            )
            result = agent.respond(prompt)
            yield self._update("보고", agent, result)
            return result

        # 중간 관리자: 위임 또는 직접 처리 결정
        available = ", ".join(sub_units.keys())
        prompt = DELEGATION_TEMPLATE.format(
            task_description=task_desc,
            file_content=file_content,
            available_units=available,
        )
        response = agent.respond(prompt)
        yield self._update("분석 중", agent, response)

        # 위임 파싱
        delegations = self._parse_delegations(response, sub_units)

        if not delegations:
            # 직접 처리 완료
            return response

        # 하위 에이전트에 위임
        sub_results = []
        for delegation in delegations:
            sub_code = delegation["code"]
            sub_info = sub_units[sub_code]

            child = agent.spawn_child(
                name=sub_info["name"],
                role=sub_info["name"],
                system_prompt=sub_info["system"],
                icon=sub_info["icon"],
            )
            child.task_description = delegation["task"]
            yield self._update("배정", child, f"업무: {delegation['task']}")

            # 재귀 호출
            child_result = yield from self._run_unit(
                agent=child,
                task_desc=delegation["task"],
                file_content=file_content,
                sub_units=sub_info.get("units", {}),
                original_question=original_question,
            )
            sub_results.append((child.display_name, child_result))

        # 하위 결과 종합
        agent.task_description = "결과 종합 중"
        team_text = "\n\n".join(
            f"[{name}]\n{result}" for name, result in sub_results
        )
        synthesis = agent.respond(SYNTHESIS_TEMPLATE.format(
            question=original_question,
            sub_results=team_text,
        ))
        yield self._update("종합", agent, synthesis)
        return synthesis

    # ══════════════════════════════════════════════════════
    # 유틸리티
    # ══════════════════════════════════════════════════════

    def _update(self, phase, agent, content):
        return {
            "phase": phase,
            "agent_name": agent.display_name,
            "agent_role": agent.role,
            "agent_title": agent.title,
            "content": content,
            "tree": self.ceo.get_tree(),
        }

    def clear(self):
        self.ceo.clear()
