---
description: Set up docs-dashboard for the current project's docs/ folder
user_invocable: true
---

# /setup-docs-dashboard

프로젝트의 docs/ 폴더를 위한 웹 대시보드를 설정하고 실행합니다.

## Steps

1. docs-dashboard 리포 확인 및 clone

```bash
if [ ! -f ~/work/docs-dashboard/docker-compose.yml ]; then
    git clone https://github.com/YOUR_USER/docs-dashboard.git ~/work/docs-dashboard
fi
```

2. 현재 프로젝트의 docs/ 폴더 확인

```bash
ls docs/ 2>/dev/null
```

docs/ 폴더가 없으면 사용자에게 경로를 확인하세요.

3. setup.sh 실행

```bash
cd ~/work/docs-dashboard
./setup.sh "$(pwd)/docs" "$(basename $(pwd))"
```

- 첫 번째 인자: 현재 프로젝트의 docs/ 절대 경로
- 두 번째 인자: 프로젝트 이름 (디렉토리명 사용)

4. Docker Compose 실행

```bash
cd ~/work/docs-dashboard && docker compose up -d --build
```

5. 사용자에게 접속 URL 안내: http://localhost:15000

## Additional Commands

- 대시보드 중지: `cd ~/work/docs-dashboard && docker compose down`
- 대시보드 재시작: `cd ~/work/docs-dashboard && docker compose up -d`
- 다른 프로젝트로 전환: `./setup.sh /other/project/docs other-project && docker compose up -d --build`

## Category Customization

프로젝트의 docs/ 폴더에 `.docs-dashboard.json`을 생성하면 카테고리를 커스텀할 수 있습니다:

```json
{
  "categories": {
    "Architecture": ["architecture", "design"],
    "Reports": ["report", "analysis"]
  }
}
```

설정 파일이 없으면 하위 폴더명으로 자동 분류됩니다.
