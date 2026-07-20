// Mirrors the backend Pydantic models (research_agent.models).

export interface Step {
  n: number;
  tool: string;
  input: string;
  output: string;
}

export interface Development {
  fact: string;
  source_url: string;
}

export interface Briefing {
  company: string;
  summary: string;
  what_they_do: string[];
  recent_developments: Development[];
  culture_signals: string[];
  likely_interview_questions: string[];
  talking_points: string[];
  sources: string[];
  notes: string;
}

export interface ResearchResult {
  task: string;
  briefing: Briefing;
  trace: Step[];
  steps_used: number;
}
