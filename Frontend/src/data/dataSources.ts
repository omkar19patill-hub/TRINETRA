import type { DataSource } from "../types/marketing";

export const dataSources: DataSource[] = [
  { name: "NVD", description: "Vulnerability data, CVSS severity, affected products." },
  { name: "CISA KEV", description: "Confirmed, real-world exploitation signal." },
  { name: "EPSS", description: "Probability of exploitation in the next 30 days." },
  { name: "MITRE ATT&CK", description: "Adversary tactics and techniques, for context." },
];
