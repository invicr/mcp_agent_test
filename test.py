import asyncio
import os
import logging
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# 로깅 설정
logging.basicConfig(level=logging.ERROR)  # ERROR 레벨 이상의 로그만 출력
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.getenv('GOOGLE_API_KEY')

async def get_tools_async():
    """GitHub MCP 서버에서 도구를 가져옵니다."""
    print("\n" + "="*50)
    print("🔌 MCP GitHub 서버 연결")
    print("="*50)
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")}
        )
    )
    print(f"\n✅ 사용 가능한 도구 목록 ({len(tools)}개):")
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
    return tools, exit_stack

async def get_agent_async():
    """GitHub 파일을 읽기 위한 에이전트를 생성합니다."""
    print("\n" + "="*50)
    print("🤖 Github 에이전트 실행")
    print("="*50)
    tools, exit_stack = await get_tools_async()
    # get_file_contents 도구만 필터링
    filtered_tools = [tool for tool in tools if tool.name == "get_file_contents"]
    if not filtered_tools:
        raise ValueError("get_file_contents 도구를 찾을 수 없습니다.")
    print("\n🔧 사용할 도구:")
    print("- get_file_contents: GitHub 리포지토리에서 파일 내용을 읽어오는 도구")
    agent = LlmAgent(
        model='gemini-2.0-flash',
        name='github_file_reader',
        instruction='You are a helpful assistant that reads files from GitHub repositories using the get_file_contents tool.',
        tools=filtered_tools
    )
    return agent, exit_stack

async def analyze_code_with_llm(code: str) -> str:
    """LLM을 사용하여 코드를 분석하고 레포트를 생성합니다."""
    print("\n" + "="*50)
    print("🔍 코드 분석 에이전트 실행")
    print("="*50)
    session_service = InMemorySessionService()
    session = session_service.create_session(
        state={}, app_name='code_analyzer', user_id='user_fs'
    )
    
    agent = LlmAgent(
        model='gemini-2.0-flash',
        name='code_analyzer',
        instruction="""
        다음 코드를 분석하고 레포트를 작성해주세요.
        다음 항목을 중점적으로 점검하고 한글로 요약해주세요:
        1. 외부 통신 여부 (HTTP, fetch, axios, WebSocket 등)
        2. API 출처의 신뢰성 (공식 API인지 확인)
        3. 보안 취약점
        
        리포트는 다음 포맷을 따르세요:
        - �� 분석 요약
        - 🌐 외부 통신 코드
        - 📦 API 출처 확인 (공식 API 사용 여부)
        - 🛡️ 보안 권고 사항
        
        주의: 함수 호출이나 다른 명령을 사용하지 말고, 순수하게 텍스트로만 응답해주세요.
        """
    )
    
    content = types.Content(role='user', parts=[types.Part(text=code)])
    runner = Runner(
        app_name='code_analyzer',
        agent=agent,
        session_service=session_service
    )
    
    try:
        async for event in runner.run_async(
            session_id=session.id, user_id=session.user_id, new_message=content
        ):
            if hasattr(event, "content") and event.content and event.content.parts:
                part = event.content.parts[0]
                if hasattr(part, "text") and part.text:
                    return part.text.strip()
    except Exception as e:
        print(f"❌ 코드 분석 중 오류 발생: {e}")
        return None

async def test_github_mcp():
    """GitHub MCP 서버를 사용하여 리포지토리의 .ts 파일 내용을 읽어오는 테스트 함수"""
    print("\n" + "="*50)
    print("🚀 테스트 시작")
    print("="*50)
    
    session_service = InMemorySessionService()
    session = session_service.create_session(
        state={}, app_name='github_file_reader', user_id='user_fs'
    )

    # get_file_contents 도구를 사용하는 명령 생성
    command = f"""
    get_file_contents(
        owner="tavily-ai",
        repo="tavily-mcp",
        path="src/index.ts",
        branch="main"
    )
    """
    content = types.Content(role='user', parts=[types.Part(text=command)])
    root_agent, exit_stack = await get_agent_async()

    runner = Runner(
        app_name='github_file_reader',
        agent=root_agent,
        session_service=session_service,
    )

    print("\n" + "="*50)
    print("📂 파일 내용 읽기")
    print("="*50)
    try:
        file_content = None
        async for event in runner.run_async(
            session_id=session.id, user_id=session.user_id, new_message=content
        ):
            if hasattr(event, "tool_request"):
                print(f"\n🔧 도구 호출: {event.tool_request.name}")
                print(f"   📂 인자: {event.tool_request.parameters}\n")
            elif hasattr(event, "tool_response"):
                print(f"✅ 도구 응답 수신 완료 (내용 생략됨)\n")
            elif hasattr(event, "content") and event.content and event.content.parts:
                part = event.content.parts[0]
                if hasattr(part, "text") and part.text:
                    file_content = part.text.strip()
                    print("📄 파일 내용을 성공적으로 읽었습니다.\n")
        
        if file_content:
            analysis_report = await analyze_code_with_llm(file_content)
            if analysis_report:
                print("\n" + "="*50)
                print("📊 분석 결과")
                print("="*50)
                print(analysis_report)
            else:
                print("❌ 코드 분석에 실패했습니다.")
        else:
            print("❌ 파일 내용을 읽을 수 없습니다.")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        print("\n" + "="*50)
        print("🧹 정리")
        print("="*50)
        print("MCP 서버 연결 종료 중...")
        await exit_stack.aclose()
        print("✅ 정리 완료")

if __name__ == '__main__':
    asyncio.run(test_github_mcp()) 