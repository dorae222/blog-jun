# LXD 인프라 + 도메인 계획

> **마지막 업데이트**: 2026-03-01
> **담당**: @dorae222
> **관련 문서**: [CLAUDE.md](../CLAUDE.md)

## 개요
hj-remote 서버의 LXD 컨테이너 인프라. blog-server 배포 완료, vLLM GPU 서버 구축 예정.

## 완료
### B-1. blog.dorae222.com Cloudflare Tunnel ✅
- **완료일**: 2025-02-28
- **내용**:
  - Tunnel ID: `079ef309-aa65-4739-a851-bdcd0a7fb14b`
  - hostname: blog.dorae222.com → http://localhost:80
  - systemd 서비스 등록 완료

### B-3. blog-server 컨테이너 생성 ✅
- **완료일**: 2025-02-28
- **내용**:
  - IP: 10.10.10.30
  - Docker + SSH + cloudflared 설치 완료
  - Docker Compose (db, redis, backend, frontend) 구동 중

## 보류
### 0-1. NVIDIA 드라이버 불일치 수정 ⏸️
- **보류 사유**: vLLM 서버 구축 시 해결
- **선행 조건**: Phase 3 착수 시점
- **우선순위**: P1
- **내용**:
  ```bash
  sudo apt-get install --reinstall nvidia-driver-580
  sudo reboot
  nvidia-smi  # 동작 확인
  ```

### 0-2. HDD 마운트 ⏸️
- **보류 사유**: 즉시 필요하지 않음
- **선행 조건**: 스토리지 필요 시점
- **우선순위**: P2
- **내용**:
  ```bash
  sudo mkdir -p /data
  sudo mount /dev/sda1 /data
  echo '/dev/sda1 /data ext4 defaults 0 2' | sudo tee -a /etc/fstab
  ```

### 0-3. Swap 원인 조사 ⏸️
- **보류 사유**: 현재 안정적 운영 중
- **선행 조건**: 성능 이슈 발생 시
- **우선순위**: P2

## 향후 계획
### B-4. llm-server 컨테이너 생성
- **우선순위**: P1 (중요)
- **예상 규모**: Large
- **내용**: llm-profile.yml 참조, GPU passthrough (RTX 3090 x2)
- **선행 조건**: NVIDIA 드라이버 수정 (0-1)

### B-5. vLLM 배포
- **우선순위**: P1 (중요)
- **예상 규모**: Large
- **내용**: vllm-docker-compose.yml 참조, 모델: Qwen3-32B-AWQ (TP=2)
- **선행 조건**: llm-server 컨테이너 생성 (B-4)

## 리소스 총괄
| | CPU | RAM |
|---|-----|-----|
| 기존 합계 | 52 | 136GB |
| + blog-server | 4 | 8GB |
| + llm-server | 8 | 32GB |
| **총 할당** | **64** | **176GB** |
| **호스트 여유** | 0 (soft) | **76GB** |

## 체크리스트
- [x] blog-server 컨테이너 구축
- [x] Cloudflare Tunnel 설정
- [x] Docker Compose 구동
- [ ] NVIDIA 드라이버 수정
- [ ] llm-server 구축
- [ ] vLLM 배포

## 참고사항
- B-2는 사용하지 않음 (번호 건너뜀)
- CPU 할당이 soft limit이므로 호스트 모니터링 필요
- GPU passthrough는 LXD profile에서 설정
