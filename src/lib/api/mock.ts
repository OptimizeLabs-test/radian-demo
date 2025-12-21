/**
 * TARA Mock Data
 * 
 * This file contains mock responses for demo/testing purposes.
 * Used when API_CONFIG.useMock is true.
 * 
 * These responses mirror what your Python backend should return.
 * Use them as reference when implementing your LangChain RAG agents.
 */

import type { PatientSummary, SpecialtyPerspective } from './types';

// Simulate network latency for realistic demo experience
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Mock Patient Summary
 * 
 * Python backend equivalent:
 * - Query vector DB for patient's full record
 * - System prompt: "Summarise insights and latest updates. No diagnosis."
 */
export async function getMockSummary(patientId: string): Promise<PatientSummary> {
  await delay(800);
  
  return {
    headline: "Stable with Monitoring Required",
    content: [
      "Vital trends stable over past 3 months",
      "HbA1c trending upward (6.8% → 7.2%) – review diabetes management",
      "Blood pressure well-controlled (avg 128/82 mmHg)",
      "Medication adherence reported as good",
      "Exercise tolerance improved – 30 min daily walking routine",
      "No adverse events or ER visits in past quarter",
      "Next comprehensive review in 2 weeks"
    ]
  };
}

/**
 * Mock Specialty Perspectives
 * 
 * Python backend equivalent:
 * - Each specialty has its own LLM agent with specialized system prompt
 * - Cardiology agent: Focus on cardiac-related insights
 * - Endocrinology agent: Focus on diabetes management
 */
export async function getMockSpecialties(patientId: string): Promise<SpecialtyPerspective[]> {
  await delay(1000);
  
  return [
    {
      specialty: "Cardiology",
      insights: [
        "Blood pressure control has been stable on current ACE inhibitor",
        "ECG from last visit shows normal sinus rhythm, no ST changes",
        "Patient reports no chest pain or palpitations in past 3 months",
        "Consider lipid profile review given diabetes management changes",
        "Continue monitoring for signs of diabetic cardiomyopathy"
      ]
    },
    {
      specialty: "Diabetes / Endocrinology",
      insights: [
        "HbA1c trending upward from 6.8% to 7.2% - requires attention",
        "Fasting glucose readings show increased variability (110-145 mg/dL)",
        "Patient adherent to metformin but may benefit from dosage review",
        "No signs of peripheral neuropathy on recent examination",
        "Recommend dietary consultation and continuous glucose monitoring consideration"
      ]
    }
  ];
}

/**
 * Mock Intro Message
 * 
 * Python backend equivalent:
 * - RAG agent analyzes patient record
 * - Suggests relevant queries for the doctor to explore
 */
export async function getMockIntroMessage(patientId: string): Promise<string> {
  await delay(600);
  
  return `Hello, Doctor. What would you like to know today?`;
}

/**
 * Mock Chat Response
 * 
 * Python backend equivalent:
 * - RAG agent queries vector DB for relevant context
 * - LLM generates response based on patient-specific data
 * - No diagnostic statements - provide information and guidance only
 */
export async function getMockChatResponse(patientId: string, question: string): Promise<string> {
  await delay(1200);
  
  const lowerQuestion = question.toLowerCase();
  
  if (lowerQuestion.includes("hba1c") || lowerQuestion.includes("glycemic")) {
    return `HbA1c has risen from 6.8% to 7.2% over 3 months, coinciding with increased work stress and reduced meal planning. Fasting glucose is more variable (110-145 mg/dL). Metformin adherence remains good.

🔹 Discuss stress management strategies
🔹 Consider diabetes educator referral
🔹 Evaluate medication or meal timing adjustments`;
  }
  
  if (lowerQuestion.includes("cardiac") || lowerQuestion.includes("blood pressure")) {
    return `BP stable at avg 128/82 mmHg over 3 months. Lisinopril 10mg taken consistently. Recent ECG shows normal sinus rhythm. Exercise tolerance improved with daily 30-min walks.

🔹 Continue current BP monitoring
🔹 Review lipid profile given diabetes changes
🔹 Watch for early diabetic cardiomyopathy signs`;
  }
  
  if (lowerQuestion.includes("medication") || lowerQuestion.includes("adherence")) {
    return `Excellent adherence across all medications: Metformin 1000mg BID, Lisinopril 10mg daily, Atorvastatin 20mg daily. Patient uses pill organizer with phone reminders. No reported side effects.

🔹 Continue current regimen
🔹 Reinforce effective adherence system
🔹 No medication changes indicated`;
  }
  
  // Default response
  return `I have access to Sanjeev's visits, labs, medications, and clinical notes from the past 2 years.

🔹 Ask about specific time periods or trends
🔹 Query symptoms or conditions
🔹 Review medication history
🔹 Explore lab result patterns`;
}
