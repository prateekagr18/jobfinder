"""Keyword vocabulary an ATS (and a recruiter skimming for 6 seconds) looks for.

Each canonical keyword maps to a regex of its common spellings, matched on
normalized text at word boundaries (see ``text.contains``). Canonical names are
what the report tells you to add to your resume — use them verbatim, since many
ATS parsers do literal matching and won't equate "k8s" with "Kubernetes".

Extend ``TECH`` / ``LEADERSHIP`` (or ``extra_keywords`` in config.yaml) for your
niche; the scorer only "sees" terms that are in this vocabulary.
"""

from __future__ import annotations

from typing import Dict

from .text import contains, normalize

TECH: Dict[str, str] = {
    # Languages
    "Python": r"python",
    "Java": r"java",
    "Go": r"golang|go(?=\s*(?:,|/|\)|and\b|or\b))",
    "Rust": r"rust",
    "C++": r"c\+\+",
    "C#": r"c#",
    "Kotlin": r"kotlin",
    "Scala": r"scala",
    "Ruby": r"ruby|rails|ruby on rails",
    "TypeScript": r"typescript",
    "JavaScript": r"javascript",
    "SQL": r"sql",
    # Web / backend
    "React": r"react(?:\.js|js)?",
    "Node.js": r"node\.js|nodejs|node",
    "GraphQL": r"graphql",
    "REST APIs": r"restful(?: apis?| services)?|rest(?: ?(?:&|and) ?soap)? (?:apis?|services)",
    "Spring": r"spring(?: boot| framework)?",
    "Hibernate": r"hibernate",
    "gRPC": r"grpc",
    "Microservices": r"micro-?services?",
    "Distributed systems": r"distributed systems?",
    "System design": r"system design|systems design",
    "Scalability": r"scalab(?:le|ility)|high[- ]scale|at scale",
    "Event-driven architecture": r"event[- ]driven",
    # Cloud / infra
    "AWS": r"aws|amazon web services",
    "GCP": r"gcp|google cloud",
    "Azure": r"azure",
    "Kubernetes": r"kubernetes|k8s",
    "Docker": r"docker|containers?",
    "Terraform": r"terraform",
    "CI/CD": r"ci/cd|ci ?/ ?cd|continuous (?:integration|delivery|deployment)",
    "Observability": r"observability|monitoring|datadog|prometheus|grafana",
    "SRE": r"sre|site reliability",
    "Linux": r"linux",
    "Serverless": r"serverless|lambda",
    # Data
    "PostgreSQL": r"postgres(?:ql)?",
    "MySQL": r"mysql",
    "NoSQL": r"nosql|mongodb|dynamodb|cassandra",
    "Redis": r"redis",
    "Kafka": r"kafka",
    "Spark": r"spark",
    "Data pipelines": r"data pipelines?|etl|elt",
    "Snowflake": r"snowflake",
    "Airflow": r"airflow",
    "Oracle": r"oracle",
    "Hive": r"hive",
    # Domain
    "Business intelligence": r"business intelligence|bi",
    "Analytics": r"analytics",
    "Reporting": r"reporting|reports?",
    "Data visualization": r"data visuali[sz]ation|dashboards?",
    "Data platform": r"data platforms?",
    "Enterprise SaaS": r"saas|enterprise software|b2b",
    "A/B testing": r"a/b test(?:ing|s)?|experimentation",
    # ML / AI
    "Machine learning": r"machine learning|ml",
    "LLMs": r"llms?|large language models?|generative ai|genai",
    "AI agents": r"ai agents?|agentic|multi-agent",
    "NLP": r"nlp|natural language processing",
    # Practice
    "Security": r"security|secure coding",
    "Testing": r"unit tests?|testing|tdd|test automation",
    "Performance optimization": r"performance (?:tuning|optimization)|latency",
    "Mobile": r"ios|android|mobile",
}

LEADERSHIP: Dict[str, str] = {
    "People management": r"people management|managing (?:a )?(?:team|engineers)|direct reports|people manager",
    "Hiring": r"hiring|recruit(?:ing|ment)?|interviewing",
    "Mentoring": r"mentor(?:ing|ship|ed)?|coaching|coach",
    "Career development": r"career (?:growth|development)|career ladders?",
    "Performance management": r"performance (?:management|reviews?)|feedback",
    "Technical leadership": r"technical leadership|tech lead|technical direction|lead engineers?",
    "Cross-functional collaboration": r"cross[- ]functional|partner(?:ing)? with product|product and design",
    "Stakeholder management": r"stakeholders?",
    "Roadmap planning": r"roadmaps?|planning|prioritiz(?:ation|e)",
    "Agile": r"agile|scrum|kanban|sprints?",
    "OKRs": r"okrs?|objectives and key results",
    "Execution & delivery": r"execution|deliver(?:y|ing|ed)?|ship(?:ping|ped)?",
    "Architecture": r"architect(?:ure|ural|ing)?",
    "Code review": r"code reviews?",
    "Incident management": r"incident (?:management|response)|on[- ]call|postmortems?",
    "Budget / headcount": r"budget|headcount",
    "Engineering culture": r"engineering culture|culture of|inclusive|diversity",
    "Communication": r"communication|communicat(?:e|or)",
    "Strategy": r"strategy|strategic|vision",
}


def vocabulary(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    """Full keyword map: tech + leadership + any user-supplied ``extra`` terms."""
    vocab = {**TECH, **LEADERSHIP}
    vocab.update(extra or {})
    return vocab


def find_keywords(text: str, vocab: Dict[str, str]) -> Dict[str, int]:
    """Return ``{canonical: count}`` for every vocabulary term present in ``text``."""
    norm = normalize(text)
    hits = {}
    for name, pattern in vocab.items():
        n = contains(norm, pattern)
        if n:
            hits[name] = n
    return hits
