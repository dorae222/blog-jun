<!-- infographic-hero -->
![Reinforcement Learning Basics 핵심 요약](figures/infographic.svg)

*Figure: Reinforcement Learning Basics 한 장 요약 인포그래픽*

## 개요

강화학습(Reinforcement Learning, RL)은 지도학습·비지도학습과 구별되는 제3의 머신러닝 패러다임입니다. **에이전트(Agent)**는 **환경(Environment)**과 반복적으로 상호작용하면서 상태(State)를 관찰하고, 행동(Action)을 선택하며, 그 결과로 **보상(Reward)**을 받습니다. 에이전트의 목표는 단기 보상이 아닌 **누적 할인 보상(Cumulative Discounted Reward)**을 최대화하는 정책(Policy)을 학습하는 것입니다.

강화학습이 주목받는 이유는 명시적인 정답 레이블 없이도 시행착오(Trial & Error)를 통해 스스로 최적 전략을 발견할 수 있다는 점입니다. AlphaGo, OpenAI Five, ChatGPT의 RLHF(인간 피드백 강화학습) 등 현대 AI의 핵심 기술 다수가 강화학습을 기반으로 합니다.

---

## 수학적 배경: 마르코프 결정 과정 (MDP)

강화학습 문제는 **마르코프 결정 과정(Markov Decision Process, MDP)**으로 형식화됩니다.

$$\mathcal{M} = (\mathcal{S},\ \mathcal{A},\ P,\ R,\ \gamma)$$

| 기호 | 의미 |
|------|------|
| $\mathcal{S}$ | 상태 공간 (State Space) |
| $\mathcal{A}$ | 행동 공간 (Action Space) |
| $P(s'\|s,a)$ | 상태 전이 확률 |
| $R(s,a)$ | 보상 함수 |
| $\gamma \in [0,1)$ | 할인율 (Discount Factor) |

**마르코프 가정**: 다음 상태 $s'$는 현재 상태 $s$와 행동 $a$에만 의존하며, 이전 이력에는 무관합니다.

### 가치 함수 (Value Function)

정책 $\pi$ 아래에서 상태 $s$의 가치는 다음과 같이 정의됩니다.

$$V^\pi(s) = \mathbb{E}_\pi\left[\sum_{t=0}^{\infty} \gamma^t R_{t+1} \,\Big|\, S_0 = s\right]$$

이를 재귀적으로 표현한 것이 **벨만 기대 방정식(Bellman Expectation Equation)**입니다.

$$V^\pi(s) = \sum_a \pi(a|s)\left[R(s,a) + \gamma \sum_{s'} P(s'|s,a)\,V^\pi(s')\right]$$

### Q-함수 (Action-Value Function)

상태 $s$에서 행동 $a$를 선택했을 때의 기대 누적 보상을 나타냅니다.

$$Q^\pi(s,a) = R(s,a) + \gamma \sum_{s'} P(s'|s,a) \sum_{a'} \pi(a'|s')\,Q^\pi(s',a')$$

최적 Q-함수 $Q^*(s,a)$를 알면 최적 정책은 $\pi^*(s) = \arg\max_a Q^*(s,a)$로 바로 도출됩니다.

---

![에이전트-환경 상호작용: 에이전트가 환경과 상태-행동-보상 루프를 통해 학습하는 과정](figures/agent_environment_interaction.png)
*에이전트-환경 상호작용: 에이전트는 현재 상태를 관찰하고, 행동을 선택하며, 환경으로부터 보상과 다음 상태를 받는 순환 과정을 반복한다.*

## 핵심 알고리즘

### 1. Q-Learning (Off-Policy TD)

환경 모델 없이 Q-함수를 직접 학습하는 **모델-프리(Model-Free)** 방법입니다. 현재 정책과 독립적으로 최적 Q-함수를 업데이트하는 **off-policy** 방식입니다.

$$Q(s,a) \leftarrow Q(s,a) + \alpha\left[r + \gamma \max_{a'} Q(s',a') - Q(s,a)\right]$$

### 2. SARSA (On-Policy TD)

Q-Learning과 유사하지만, 다음 행동 $a'$을 실제 정책에서 샘플링하는 **on-policy** 방식입니다.

$$Q(s,a) \leftarrow Q(s,a) + \alpha\left[r + \gamma\, Q(s',a') - Q(s,a)\right]$$

SARSA는 탐색 중 발생하는 위험한 행동의 페널티를 학습에 반영하므로, 안전이 중요한 환경에서 더 보수적인 정책을 형성합니다.

### 3. Policy Gradient (REINFORCE)

가치 함수 추정 없이 정책 $\pi_\theta$를 직접 파라미터화하여 기울기 상승법으로 최적화합니다.

$$\nabla_\theta J(\theta) = \mathbb{E}_\pi\left[G_t \nabla_\theta \log \pi_\theta(a_t|s_t)\right]$$

연속 행동 공간이나 확률적 정책이 필요한 환경에 적합합니다.

### 4. 탐색-활용 트레이드오프 (ε-greedy)

학습 초기에는 **탐색(Exploration)**을 통해 다양한 상태를 경험하고, 학습이 진행될수록 **활용(Exploitation)**의 비중을 높여야 합니다.

$$a = \begin{cases} \text{무작위 행동} & \text{확률 } \varepsilon \\ \arg\max_a Q(s,a) & \text{확률 } 1-\varepsilon \end{cases}$$

탐색률 $\varepsilon$은 학습이 진행됨에 따라 점진적으로 감소시킵니다 (예: $\varepsilon \leftarrow \varepsilon \cdot 0.995$).

### 5. Deep Q-Network (DQN) 개요

상태 공간이 고차원(예: 픽셀 이미지)인 경우 Q-테이블 대신 신경망으로 Q-함수를 근사합니다.

- **Experience Replay**: 과거 경험 $(s, a, r, s')$을 버퍼에 저장하고 미니배치로 샘플링 → 데이터 상관성 제거
- **Target Network**: 학습 안정성을 위해 주기적으로 업데이트되는 별도의 타겟 네트워크 사용

---

## Python 구현: CartPole Q-Learning

```python
import numpy as np
import gym
import matplotlib.pyplot as plt

# 환경 초기화
env = gym.make('CartPole-v1')

# 하이퍼파라미터
N_EPISODES = 500
ALPHA = 0.1          # 학습률
GAMMA = 0.99         # 할인율
EPSILON_START = 1.0  # 초기 탐색률
EPSILON_END = 0.01   # 최소 탐색률
EPSILON_DECAY = 0.995

# 상태 이산화 (CartPole은 연속 상태공간)
N_BINS = 10
bins = [
    np.linspace(-4.8, 4.8, N_BINS),    # cart position
    np.linspace(-4, 4, N_BINS),         # cart velocity
    np.linspace(-0.418, 0.418, N_BINS), # pole angle
    np.linspace(-4, 4, N_BINS),         # pole angular velocity
]

def discretize(state):
    """연속 상태를 이산 인덱스로 변환"""
    indices = []
    for i, val in enumerate(state):
        idx = np.digitize(val, bins[i]) - 1
        idx = np.clip(idx, 0, N_BINS - 1)
        indices.append(idx)
    return tuple(indices)

# Q-테이블 초기화 (상태 차원: N_BINS^4, 행동 차원: 2)
q_table = np.zeros([N_BINS] * 4 + [env.action_space.n])

epsilon = EPSILON_START
episode_rewards = []
epsilon_history = []

for episode in range(N_EPISODES):
    state, _ = env.reset()
    state = discretize(state)
    total_reward = 0
    done = False

    while not done:
        # ε-greedy 행동 선택
        if np.random.random() < epsilon:
            action = env.action_space.sample()  # 탐색
        else:
            action = np.argmax(q_table[state])  # 활용

        next_state, reward, terminated, truncated, _ = env.step(action)
        done = terminated or truncated
        next_state = discretize(next_state)

        # Q-Learning 업데이트
        best_next = np.max(q_table[next_state])
        td_target = reward + GAMMA * best_next * (not done)
        td_error = td_target - q_table[state][action]
        q_table[state][action] += ALPHA * td_error

        state = next_state
        total_reward += reward

    # 탐색률 감소
    epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
    episode_rewards.append(total_reward)
    epsilon_history.append(epsilon)

    if (episode + 1) % 50 == 0:
        avg = np.mean(episode_rewards[-50:])
        print(f"Episode {episode+1:4d} | Avg Reward: {avg:6.1f} | ε: {epsilon:.3f}")

env.close()
```

<!-- Execution error: ModuleNotFoundError: No module named 'gym' -->

---

![Q-value 그리드월드: 4x4 그리드 환경에서 학습된 Q-value와 최적 정책 시각화](figures/q_value_gridworld.png)
*Q-value 그리드월드: 각 셀의 Q-value 크기와 화살표 방향을 통해 에이전트가 학습한 최적 정책을 직관적으로 파악할 수 있다.*

## 시각화: 학습 보상 곡선 & 탐색률 감소

```python
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# --- (1) 에피소드 보상 곡선 ---
window = 20
rolling_avg = np.convolve(
    episode_rewards,
    np.ones(window) / window,
    mode='valid'
)
axes[0].plot(episode_rewards, alpha=0.3, color='steelblue', label='Episode Reward')
axes[0].plot(
    range(window - 1, len(episode_rewards)),
    rolling_avg,
    color='steelblue', linewidth=2, label=f'{window}-ep Moving Avg'
)
axes[0].axhline(y=195, color='red', linestyle='--', alpha=0.7, label='Solved (195)')
axes[0].set_xlabel('Episode')
axes[0].set_ylabel('Total Reward')
axes[0].set_title('CartPole Q-Learning: Episode Reward')
axes[0].legend()
axes[0].grid(alpha=0.3)

# --- (2) 탐색률 감소 곡선 ---
axes[1].plot(epsilon_history, color='coral', linewidth=2)
axes[1].fill_between(range(len(epsilon_history)), epsilon_history, alpha=0.2, color='coral')
axes[1].set_xlabel('Episode')
axes[1].set_ylabel('Epsilon (ε)')
axes[1].set_title('Exploration Rate (ε) Decay')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('rl_training_curves.png', dpi=150, bbox_inches='tight')
plt.show()
```

<!-- Execution error: NameError: name 'plt' is not defined -->

학습 초반에는 보상이 낮고 불안정하지만, 에피소드가 진행되면서 이동 평균이 상승하고 최종적으로 195점 기준선(CartPole 해결 기준)에 수렴하는 패턴을 확인할 수 있습니다.

---

## 실전 팁

### 언제 강화학습을 사용해야 할까?

강화학습은 다음 조건이 충족될 때 적합합니다.
- **순차적 의사결정**: 현재 행동이 미래 상태에 영향을 미치는 환경
- **명시적 레이블 부재**: 정답이 없고 보상 신호만 존재하는 경우
- **시뮬레이터 또는 환경 존재**: 충분한 경험 데이터를 생성할 수 있는 환경
- 예시: 게임 AI, 로봇 제어, 동적 가격 결정, 자율주행, 광고 입찰

반대로 정적 데이터셋이 있고 지도학습이 가능하다면 굳이 강화학습을 선택할 필요는 없습니다.

### Reward Shaping

희소 보상(Sparse Reward) 환경에서는 학습이 매우 느립니다. **Reward Shaping**은 도메인 지식을 활용해 중간 보상을 추가하여 학습을 가속화합니다.

- CartPole: 폴이 수직에 가까울수록 추가 보상
- 로봇 보행: 목표 방향으로의 이동 거리에 비례한 보상

단, 잘못 설계된 reward shaping은 의도치 않은 행동(reward hacking)을 유발할 수 있으므로 주의가 필요합니다.

### 하이퍼파라미터 조정

| 파라미터 | 권장 시작값 | 영향 |
|---------|------------|------|
| 학습률 $\alpha$ | 0.01 ~ 0.1 | 너무 크면 발산, 너무 작으면 수렴 느림 |
| 할인율 $\gamma$ | 0.95 ~ 0.99 | 클수록 장기 보상 중시 |
| $\varepsilon$ 감소율 | 0.99 ~ 0.999 | 탐색-활용 균형 |
| 배치 크기 (DQN) | 32 ~ 256 | 클수록 안정적, 느림 |
| 리플레이 버퍼 크기 | 10,000 ~ 100,000 | 클수록 다양한 경험 활용 |

### 안정적 학습을 위한 팁

1. **보상 정규화**: 보상을 $[-1, 1]$ 범위로 클리핑하거나 정규화하면 학습 안정성이 향상됩니다.
2. **상태 정규화**: 입력 상태를 표준화(mean=0, std=1)하면 신경망 기반 방법에서 특히 효과적입니다.
3. **점진적 난이도**: 쉬운 환경에서 시작해 점차 난이도를 높이는 **커리큘럼 학습** 활용
4. **시드 고정**: 재현 가능한 실험을 위해 `np.random.seed()`, `env.seed()` 설정
5. **조기 종료 방지**: 탐색 초기에 너무 빨리 $\varepsilon$을 낮추면 지역 최적해에 빠집니다.

---

## 정리

강화학습은 환경과의 상호작용을 통해 최적 정책을 스스로 발견하는 강력한 학습 패러다임입니다. MDP라는 수학적 토대 위에 Q-Learning, SARSA, Policy Gradient 등 다양한 알고리즘이 구축되어 있으며, Deep Q-Network를 통해 고차원 상태 공간으로 확장됩니다. 실제 적용 시에는 보상 설계, 탐색-활용 균형, 하이퍼파라미터 조정이 성능을 좌우하는 핵심 요소임을 기억하세요.