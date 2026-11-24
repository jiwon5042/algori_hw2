# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 **고급알고리즘**(SIT2001-01) 과제2의 **시작 저장소**입니다.
채팅창에 묻고 복사·붙여넣기 하던 방식에서 벗어나, Codespace 안의 에이전트가
저장소를 읽고, 파일을 고치고, 테스트를 직접 돌리게 하는 방법을 익힙니다.

- 과제 안내: [lec-algorithm.github.io/lecture/article/hw2-2026](https://lec-algorithm.github.io/lecture/article/hw2-2026/)
- 수업 슬라이드: [lec-algorithm.github.io/lecture/slides/hw2-2026](https://lec-algorithm.github.io/lecture/slides/hw2-2026/)
- 해시 테이블 복습: [주제 08 해시 테이블](https://lec-algorithm.github.io/lecture/course/topic-08-hashing/)

## 시작하기

1. 이 저장소 상단의 **Use this template** → **Create a new repository**
2. 저장소 이름은 `algorithms-hw2`처럼 정합니다. 공개(Public)로 만듭니다.
3. 만들어진 **내 저장소**에서 **Code** → **Codespaces** 탭 → **Create codespace on main**
4. 왼쪽 막대의 Copilot 아이콘을 눌러 채팅 창을 열고, 창 아래쪽에서 **Agent** 모드를 고릅니다.

## 들어 있는 것

| 파일 | 하는 일 |
| --- | --- |
| `SPEC.md` · `PLAN.md` | URL 단축기 명세 초안과 구현 순서 |
| `src/base62.py` | base62 인코딩·디코딩 |
| `src/hash_table.py` · `src/linear_probing.py` | 체이닝·선형 탐지 해시 테이블 |
| `src/shortener.py` · `src/server.py` | URL 단축기와 테이블 조회 화면 |
| `tests/` | 표준 라이브러리 `unittest` 기반 테스트 |
| `experiments/` | 체이닝 탐색 비용 실험과 CSV·SVG·분석 결과 |
| `tools/catchup.sh` | 수업 중 놓친 단계를 따라잡는 스크립트 |
| `Makefile` | `make test` · `make serve` · `make serve-linear` · `make experiment` |

현재 구현은 학습용 초안입니다. `SPEC.md`를 직접 검토하고, 과제 요구사항과
맞지 않는 부분은 구현·테스트와 함께 고칩니다.

## 명령

컨테이너 안(Codespaces 터미널)에서 실행합니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 체이닝 웹 서버 (포트 8000) | `make serve` |
| 선형 탐지 웹 서버 (포트 8001) | `make serve-linear` |
| 충돌 실험·비교 (CSV·SVG·보고서 생성) | `make experiment` |
| 놓친 단계 따라잡기 | `sh tools/catchup.sh <단계 번호>` |

외부 라이브러리는 쓰지 않습니다. Python 표준 모듈만으로 충분합니다.
두 서버는 서로 다른 포트와 메모리 저장소를 사용하므로 동시에 실행해도 데이터가
섞이지 않습니다. 각 서버에서 `/`에 URL을 입력하고 `/table`에서 테이블을
확인합니다. 선형 탐지 서버는 빈 칸을 만나기 전까지 다음 칸들을 차례로
탐색합니다. Codespaces에서는 체이닝 8000, 선형 탐지 8001 포트를 각각 전달해
사용합니다.

## 로컬에서 하기

```sh
git clone https://github.com/<본인 계정>/<내 저장소>.git
cd <내 저장소>
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
