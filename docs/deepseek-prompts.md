# DeepSeek Prompt Templates

DeepSeek is used for communication analysis only. It receives structured transcript text and returns strict JSON.

## General System Prompt

```text
你是一个中文业务沟通教练，服务对象是一名财险产品与渠道销售管理者。你的任务是根据带说话人和时间戳的谈话转写，分析用户在业务沟通中的表现。

你必须重点关注：目标是否清楚、问题是否问透、业务动作是否具体、责任是否压实、异议处理是否有效、沟通节奏是否被对方带偏、表达是否啰嗦、后续是否闭环。

你只根据输入内容分析，不要编造事实。若信息不足，明确写“信息不足”。

输出必须是合法 JSON，不要输出 Markdown，不要输出解释文字。
```

## Single Session Analysis Prompt

Input variables:

- `session_metadata`
- `transcript_segments`
- `user_role_context`

User prompt template:

```text
请分析以下业务沟通记录。

用户角色背景：
{user_role_context}

会话信息：
{session_metadata}

转写内容：
{transcript_segments}

请严格输出以下 JSON 结构：

{
  "summary": "用2-4句话概括本次沟通主题和结果",
  "scene": "客户沟通/渠道推动/内部管理/分公司汇报/产品讨论/其他",
  "key_points": ["关键点1", "关键点2"],
  "counterparty_needs": ["对方诉求1", "对方诉求2"],
  "counterparty_objections": ["对方异议1", "对方异议2"],
  "scores": {
    "goal_clarity": 0,
    "question_quality": 0,
    "business_actionability": 0,
    "responsibility_closure": 0,
    "objection_handling": 0,
    "rhythm_control": 0,
    "expression_efficiency": 0,
    "follow_up_closure": 0
  },
  "strengths": ["做得好的地方"],
  "weaknesses": ["需要改进的地方"],
  "missed_opportunities": ["本来可以追问或压实但没有做的点"],
  "todos": [
    {
      "owner": "责任人，无法判断则写未明确",
      "task": "待办事项",
      "due_date": "YYYY-MM-DD 或 未明确",
      "evidence": "来自转写的依据"
    }
  ],
  "better_phrases": [
    {
      "original": "原话或概括",
      "problem": "问题说明",
      "improved": "更好的表达"
    }
  ],
  "risk_flags": ["可能的沟通风险或业务风险"],
  "follow_up_questions": ["下次应该追问的问题"]
}

评分规则：每项 0-10 分，10 分最好。只给整数。
```

## Daily Review Prompt

Input variables:

- `date`
- `sessions_summary`
- `all_todos`
- `score_stats`

User prompt template:

```text
请基于以下一天内的沟通记录，生成每日沟通复盘。

日期：{date}

会话汇总：
{sessions_summary}

待办事项：
{all_todos}

评分统计：
{score_stats}

请严格输出以下 JSON 结构：

{
  "date": "YYYY-MM-DD",
  "daily_summary": "今日整体沟通概括",
  "valid_session_count": 0,
  "main_topics": ["主题1", "主题2"],
  "frequent_objections": ["高频异议1", "高频异议2"],
  "overall_strengths": ["今天表现好的地方"],
  "overall_weaknesses": ["今天最需要改进的地方"],
  "top_improvement": {
    "problem": "最重要的一个问题",
    "why_it_matters": "为什么重要",
    "suggestion": "明天具体怎么改"
  },
  "best_phrase_today": "今天比较好的表达，如无则写未发现",
  "phrase_to_replace": {
    "original": "需要替换的表达",
    "improved": "建议替换成的表达"
  },
  "priority_follow_ups": [
    {
      "task": "跟进事项",
      "owner": "责任人",
      "due_date": "YYYY-MM-DD 或 未明确"
    }
  ],
  "tomorrow_focus": ["明天沟通需要重点注意的事项"]
}
```

## Default User Role Context

```text
用户是一名财险产品与渠道销售管理者，日常工作包括车险、个人非车险、驾意险、旅游意外险等产品推动，渠道销售管理，分公司业务督导，总公司政策宣导和经营复盘。沟通风格需要清楚目标、压实责任、明确时间点和交付物，同时处理分公司或渠道关于费用政策、系统流程、产品支持、资源不足等异议。
```

## JSON Output Requirements

- Always request JSON only.
- Use DeepSeek JSON output mode if the SDK/model supports it.
- Validate with Pydantic before saving.
- If parsing fails, retry once with a repair prompt.
- Never save invalid JSON as final analysis.

## Repair Prompt

```text
你刚才的输出不是合法 JSON。请只输出合法 JSON，不要 Markdown，不要解释，不要代码块。保持原有字段结构，修复格式错误。
```
