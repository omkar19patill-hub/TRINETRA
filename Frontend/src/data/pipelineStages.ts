import type { PipelineStage } from "../types/marketing";

export const pipelineStages: PipelineStage[] = [
  { index: 1, title: "Threat Intelligence", description: "Live CVE, EPSS and KEV data mapped to your actual assets." },
  { index: 2, title: "Risk Analysis", description: "Likelihood and business impact combined into one score." },
  { index: 3, title: "Financial Risk", description: "Converted into an estimated ₹ exposure range — not a single guess." },
  { index: 4, title: "Investment Optimization", description: "A fixed budget, allocated for maximum risk reduction." },
  { index: 5, title: "Security Action", description: "Fix, mitigate, accept, or transfer — with the reasoning attached." },
];
