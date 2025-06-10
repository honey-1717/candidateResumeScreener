/**
 * Resume Screener - API Client
 * Handles client-side API calls to Gemini
 */

const API_KEY = "AIzaSyCs-oX4DvQv7_B9FOuAXTVMnij_JKhkWCo"
const API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent"

/**
 * Generate criteria from job description
 * @param {string} jobDescription - The job description text
 * @returns {Promise<string[]>} - List of criteria
 */
async function generateCriteria(jobDescription) {
  const prompt = `
    Based on the following job description, identify 5-8 key evaluation criteria that would be important for 
    differentiating and ranking candidates. These should be specific, measurable aspects that can be evaluated 
    from a resume and will help clearly distinguish between candidates.
    
    For each criterion, provide a short, clear label that would work well as a column header in a comparison table.
    Focus on skills, qualifications, and experiences that are most relevant to this specific role.
    
    Job Description:
    ${jobDescription}
    
    Format your response as a simple list of criteria, one per line, without numbering or bullet points.
    For example:
    Technical Expertise
    Years of Experience
    Education Level
    Industry Knowledge
    Project Management
    `

  try {
    const response = await callGeminiAPI(prompt)

    // Process the response to get a clean list of criteria
    const criteriaText = response.trim()
    const criteriaList = criteriaText
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0 && line.length < 50 && !line.includes("."))

    // Limit to 8 criteria maximum
    return criteriaList.slice(0, 8)
  } catch (error) {
    console.error("Error generating criteria:", error)
    // Return default criteria if API call fails
    return ["Technical Skills", "Experience", "Education", "Communication Skills", "Problem Solving"]
  }
}

/**
 * Evaluate a resume against criteria
 * @param {string} jobDescription - The job description text
 * @param {string[]} criteria - List of criteria
 * @param {string} resumeText - The resume text
 * @returns {Promise<Object>} - Scores for each criterion
 */
async function evaluateResume(jobDescription, criteria, resumeText) {
  // Truncate resume text if too long
  const maxLength = 4000
  const truncatedResume = resumeText.length > maxLength ? resumeText.substring(0, maxLength) + "..." : resumeText

  const prompt = `
    You are an expert resume screener. Evaluate the following resume against the job description and criteria.
    
    Job Description:
    ${jobDescription}
    
    Resume:
    ${truncatedResume}
    
    Evaluate the candidate on each of the following criteria on a scale of 0-10 (where 10 is perfect match):
    ${criteria.join(", ")}
    
    For each criterion, provide:
    1. A score from 0-10
    2. A brief justification (1-2 sentences)
    
    Format your response as:
    Criterion: Score
    Justification: Brief explanation
    
    Repeat for each criterion.
    `

  try {
    const response = await callGeminiAPI(prompt)

    // Parse the response to extract scores
    const scores = {}
    const lines = response.trim().split("\n")

    for (const criterion of criteria) {
      let found = false

      for (const line of lines) {
        if (line.includes(criterion) && line.includes(":")) {
          try {
            const scoreText = line.split(":")[1].trim()
            // Extract the first number found in the score text
            const scoreMatch = scoreText.match(/\d+/)
            const score = scoreMatch ? Number.parseInt(scoreMatch[0]) : 0
            scores[criterion] = Math.min(10, Math.max(0, score)) // Ensure score is between 0-10
            found = true
            break
          } catch (error) {
            scores[criterion] = 0
          }
        }
      }

      // If criterion wasn't found in the response
      if (!found) {
        scores[criterion] = 0
      }
    }

    return scores
  } catch (error) {
    console.error("Error evaluating resume:", error)
    // Return default scores if API call fails
    return Object.fromEntries(criteria.map((criterion) => [criterion, 5]))
  }
}

/**
 * Call Gemini API
 * @param {string} prompt - The prompt to send to the API
 * @returns {Promise<string>} - The API response text
 */
async function callGeminiAPI(prompt) {
  const url = `${API_URL}?key=${API_KEY}`

  const payload = {
    contents: [
      {
        role: "user",
        parts: [{ text: prompt }],
      },
    ],
  }

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`API returned status code ${response.status}: ${await response.text()}`)
  }

  const result = await response.json()

  if (result.candidates && result.candidates.length > 0) {
    return result.candidates[0].content.parts[0].text
  }

  return ""
}

/**
 * Calculate overall score based on criteria scores and priorities
 * @param {Object} criteriaScores - Scores for each criterion
 * @param {Object} priorities - Priority values for each criterion
 * @returns {number} - Overall score (0-100)
 */
function calculateOverallScore(criteriaScores, priorities) {
  const totalPriority = Object.values(priorities).reduce((sum, priority) => sum + priority, 0)
  let weightedScore = 0

  for (const [criterion, score] of Object.entries(criteriaScores)) {
    const priority = priorities[criterion]
    weightedScore += (score * priority) / totalPriority
  }

  // Convert to percentage
  return (weightedScore / 10) * 100
}
