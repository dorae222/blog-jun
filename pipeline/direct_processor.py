"""
Direct File Processor - Claude Code가 직접 파일을 읽고 정제하는 파이프라인 코디네이터.
처리 대상 파일 목록 관리, 진행 추적, batch_output.jsonl 누적 기록.

사용법:
    python pipeline/direct_processor.py list        # 남은 파일 목록 출력
    python pipeline/direct_processor.py status      # 진행 현황 출력
    python pipeline/direct_processor.py write <id> <json>  # 처리 결과 기록
    python pipeline/direct_processor.py skip <id>   # 파일 스킵 표시
"""
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
PROGRESS_FILE = DATA_DIR / "processing_progress.json"
OUTPUT_FILE = DATA_DIR / "batch_output.jsonl"

# ──────────────────────────────────────────────────────────────────────────────
# 처리 대상 파일 목록 (처리 순서 순)
# custom_id: "카테고리/서브카테고리/파일명" (batch_import.py와 매핑되는 상대 키)
# src: 실제 파일 절대 경로
# ──────────────────────────────────────────────────────────────────────────────
DOWNLOADS = Path("/Users/dorae222/Downloads")
MY_PAGE = DOWNLOADS / "my page" / "[My Page]"
PORTFOLIO = DOWNLOADS / "portfolio notion export" / "포트폴리오"

FILE_QUEUE = [
    # ── 1. 40.DEV ──────────────────────────────────────────────────────────
    {
        "custom_id": "40.DEV/41.Backend/Django 기초.md",
        "src": MY_PAGE / "[Front+Back]" / "Django 기초 0bbacb14a8da40b49a319ee6a454b3ad.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Django.md",
        "src": MY_PAGE / "[Front+Back]" / "Django 67d93e25c7dc42e2b3bf0925fed1393b.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Cookie Token Session JWT.md",
        "src": MY_PAGE / "[Front+Back]" / "Cookie↔Token & Session↔JWT f77c216169234d388ca469fbe9f5a89a.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Servlet JSP.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP b9981df704954911a2a63ba463b7f524.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Servlet LifeCycle.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP" / "Servlet LifeCycle ef5360aa8806432e838839ea80c32c85.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Tomcat Servlet.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP" / "Tomcat, Servlet 698cfc07b1964f2d81977fa8a1f33f32.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/JSP.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP" / "JSP 4ea2481491c749a0aab66d69250bc08d.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Cookie and Session.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP" / "Cookie & Session 85c9b41d9d9a4a24bf21ee2d01a37afd.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/Expression Language.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP" / "Expression Language 1bab8b09750145bca58ff9c9739548b0.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/41.Backend/JSP MySQL.md",
        "src": MY_PAGE / "[Front+Back]" / "Servlet & JSP" / "JSP - MySQL 연동 34af8e471643438ba11e8d4f28f80c08.md",
        "category": "40.DEV", "sub": "41.Backend",
    },
    {
        "custom_id": "40.DEV/42.Git/Git.md",
        "src": MY_PAGE / "[Etc]" / "Git 37627f8feec84272aef75cec762da5af.md",
        "category": "40.DEV", "sub": "42.Git",
    },
    {
        "custom_id": "40.DEV/43.Linux/LINUX_UBUNTU.md",
        "src": MY_PAGE / "[Etc]" / "LINUX_UBUNTU 0af9dd1ed1b54262867cc8d5f535c646.md",
        "category": "40.DEV", "sub": "43.Linux",
    },

    # ── 2. 33.Database ──────────────────────────────────────────────────────
    {
        "custom_id": "33.Database/MongoDB.md",
        "src": MY_PAGE / "[Front+Back]" / "[MongoDB]" / "MongoDB를 활용한 사용자 회원 정보 프로그램 36e169706fec41d9bb0276c3036b84ca.md",
        "category": "33.Database", "sub": "MongoDB",
    },
    {
        "custom_id": "33.Database/MongoDB 쿼리 연습.md",
        "src": MY_PAGE / "[Front+Back]" / "[MongoDB]" / "쿼리 연습문제 19347ae60e604be28cb882264242c5f2.md",
        "category": "33.Database", "sub": "MongoDB",
    },

    # ── 3. 30.Data ──────────────────────────────────────────────────────────
    {
        "custom_id": "30.Data/Big Data Introduction.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[What is Big Data ] ca7c26d6d5184ef4a0f893528a99ef92.md",
        "category": "30.Data", "sub": "Big Data",
    },
    {
        "custom_id": "30.Data/Hadoop.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[Hadoop] 81e413ea5d474ad6b2599e81d88516ea.md",
        "category": "30.Data", "sub": "Hadoop",
    },
    {
        "custom_id": "30.Data/HIVE.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[HIVE] 6999f8988dbf479b8c6ebe45302b9915.md",
        "category": "30.Data", "sub": "Hadoop",
    },
    {
        "custom_id": "30.Data/Pig.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[Pig] 0a44e2ccea1341f7bf1ee8dcbe153826.md",
        "category": "30.Data", "sub": "Hadoop",
    },
    {
        "custom_id": "30.Data/Spark.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[Spark] 4e4d11f0fe80440898194570cc38fa0d.md",
        "category": "30.Data", "sub": "Spark",
    },
    {
        "custom_id": "30.Data/SQOOP.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[SQOOP] f8e7cd5397144f7fa38f33c9a7bed067.md",
        "category": "30.Data", "sub": "Hadoop",
    },
    {
        "custom_id": "30.Data/빅데이터 수집 및 시각화.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[빅데이터 수집 및 시각화] 327dede2828e49078cc19da132652fce.md",
        "category": "30.Data", "sub": "Big Data",
    },
    {
        "custom_id": "30.Data/하둡 완전분산모드.md",
        "src": MY_PAGE / "[Big Data Solution]" / "[하둡완전분산모드] ba16e78affe2495f9deac22a6eedc029.md",
        "category": "30.Data", "sub": "Hadoop",
    },

    # ── 4. 20.AI ────────────────────────────────────────────────────────────
    {
        "custom_id": "20.AI/23.DL Basic/Lv1 Deep Learning Basic.md",
        "src": MY_PAGE / "[ML & DL]" / "[ Deep Learning ]" / "[Lv1]Basic for Deep Learning d47b7693e9dd4cbcbaba5e12b7306c7a.md",
        "category": "20.AI", "sub": "23.DL Basic",
    },
    {
        "custom_id": "20.AI/23.DL Basic/Lv2 Beginning for Deep Learning.md",
        "src": MY_PAGE / "[ML & DL]" / "[ Deep Learning ]" / "[Lv2]Beginning for Deep Learning 1eaa1d1309f24d75b9ff8841278c7a08.md",
        "category": "20.AI", "sub": "23.DL Basic",
    },
    {
        "custom_id": "20.AI/23.DL Basic/Lv2 Basic for NLP.md",
        "src": MY_PAGE / "[ML & DL]" / "[ Deep Learning ]" / "[Lv2]Basic for NLP 0fc8d1fb72cc4e449a62d989d72b8d79.md",
        "category": "20.AI", "sub": "23.DL Basic",
    },
    {
        "custom_id": "20.AI/23.DL Basic/Lv3 Natural Language Generation.md",
        "src": MY_PAGE / "[ML & DL]" / "[ Deep Learning ]" / "[Lv3]Natural Language Genration(NLG) a88d69405e4941e2a84831b82d2581ae.md",
        "category": "20.AI", "sub": "23.DL Basic",
    },
    {
        "custom_id": "20.AI/23.DL Basic/Lv4 NLP with BERT GPT.md",
        "src": MY_PAGE / "[ML & DL]" / "[ Deep Learning ]" / "[Lv4]NLP with BERT, GPT-3 7fa91f050d054567ad5eeb5b4d3abcb5.md",
        "category": "20.AI", "sub": "23.DL Basic",
    },
    {
        "custom_id": "20.AI/28.Paper Review/GAN.md",
        "src": MY_PAGE / "[ML & DL]" / "Paper Review" / "[2014] GAN Genrative Adversarial Nets afd3d3c7feaf4cf789c791773dbd12be.md",
        "category": "20.AI", "sub": "28.Paper Review",
    },
    {
        "custom_id": "20.AI/28.Paper Review/BERT.md",
        "src": MY_PAGE / "[ML & DL]" / "Paper Review" / "[2018] BERT Pre-training of Deep Bidirectional Tra f30ad7a1358f42cf90aae3b41a40c234.md",
        "category": "20.AI", "sub": "28.Paper Review",
    },
    {
        "custom_id": "20.AI/28.Paper Review/ViT.md",
        "src": MY_PAGE / "[ML & DL]" / "Paper Review" / "[2021] AN IMAGE IS WORTH 16X16 WORDS TRANSFORMERS  a18c337c38de4618b9cca8ee77d2ac42.md",
        "category": "20.AI", "sub": "28.Paper Review",
    },
    {
        "custom_id": "20.AI/28.Paper Review/Diffusion Gen AI Advanced.md",
        "src": MY_PAGE / "[ML & DL]" / "Paper Review" / "[Diffusion] Gen AI Advanced c32b98575f88443ba32a49cc7d8462c1.md",
        "category": "20.AI", "sub": "28.Paper Review",
    },
    {
        "custom_id": "20.AI/28.Paper Review/UMAP PaCMAP.md",
        "src": MY_PAGE / "[ML & DL]" / "Paper Review" / "UMAP&PaCMAP f4c954a6c7db498689f64a31c68f5031.md",
        "category": "20.AI", "sub": "28.Paper Review",
    },

    # ── 5. 60.Project ───────────────────────────────────────────────────────
    {
        "custom_id": "60.Project/인공지능사관학교 최종 프로젝트.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[인공지능사관학교] 최종 프로젝트 303f40608d7681e99bd8ea92c4cc8518.md",
        "category": "60.Project", "sub": "AI Project",
    },
    {
        "custom_id": "60.Project/인공지능사관학교 온라인 해커톤.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[인공지능 사관학교] 온라인 해커톤 303f40608d768119ae1efeab701f2825.md",
        "category": "60.Project", "sub": "AI Project",
    },
    {
        "custom_id": "60.Project/부산 빅데이터 해커톤.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[부산광역시] 부산 BiG data Hackathon 303f40608d76813cbee4e1433b620ee1.md",
        "category": "60.Project", "sub": "AI Project",
    },
    {
        "custom_id": "60.Project/SKT Multi-concept Image Generation.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[SKT] Multi-concept text to image Generation 303f40608d76818b9396f4938f0af3dd.md",
        "category": "60.Project", "sub": "AI Project",
    },
    {
        "custom_id": "60.Project/INTOON.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[Encore] # INTOON 303f40608d7681dc8c3fc0759b4c0700.md",
        "category": "60.Project", "sub": "AI Project",
    },
    {
        "custom_id": "60.Project/한국관광공사 관광부상지역 모니터링.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[한국관광공사] 관광부상지역 모니터링 시스템 303f40608d7681258275cde760ce5af4.md",
        "category": "60.Project", "sub": "AI Project",
    },
    {
        "custom_id": "60.Project/한국관광데이터랩 공모전.md",
        "src": PORTFOLIO / "교외 AI 프로젝트" / "[한국관광공사] 한국관광데이터랩 우수활용사례 공모전 303f40608d7681a28829d7736730b0f2.md",
        "category": "60.Project", "sub": "AI Project",
    },

    # ── 6. 10.Cloud/Docker ──────────────────────────────────────────────────
    # (Obsidian vault에서, 처리 완료 후 추가)
]


def load_progress():
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"completed": [], "skipped": [], "last_processed": None,
            "stats": {"completed": 0, "skipped": 0}}


def save_progress(progress):
    PROGRESS_FILE.write_text(json.dumps(progress, ensure_ascii=False, indent=2))


def get_remaining(progress):
    done = set(progress["completed"] + progress["skipped"])
    return [f for f in FILE_QUEUE if f["custom_id"] not in done]


def cmd_list():
    progress = load_progress()
    remaining = get_remaining(progress)
    print(f"=== 남은 파일: {len(remaining)} / 전체: {len(FILE_QUEUE)} ===")
    for i, f in enumerate(remaining[:20], 1):
        exists = "✓" if Path(f["src"]).exists() else "✗"
        print(f"  {i:2d}. [{exists}] {f['custom_id']}")
    if len(remaining) > 20:
        print(f"  ... 외 {len(remaining)-20}개")


def cmd_status():
    progress = load_progress()
    remaining = get_remaining(progress)
    print(f"완료: {progress['stats']['completed']}, 스킵: {progress['stats']['skipped']}, "
          f"남음: {len(remaining)}, 전체: {len(FILE_QUEUE)}")
    print(f"마지막 처리: {progress['last_processed']}")


def cmd_write(custom_id: str, result_json: str):
    """처리 결과를 batch_output.jsonl에 기록하고 progress 업데이트."""
    progress = load_progress()
    result = json.loads(result_json)

    # batch_output.jsonl 포맷으로 기록
    record = {
        "custom_id": custom_id,
        "response": {
            "status_code": 200,
            "body": {
                "choices": [{"message": {"content": json.dumps(result, ensure_ascii=False)}}]
            }
        }
    }
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # progress 업데이트
    if custom_id not in progress["completed"]:
        progress["completed"].append(custom_id)
        progress["stats"]["completed"] += 1
    progress["last_processed"] = custom_id
    save_progress(progress)
    print(f"✓ 기록 완료: {custom_id}")


def cmd_skip(custom_id: str):
    progress = load_progress()
    if custom_id not in progress["skipped"]:
        progress["skipped"].append(custom_id)
        progress["stats"]["skipped"] += 1
    progress["last_processed"] = custom_id
    save_progress(progress)
    print(f"⊘ 스킵: {custom_id}")


def cmd_next():
    """다음 처리할 파일 경로 출력."""
    progress = load_progress()
    remaining = get_remaining(progress)
    if not remaining:
        print("모든 파일 처리 완료!")
        return
    nxt = remaining[0]
    exists = Path(nxt["src"]).exists()
    print(f"custom_id: {nxt['custom_id']}")
    print(f"src: {nxt['src']}")
    print(f"exists: {exists}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "list":
        cmd_list()
    elif cmd == "status":
        cmd_status()
    elif cmd == "next":
        cmd_next()
    elif cmd == "write" and len(sys.argv) >= 4:
        cmd_write(sys.argv[2], sys.argv[3])
    elif cmd == "skip" and len(sys.argv) >= 3:
        cmd_skip(sys.argv[2])
    else:
        print(__doc__)
