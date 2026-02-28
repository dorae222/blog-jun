# LXD 인프라 + 도메인 계획

## Phase 0: 인프라 선행 작업 (호스트)

### 0-1. NVIDIA 드라이버 불일치 수정
```bash
sudo apt-get install --reinstall nvidia-driver-580
sudo reboot
nvidia-smi  # 동작 확인
```

### 0-2. HDD 마운트
```bash
sudo mkdir -p /data
# 4x TOSHIBA 2TB HDD 중 하나를 /data에 마운트
sudo mount /dev/sda1 /data
# fstab에 영구 등록
echo '/dev/sda1 /data ext4 defaults 0 2' | sudo tee -a /etc/fstab
```

### 0-3. Swap 원인 조사
```bash
for f in /proc/*/status; do
  awk '/VmSwap/{s=$2} /^Name/{n=$2} END{if(s>0) print s,n}' "$f" 2>/dev/null
done | sort -rn | head -20
```

## Phase 2: 블로그 배포 + 도메인 ✅ 완료

### B-1. blog.dorae222.com Cloudflare Tunnel ✅
- Tunnel ID: `079ef309-aa65-4739-a851-bdcd0a7fb14b`
- hostname: blog.dorae222.com → http://localhost:80
- systemd 서비스 등록 완료

### B-3. blog-server 컨테이너 생성 ✅
- IP: 10.10.10.30
- Docker + SSH + cloudflared 설치 완료
- Docker Compose (db, redis, backend, frontend) 구동 중

## Phase 3: vLLM 인프라

### B-4. llm-server 컨테이너 생성
- llm-profile.yml 참조
- GPU passthrough: RTX 3090 x2

### B-5. vLLM 배포
- vllm-docker-compose.yml 참조
- 모델: Qwen3-32B-AWQ (TP=2)

## 리소스 총괄 (추가 후)
| | CPU | RAM |
|---|-----|-----|
| 기존 합계 | 52 | 136GB |
| + blog-server | 4 | 8GB |
| + llm-server | 8 | 32GB |
| **총 할당** | **64** | **176GB** |
| **호스트 여유** | 0 (soft) | **76GB** |
