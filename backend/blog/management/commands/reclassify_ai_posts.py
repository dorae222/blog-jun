"""
AI/ML 부모 카테고리에 직접 할당된 포스트를 올바른 서브카테고리로 재분류.
papers.csv category 기준 매핑 사용.

사용법:
    python manage.py reclassify_ai_posts --dry-run
    python manage.py reclassify_ai_posts
"""
from django.core.management.base import BaseCommand

from blog.models import Category, Post


# papers.csv / content.json category → 7개 서브카테고리 slug
CATEGORY_SLUG_MAP = {
    'transformer': 'llm',
    'nlp':         'llm',
    'llm':         'llm',
    'vision':      'vision',
    'multimodal':  'multimodal',
    'ssm':         'ssm',
    'diffusion':   'diffusion',
    'moe':         'technique',
    'scaling':     'technique',
    'efficiency':  'technique',
    'alignment':   'technique',
    'finetuning':  'technique',
    'rag':         'technique',
    'retrieval':   'technique',
    'technique':   'technique',
    'prompting':   'technique',
    'icl':         'technique',
    'benchmark':   'technique',
    'evaluation':  'technique',
    'agents':      'agent',
    'tools':       'agent',
    'data':        'technique',
    'security':    'technique',
}

# slug → 서브카테고리 직접 매핑 (papers.csv 57개 기준)
SLUG_TO_SUBCATEGORY = {
    # transformer / nlp / llm → llm
    'attention-is-all-you-need': 'llm',
    'bert-pre-training-of-deep-bidirectional-transformers': 'llm',
    'language-models-are-few-shot-learners-gpt-3': 'llm',
    'llama-open-and-efficient-foundation-language-models': 'llm',
    'llama-2-open-foundation-and-fine-tuned-chat-models': 'llm',
    'mistral-7b': 'llm',
    'qwen2-technical-report': 'llm',
    'qwen25-technical-report': 'llm',
    'yi-open-foundation-models-by-01ai': 'llm',
    'gemma-open-models-based-on-gemini': 'llm',
    'phi-3-technical-report': 'llm',
    'olmo-accelerating-the-science-of-language-models': 'llm',
    'on-layer-normalization-in-the-transformer-architecture': 'llm',
    'sheared-llama-accelerating-language-model-pre-training-via-structured-pruning': 'llm',
    'what-language-model-architecture-and-pretraining-objective-work-best-for-zero-shot-generalization': 'llm',
    # moe → technique
    'mixtral-of-experts': 'technique',
    'deepseek-v2-a-strong-and-economical-mixture-of-experts': 'technique',
    'deepseek-v3-technical-report': 'technique',
    'switch-transformers-scaling-to-trillion-parameter-models-with-simple-and-efficient-sparsity': 'technique',
    'a-review-of-sparse-expert-models-in-deep-learning': 'technique',
    # scaling → technique
    'scaling-laws-for-neural-language-models': 'technique',
    'training-compute-optimal-large-language-models-chinchilla': 'technique',
    'scaling-data-constrained-language-models': 'technique',
    # technique / efficiency → technique
    'roformer-enhanced-transformer-with-rotary-position-embedding': 'technique',
    'gqa-training-generalized-multi-query-transformer-models': 'technique',
    'flashattention-fast-and-memory-efficient-exact-attention': 'technique',
    'flashattention-2-faster-attention-with-better-parallelism': 'technique',
    'lora-low-rank-adaptation-of-large-language-models': 'technique',
    'qlora-efficient-finetuning-of-quantized-llms': 'technique',
    'fast-inference-from-transformers-via-speculative-decoding': 'technique',
    'efficient-memory-management-for-large-language-model-serving-with-pagedattention': 'technique',
    # alignment → technique
    'training-language-models-to-follow-instructions-instructgpt': 'technique',
    'constitutional-ai-harmlessness-from-ai-feedback': 'technique',
    'direct-preference-optimization-dpo': 'technique',
    'training-a-helpful-and-harmless-assistant-with-reinforcement-learning-from-human-feedback': 'technique',
    # rag / retrieval → technique
    'retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks': 'technique',
    'self-rag-learning-to-retrieve-generate-and-critique': 'technique',
    'realm-retrieval-augmented-language-model-pre-training': 'technique',
    'in-context-retrieval-augmented-language-models': 'technique',
    # prompting / icl → technique
    'rethinking-the-role-of-demonstrations-what-makes-in-context-learning-work': 'technique',
    'multitask-prompted-training-enables-zero-shot-task-generalization': 'technique',
    'finetuned-language-models-are-zero-shot-learners': 'technique',
    'scaling-instruction-finetuned-language-models': 'technique',
    'chain-of-thought-prompting-elicits-reasoning-in-large-language-models': 'technique',
    # benchmark / evaluation → technique
    'ares-an-automated-evaluation-framework-for-retrieval-augmented-generation-systems': 'technique',
    'chatbot-arena-an-open-platform-for-evaluating-llms-by-human-preference': 'technique',
    'agentbench-evaluating-llms-as-agents': 'technique',
    'megaverse-benchmarking-large-language-models-across-languages-modalities-models-and-tasks': 'technique',
    # vision → vision
    'an-image-is-worth-16x16-words-vit': 'vision',
    # multimodal → multimodal
    'llava-visual-instruction-tuning': 'multimodal',
    # ssm → ssm
    'mamba-linear-time-sequence-modeling-with-selective-state-spaces': 'ssm',
    'jamba-a-hybrid-transformer-mamba-language-model': 'ssm',
    # agents / tools → agent
    'logic-lm-empowering-large-language-models-with-symbolic-solvers': 'agent',
    'toolformer-language-models-can-teach-themselves-to-use-tools': 'agent',
    'self-rewarding-language-models': 'agent',
    # data / security → technique
    'detecting-pretraining-data-from-large-language-models': 'technique',
    'scalable-extraction-of-training-data-from-production-language-models': 'technique',
    # 실제 DB slug 매핑 (축약형)
    'training-helpful-harmless': 'technique',
    'chain-of-thought': 'technique',
    'scaling-instruction-finetuning': 'technique',
    'self-rewarding-lm': 'agent',
    'toolformer': 'agent',
    'instructgpt': 'technique',
    'megaverse': 'technique',
    'agentbench': 'technique',
    'chatbot-arena': 'technique',
    'flan': 'technique',
    'multitask-prompted-training': 'technique',
    'rethinking-demonstrations': 'technique',
    'ares-rag-eval': 'technique',
    'in-context-ralm': 'technique',
    'realm': 'technique',
    'scaling-data-constrained': 'technique',
    'sparse-expert-models': 'technique',
    'switch-transformers': 'technique',
    'paged-attention': 'technique',
    'speculative-decoding': 'technique',
    'logic-lm': 'agent',
    'dpo': 'technique',
    'constitutional-ai': 'technique',
    'self-rag': 'technique',
    'rag': 'technique',
    'roformer-rope': 'technique',
    'chinchilla': 'technique',
    'scaling-laws': 'technique',
}


class Command(BaseCommand):
    help = "AI/ML 포스트를 올바른 서브카테고리로 재분류"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 미리보기',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        prefix = "[DRY-RUN] " if dry_run else ""

        # AI/ML 부모 카테고리
        try:
            ai_parent = Category.objects.get(slug='ai-ml')
        except Category.DoesNotExist:
            self.stderr.write("AI/ML 카테고리(slug='ai-ml')가 없습니다. seed_ai_categories를 먼저 실행하세요.")
            return

        # 서브카테고리 로드
        sub_cats = {cat.slug: cat for cat in Category.objects.filter(parent=ai_parent)}
        self.stdout.write(f"서브카테고리: {list(sub_cats.keys())}")

        # AI/ML 부모 + 모든 하위 카테고리의 포스트 조회
        all_ai_cats = [ai_parent] + list(sub_cats.values())
        posts = Post.objects.filter(category__in=all_ai_cats)

        moved = 0
        already_correct = 0
        unmapped = 0

        self.stdout.write(f"\n{prefix}reclassify_ai_posts 시작 (총 {posts.count()}개 포스트)")
        self.stdout.write("=" * 60)

        for post in posts:
            # slug 기반 매핑 먼저 시도
            target_slug = SLUG_TO_SUBCATEGORY.get(post.slug)

            if not target_slug:
                # content.json의 category/sub_category 필드 기반 fallback
                # 현재 카테고리가 이미 서브카테고리인지 확인
                if post.category.slug in sub_cats and post.category != ai_parent:
                    already_correct += 1
                    continue
                unmapped += 1
                self.stdout.write(f"  [UNMAPPED] {post.slug} (현재: {post.category.slug})")
                continue

            target_cat = sub_cats.get(target_slug)
            if not target_cat:
                self.stdout.write(f"  [WARN] 서브카테고리 '{target_slug}' 없음: {post.slug}")
                continue

            if post.category == target_cat:
                already_correct += 1
                continue

            old_cat = post.category.slug
            if not dry_run:
                post.category = target_cat
                post.save(update_fields=['category'])

            moved += 1
            self.stdout.write(f"  {prefix}[MOVE] {post.slug}: {old_cat} → {target_slug}")

        self.stdout.write("=" * 60)
        self.stdout.write(
            f"{prefix}완료: {moved}개 이동, {already_correct}개 정상, {unmapped}개 매핑없음"
        )
